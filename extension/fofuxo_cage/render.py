"""View sheets drawn on the CPU: numpy rasterizer and a bitmap font.

No GPU, no screen context, no scene changes, so it runs the same from the MCP
and in background mode.

- render_sheet: front / top / side x cage / subdivision / concept, on the
  frame grid (thin lines, the mirror plane in blue, the frame edge in orange).
- render_views: any cameras (yaw, pitch in degrees) x cage / subdivision, for
  3/4 views, views from above or below, the back.

Cage panels label the base vertices with their ids, placed away from the
model with a leader line to each vertex. Parent, children and siblings are
drawn gray in the subdivision panels and join the outline.
"""

import itertools
import math

import bpy
import numpy as np
from mathutils import Vector

from . import concept as concept_mod
from . import font, topology

PANEL = 480
GAP = 6
HEADER = 26
PAD = 34  # room inside a panel for the title and the grid labels
FILL = 0.72  # share of the panel the model takes, leaving room for labels

WHITE = np.array([1.0, 1.0, 1.0])
GRID = np.array([0.89, 0.89, 0.91])
PLANE = np.array([0.35, 0.55, 0.95])
EDGE = np.array([0.95, 0.55, 0.15])
CAGE_FACE = np.array([0.80, 0.83, 0.90])
SUB_FACE = np.array([0.86, 0.74, 0.64])
CONTEXT_FACE = np.array([0.70, 0.70, 0.72])
WIRE = np.array([0.12, 0.12, 0.18])
WIRE_COPY = np.array([0.62, 0.64, 0.70])
VERT = np.array([0.85, 0.10, 0.10])
POLE = np.array([0.95, 0.55, 0.0])
OUTLINE = np.array([0.0, 0.35, 1.0])
LEADER = np.array([0.40, 0.40, 0.50])
TEXT = np.array([0.1, 0.1, 0.1])
LABEL_H = 16
AXIS_NAME = "wdh"

# yaw 0 looks from the front (-Y), yaw 90 from the right (+X); pitch > 0 from above.
PRESETS = {
    "front": (0, 0), "back": (180, 0), "right": (90, 0), "side": (90, 0), "left": (-90, 0),
    "top": (0, 90), "bottom": (0, -90),
}
SHEET_VIEWS = ("front", "top", "side")
DEFAULT_VIEWS = ((45, 30), (45, -30), (135, 30))


class Camera:
    """Orthographic camera around the object, in its local space."""

    def __init__(self, spec):
        if isinstance(spec, str):
            if spec in PRESETS:
                self.name = spec
                yaw, pitch = PRESETS[spec]
            else:
                yaw, pitch = (float(v) for v in spec.split(","))
                self.name = f"yaw {yaw:g} pitch {pitch:g}"
        else:
            yaw, pitch = spec
            self.name = f"yaw {yaw:g} pitch {pitch:g}"
        y, p = math.radians(yaw), math.radians(pitch)
        self.toward = np.array([math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)])
        self.right = np.array([math.cos(y), math.sin(y), 0.0])
        self.up = np.cross(self.toward, self.right)
        for v in (self.toward, self.right, self.up):
            v[np.abs(v) < 1e-9] = 0.0

    def axis(self, vec):
        """Index of the local axis vec lies on, or None when it is oblique."""
        k = int(np.argmax(np.abs(vec)))
        return k if abs(abs(vec[k]) - 1) < 1e-9 else None

    @property
    def aligned(self):
        return self.axis(self.right) is not None and self.axis(self.up) is not None


