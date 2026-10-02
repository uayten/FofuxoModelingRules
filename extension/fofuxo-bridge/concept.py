"""The concept image: find a part's box by color and tie that box to the frame.

set_frame(..., concept={"image": ..., "box": [x0, x1, y0, y1]}) makes the
frame's width and height the box's, so 1000 on the grid is the part's edge in
the concept, and the render draws the box's crop behind the model's outline.
Boxes are in image pixels, top-left origin, inclusive.
"""

import bpy
import numpy as np


def pixels(image_name):
    """RGBA float pixels, row 0 at the top."""
    img = bpy.data.images.get(image_name)
    if img is None:
        raise ValueError(f"no image named {image_name!r}")
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(h, w, 4)[::-1]


def sample(image_name, x, y):
    """RGB (0..1) at a pixel, to pick the color of a part."""
    return [round(float(c), 3) for c in pixels(image_name)[y, x, :3]]


def find_box(image_name, rgb, tol=0.2, roi=None):
    """Box of the pixels within tol (per channel) of rgb, inside roi [x0, x1, y0, y1].

    Returns {"box": [x0, x1, y0, y1], "pixels": count} or None.
    """
    px = pixels(image_name)
    mask = np.abs(px[..., :3] - np.asarray(rgb, dtype=np.float32)).max(axis=2) <= tol
    if roi is not None:
        keep = np.zeros_like(mask)
        x0, x1, y0, y1 = roi
        keep[y0:y1 + 1, x0:x1 + 1] = True
        mask &= keep
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return {"box": [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())], "pixels": int(mask.sum())}


def mm_per_px(image_name):
    """Scale of the image as an Image Empty shows it in the scene, or None."""
    for e in bpy.data.objects:
        if e.type == "EMPTY" and e.empty_display_type == "IMAGE" and e.data and e.data.name == image_name:
            w, h = e.data.size
            return e.empty_display_size * e.matrix_world.to_scale().x * 1000 / max(w, h)
    return None


def box_size_mm(concept):
    """(width, height) of the concept box in mm."""
    x0, x1, y0, y1 = concept["box"]
    scale = concept.get("mm_per_px") or mm_per_px(concept["image"])
    if not scale:
        raise ValueError("the concept needs mm_per_px, or an Image Empty showing it in the scene")
    return (x1 - x0 + 1) * scale, (y1 - y0 + 1) * scale


def crop_lookup(concept, frame, right_vals, up_vals):
    """Concept RGBA for local X (right_vals) and Z (up_vals) in the front view.

    The box spans the frame: -1000..1000 on a mirrored axis, 0..1000 on a range.
    Returns (rgba, inside_mask).
    """
    px = pixels(concept["image"])
    x0, x1, y0, y1 = concept["box"]

    def frac(fa, vals):
        if fa.side:
            return (vals / fa.extent + 1) / 2
        return (vals - fa.start) / fa.extent

    fx = frac(frame.axes[0], right_vals)
    fz = frac(frame.axes[2], up_vals)
    inside = (fx >= 0) & (fx < 1) & (fz >= 0) & (fz < 1)
    ix = np.clip((x0 + fx * (x1 - x0 + 1)).astype(int), 0, px.shape[1] - 1)
    iy = np.clip((y1 + 1 - fz * (y1 - y0 + 1)).astype(int), 0, px.shape[0] - 1)
    return px[iy, ix], inside