class Panel:
    """One view: a pixel buffer, a depth buffer and the projection."""

    def __init__(self, cam, scale, center):
        self.cam, self.scale, self.center = cam, scale, center
        self.img = np.tile(WHITE, (PANEL, PANEL, 1))
        self.zbuf = np.full((PANEL, PANEL), -np.inf)

    def to_px(self, co):
        """(N, 3) local coords -> (N, 2) pixel coords (x right, y down) and depth."""
        rel = np.asarray(co, dtype=float).reshape(-1, 3) - self.center
        x = PANEL / 2 + rel @ self.cam.right * self.scale
        y = PANEL / 2 - rel @ self.cam.up * self.scale + PAD / 4
        return np.stack([x, y], axis=1), rel @ self.cam.toward

    def plane_of_px(self, px, py):
        """Local coords of pixel centers on the plane through the center."""
        a = (px - PANEL / 2) / self.scale
        b = -(py - PANEL / 2 - PAD / 4) / self.scale
        return self.center + a[..., None] * self.cam.right + b[..., None] * self.cam.up

    def fill(self, tris3d, color):
        """Flat-shaded triangles with a depth test. tris3d: (T, 3, 3) local."""
        mask = np.zeros((PANEL, PANEL), dtype=bool)
        if not len(tris3d):
            return mask
        light = self.cam.toward * 0.85 + self.cam.up * 0.4 - self.cam.right * 0.3
        light /= np.linalg.norm(light)
        n = np.cross(tris3d[:, 1] - tris3d[:, 0], tris3d[:, 2] - tris3d[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        shade = 0.30 + 0.70 * np.abs(n @ light)
        px, depth = self.to_px(tris3d.reshape(-1, 3))
        px = px.reshape(-1, 3, 2)
        depth = depth.reshape(-1, 3)
        for t in range(len(px)):
            (x0, y0), (x1, y1), (x2, y2) = px[t]
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if abs(area) < 1e-9:
                continue
            minx, maxx = max(int(min(x0, x1, x2)), 0), min(int(max(x0, x1, x2)) + 1, PANEL - 1)
            miny, maxy = max(int(min(y0, y1, y2)), 0), min(int(max(y0, y1, y2)) + 1, PANEL - 1)
            if minx > maxx or miny > maxy:
                continue
            X, Y = np.meshgrid(np.arange(minx, maxx + 1) + 0.5, np.arange(miny, maxy + 1) + 0.5)
            w0 = ((x1 - X) * (y2 - Y) - (x2 - X) * (y1 - Y)) / area
            w1 = ((x2 - X) * (y0 - Y) - (x0 - X) * (y2 - Y)) / area
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            z = w0 * depth[t, 0] + w1 * depth[t, 1] + w2 * depth[t, 2]
            zsub = self.zbuf[miny:maxy + 1, minx:maxx + 1]
            upd = inside & (z > zsub)
            zsub[upd] = z[upd]
            self.img[miny:maxy + 1, minx:maxx + 1][upd] = color * shade[t]
            mask[miny:maxy + 1, minx:maxx + 1] |= inside
        return mask

    def line(self, p0, p1, color, alpha=1.0):
        n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 2
        xs = np.linspace(p0[0], p1[0], n).astype(int)
        ys = np.linspace(p0[1], p1[1], n).astype(int)
        ok = (xs >= 0) & (xs < PANEL) & (ys >= 0) & (ys < PANEL)
        xs, ys = xs[ok], ys[ok]
        self.img[ys, xs] = self.img[ys, xs] * (1 - alpha) + color * alpha

    def dot(self, p, color, r=2):
        x, y = int(p[0]), int(p[1])
        self.img[max(y - r, 0):min(y + r + 1, PANEL), max(x - r, 0):min(x + r + 1, PANEL)] = color

    def text(self, x, y, s, color=TEXT, scale=2, bg=True):
        mask = font.text_mask(s, scale)
        h, w = mask.shape
        x, y = int(x), int(y)
        if bg:
            y0, y1 = max(y - 1, 0), min(y + h + 1, PANEL)
            x0, x1 = max(x - 1, 0), min(x + w + 1, PANEL)
            self.img[y0:y1, x0:x1] = self.img[y0:y1, x0:x1] * 0.25 + WHITE * 0.75
        ys, xs = np.nonzero(mask)
        ys, xs = ys + y, xs + x
        ok = (xs >= 0) & (xs < PANEL) & (ys >= 0) & (ys < PANEL)
        self.img[ys[ok], xs[ok]] = color


# --- scene data -------------------------------------------------------------

def _mirror_copies(co, faces, edges, mirror_axes):
    """Base mesh repeated across the mirror planes, faces rewound where needed."""
    out_co, out_faces, out_edges, copy_of = [], [], [], []
    n = len(co)
    choices = [(1.0, -1.0) if a in mirror_axes else (1.0,) for a in topology.AXES]
    for k, signs in enumerate(itertools.product(*choices)):
        s = np.array(signs)
        out_co.append(co * s)
        flip = np.prod(s) < 0
        out_faces += [[i + k * n for i in (f[::-1] if flip else f)] for f in faces]
        out_edges += [(a + k * n, b + k * n) for a, b in edges]
        copy_of += [k] * len(edges)
    return np.concatenate(out_co), out_faces, out_edges, copy_of


def _triangles(co, faces):
    tris = [(f[0], f[i], f[i + 1]) for f in faces for i in range(1, len(f) - 1)]
    return co[np.array(tris, dtype=int)] if tris else np.zeros((0, 3, 3))


def _evaluated(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        co = np.empty(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get("co", co)
        faces = [list(p.vertices) for p in me.polygons]
    finally:
        ev.to_mesh_clear()
    return co.reshape(-1, 3).astype(float), faces


def _mirror_axes(obj):
    axes = set()
    for m in obj.modifiers:
        if m.type == "MIRROR" and m.show_viewport and m.mirror_object is None:
            axes |= {a for a, on in zip(topology.AXES, m.use_axis) if on}
    return [a for a in topology.AXES if a in axes]


def _pole_indices(obj, mirror):
    import bmesh

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return {v.index for v in bm.verts if v.link_faces and topology.mirrored_valence(v, mirror) != 4}
    finally:
        bm.free()


def _related(obj):
    """Parent, children and siblings: the parts drawn around obj as context."""
    out = []
    if obj.parent is not None:
        out.append(obj.parent)
        out += [c for c in obj.parent.children if c is not obj]
    out += list(obj.children)
    seen = set()
    return [o for o in out if o.type == "MESH" and o.visible_get() and not (o.name in seen or seen.add(o.name))]


def _context_triangles(obj, depsgraph):
    """Evaluated triangles of the related parts, in obj's local space."""
    inv = np.array(obj.matrix_world.inverted())
    tris = []
    for other in _related(obj):
        co, faces = _evaluated(other, depsgraph)
        m = inv @ np.array(other.matrix_world)
        tris.append(_triangles(co @ m[:3, :3].T + m[:3, 3], faces))
    return np.concatenate(tris) if tris else np.zeros((0, 3, 3))


class Scene:
    """Everything a sheet draws for one object."""

    def __init__(self, obj, ids, depsgraph):
        mesh = obj.data
        mirror = _mirror_axes(obj)
        base = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", base)
        self.base = base.reshape(-1, 3).astype(float)
        faces = [list(p.vertices) for p in mesh.polygons]
        edges = [tuple(e.vertices) for e in mesh.edges]
        self.cage_co, cage_faces, self.cage_edges, self.copy_of = _mirror_copies(self.base, faces, edges, mirror)
        self.cage_tris = _triangles(self.cage_co, cage_faces)
        ev_co, ev_faces = _evaluated(obj, depsgraph)
        self.ev_tris = _triangles(ev_co, ev_faces)
        self.context_tris = _context_triangles(obj, depsgraph)
        self.labels = [f"v{vid}" for vid in ids]
        self.poles = _pole_indices(obj, mirror)
        pts = [self.cage_co, ev_co] + ([self.context_tris.reshape(-1, 3)] if len(self.context_tris) else [])
        self.lo = np.min([p.min(axis=0) for p in pts], axis=0)
        self.hi = np.max([p.max(axis=0) for p in pts], axis=0)

    def fit(self, cams, frame=None):
        """Scale and center shared by the given cameras."""
        lo, hi = self.lo.copy(), self.hi.copy()
        if frame is not None:
            for k, fa in enumerate(frame.axes):
                lo[k] = min(lo[k], -fa.extent if fa.side else fa.start)
                hi[k] = max(hi[k], fa.extent if fa.side else fa.start + fa.extent)
        center = (lo + hi) / 2
        corners = np.array(list(itertools.product(*zip(lo, hi)))) - center
        span = max(max(np.ptp(corners @ c.right), np.ptp(corners @ c.up)) for c in cams)
        return (PANEL - 2 * PAD) * FILL / max(span, 1e-6), center

    def cage_panel(self, cam, scale, center, frame=None):
        panel = Panel(cam, scale, center)
        if frame is not None and cam.aligned:
            _grid(panel, frame)
        mask = panel.fill(self.cage_tris, CAGE_FACE)
        px, _ = panel.to_px(self.cage_co)
        for (a, b), k in zip(self.cage_edges, self.copy_of):
            if k:
                panel.line(px[a], px[b], WIRE_COPY, alpha=0.8)
        for (a, b), k in zip(self.cage_edges, self.copy_of):
            if not k:
                panel.line(px[a], px[b], WIRE)
        n = len(self.base)
        for i in range(n):
            panel.dot(px[i], POLE if i in self.poles else VERT, r=3 if i in self.poles else 2)
        _place_labels(panel, px[:n], self.labels, mask)
        panel.text(4, 4, f"{cam.name}  cage")
        return panel

    def sub_panel(self, cam, scale, center, frame=None):
        panel = Panel(cam, scale, center)
        if frame is not None and cam.aligned:
            _grid(panel, frame)
        mask = panel.fill(self.ev_tris, SUB_FACE) | panel.fill(self.context_tris, CONTEXT_FACE)
        px, _ = panel.to_px(self.cage_co)
        for (a, b), k in zip(self.cage_edges, self.copy_of):
            if not k:
                panel.line(px[a], px[b], WIRE, alpha=0.35)
        panel.text(4, 4, f"{cam.name}  subdivision")
        return panel, mask


# --- drawing helpers ----------------------------------------------------------

def _dilate(mask, r):
    out = mask.copy()
    for _ in range(r):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def _place_labels(panel, pts, labels, model_mask):
    """Labels go around the model, never over it, over another label or over a
    vertex; a leader line joins each label to its vertex.

    Each label searches rings of growing radius around its vertex for a spot
    off the model; crowded vertices choose first. Only when no such spot exists
    does a label sit over the model.
    """
    pts = np.asarray(pts, dtype=float)
    if not len(pts):
        return
    avoid = _dilate(model_mask, 5)
    dist = np.linalg.norm(pts[:, None] - pts[None], axis=2)
    order = np.argsort(-(dist < 40).sum(axis=1), kind="stable")
    dots = [(p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3) for p in pts]
    placed = {}

    def free(rect, own, allow_model):
        x0, y0, x1, y1 = rect
        if x0 < 0 or y0 < PAD / 2 or x1 > PANEL or y1 > PANEL - 12:
            return False
        if not allow_model and avoid[int(y0):int(y1), int(x0):int(x1)].any():
            return False
        hits = list(placed.values()) + [d for j, d in enumerate(dots) if j != own]
        return all(x1 <= r[0] or x0 >= r[2] or y1 <= r[1] or y0 >= r[3] for r in hits)

    for i in order:
        w = len(labels[i]) * 12 + 2
        vx, vy = pts[i]
        chosen = None
        for allow_model in (False, True):
            for radius in range(14, 260, 12):
                for k in range(24):
                    ang = k * np.pi / 12
                    cx, cy = vx + radius * np.cos(ang), vy - radius * np.sin(ang)
                    x = cx if np.cos(ang) >= 0 else cx - w
                    rect = (x, cy - LABEL_H / 2, x + w, cy + LABEL_H / 2)
                    if free(rect, i, allow_model):
                        chosen = rect
                        break
                if chosen:
                    break
            if chosen:
                break
        placed[i] = chosen or (vx + 4, vy - LABEL_H - 2, vx + 4 + w, vy - 2)

    for i, rect in placed.items():
        vx, vy = pts[i]
        nx = min(max(vx, rect[0]), rect[2])
        ny = min(max(vy, rect[1]), rect[3])
        if np.hypot(nx - vx, ny - vy) > 5:
            panel.line((vx, vy), (nx, ny), LEADER, alpha=0.85)
    for i, rect in placed.items():
        panel.text(rect[0] + 1, rect[1] + 1, labels[i], color=WIRE, scale=2)


def _grid(panel, frame):
    """Frame grid on both screen axes of an aligned view. The step keeps lines
    >= 10 px apart and labels >= 44 px apart."""
    right, up = panel.cam.axis(panel.cam.right), panel.cam.axis(panel.cam.up)
    for axis, other, horizontal in ((right, up, False), (up, right, True)):
        fa = frame.axes[axis]
        px_per = fa.extent / 1000 * panel.scale
        step = next((s for s in (50, 100, 200, 250, 500, 1000) if s * px_per >= 10), 2000)
        label_step = next((s for s in (100, 250, 500, 1000, 2000, 5000) if s * px_per >= 44 and s % step == 0), 10000)
        for v in range(-10000, 10001, step):
            if fa.side and v < 0:
                continue
            color = PLANE if (fa.side and v == 0) else EDGE if v == 1000 else GRID
            for pos in [fa.to_local(v)] + ([-fa.to_local(v)] if fa.side and v else []):
                co = np.tile(panel.center, (2, 1))
                co[:, axis] = pos
                co[0, other] -= PANEL / panel.scale
                co[1, other] += PANEL / panel.scale
                p, _ = panel.to_px(co)
                coord = p[0][1] if horizontal else p[0][0]
                if not 0 <= coord < PANEL:
                    continue
                panel.line(p[0], p[1], color, alpha=0.9 if color is GRID else 1.0)
                if v % label_step == 0:
                    if horizontal and coord < PANEL - 8:
                        panel.text(2, coord - 7, str(v), color=color * 0.8, scale=1)
                    elif not horizontal and coord < PANEL - 20:
                        panel.text(coord - 6, PANEL - 10, str(v), color=color * 0.8, scale=1)


def _outline(mask):
    inner = mask.copy()
    inner[1:, :] &= mask[:-1, :]
    inner[:-1, :] &= mask[1:, :]
    inner[:, 1:] &= mask[:, :-1]
    inner[:, :-1] &= mask[:, 1:]
    edge = mask & ~inner
    thick = edge.copy()
    thick[1:, :] |= edge[:-1, :]
    thick[:, 1:] |= edge[:, :-1]
    return thick


# --- concept ------------------------------------------------------------------

def _concept_images():
    """Image Empties in the scene with their pixels."""
    out = []
    for e in bpy.data.objects:
        if e.type != "EMPTY" or e.empty_display_type != "IMAGE" or e.data is None:
            continue
        w, h = e.data.size
        if not w or not h:
            continue
        px = np.empty(w * h * 4, dtype=np.float32)
        e.data.pixels.foreach_get(px)
        out.append((e, px.reshape(h, w, 4)))
    return out


def _draw_concept(panel, obj, images):
    """Sample every Image Empty facing this view into the panel. False if none."""
    mo = np.array(obj.matrix_world)
    dir_w = mo[:3, :3] @ panel.cam.toward
    dir_w /= np.linalg.norm(dir_w)
    ys, xs = np.mgrid[0:PANEL, 0:PANEL] + 0.5
    local = panel.plane_of_px(xs, ys).reshape(-1, 3)
    world = local @ mo[:3, :3].T + mo[:3, 3]
    drawn = False
    for e, pixels in images:
        me_ = e.matrix_world
        normal = np.array((me_.to_3x3() @ Vector((0, 0, 1))).normalized())
        dn = dir_w @ normal
        if abs(dn) < 0.95:
            continue
        t = ((np.array(me_.translation) - world) @ normal) / dn
        hit = world + t[:, None] * dir_w
        inv = np.array(me_.inverted())
        el = hit @ inv[:3, :3].T + inv[:3, 3]
        h, w = pixels.shape[:2]
        size = e.empty_display_size
        iw, ih = size * w / max(w, h), size * h / max(w, h)
        ox, oy = e.empty_image_offset
        fx = (el[:, 0] - ox * iw) / iw
        fy = (el[:, 1] - oy * ih) / ih
        ok = (fx >= 0) & (fx < 1) & (fy >= 0) & (fy < 1)
        if not ok.any():
            continue
        rgba = pixels[np.clip((fy * h).astype(int), 0, h - 1), np.clip((fx * w).astype(int), 0, w - 1)]
        flat = panel.img.reshape(-1, 3)
        a = rgba[:, 3:4] * ok[:, None]
        flat[:] = flat * (1 - a) + rgba[:, :3] * a
        drawn = True
    return drawn


def _draw_concept_crop(panel, frame, concept):
    """Front view: the concept box stretched over the frame. False if unusable."""
    ys, xs = np.mgrid[0:PANEL, 0:PANEL] + 0.5
    local = panel.plane_of_px(xs, ys)
    try:
        rgba, inside = concept_mod.crop_lookup(concept, frame, local[..., 0], local[..., 2])
    except ValueError:
        return False
    a = rgba[..., 3:4] * inside[..., None]
    panel.img[:] = panel.img * (1 - a) + rgba[..., :3] * a
    return True


# --- sheets -------------------------------------------------------------------

def _compose(rows, title, path):
    cols = max(len(r) for r in rows)
    width = cols * PANEL + (cols - 1) * GAP
    height = HEADER + len(rows) * PANEL + (len(rows) - 1) * GAP
    sheet = np.tile(np.array([0.8, 0.8, 0.82]), (height, width, 1))
    for i, row in enumerate(rows):
        for j, img in enumerate(row):
            y = HEADER + i * (PANEL + GAP)
            x = j * (PANEL + GAP)
            sheet[y:y + PANEL, x:x + PANEL] = img
    mask = font.text_mask(title[: width // 12], 2)
    ys, xs = np.nonzero(mask)
    sheet[ys + 6, xs + 6] = TEXT
    _write_png(sheet, path)
    return path


def render_sheet(obj, ids, depsgraph, frame, path, title="", concept=None):
    """Front / top / side x cage / subdivision / concept. Returns the path.

    concept: {"image", "box"} from set_frame; the front concept panel then
    shows that box over the frame. Otherwise Image Empties facing each view
    are drawn where they are in the scene.
    """
    scene = Scene(obj, ids, depsgraph)
    cams = [Camera(v) for v in SHEET_VIEWS]
    scale, center = scene.fit(cams, frame)
    images = _concept_images()
    rows = []
    for cam in cams:
        cage = scene.cage_panel(cam, scale, center, frame)
        sub, mask = scene.sub_panel(cam, scale, center, frame)
        cpanel = Panel(cam, scale, center)
        if cam.name == "front" and concept and _draw_concept_crop(cpanel, frame, concept):
            drawn = True
        else:
            drawn = _draw_concept(cpanel, obj, images)
        if drawn:
            _grid(cpanel, frame)
            cpanel.img[_outline(mask)] = OUTLINE
            cpanel.text(4, 4, f"{cam.name}  concept + outline")
        else:
            cpanel.img[:] = 0.95
            cpanel.text(4, 4, f"{cam.name}: no concept")
        rows.append([cage.img, sub.img, cpanel.img])
    return _compose(rows, title, path)


def render_views(obj, ids, depsgraph, views, path, title=""):
    """Any cameras x cage / subdivision. views: preset names ("front", "top",
    "left"...), "yaw,pitch" strings or (yaw, pitch) pairs in degrees."""
    scene = Scene(obj, ids, depsgraph)
    cams = [Camera(v) for v in views]
    scale, center = scene.fit(cams)
    rows = [[scene.cage_panel(c, scale, center).img, scene.sub_panel(c, scale, center)[0].img] for c in cams]
    return _compose(rows, title, path)


def _write_png(rgb, path):
    h, w = rgb.shape[:2]
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((h, w, 1))], axis=2)[::-1]
    img = bpy.data.images.new("fofuxo_cage_sheet", w, h, alpha=False)
    try:
        img.pixels.foreach_set(rgba.astype(np.float32).ravel())
        img.filepath_raw = str(path)
        img.file_format = "PNG"
        img.save()
    finally:
        bpy.data.images.remove(img)
