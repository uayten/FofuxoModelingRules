"""What the view sheet labels, kept as mesh attributes (Object Data >
Attributes), so the modeler can change them by hand and the AI by call.
Nothing is labeled by itself: the sheet shows what these ask for.

    llm_bridge_show_vertex  POINT INT  the vertex's id
    llm_bridge_loop         EDGE  INT  each connected run of shown edges (closed
                                   across the mirror planes) is drawn as one
                                   colored loop with one label
    llm_bridge_show_face    FACE  INT  the face's id (f12) at its center

Each works in levels: only the elements with the highest value present are
shown, and 0 is never shown. Marking a few with a new, higher level narrows
the view to them; marking everything with 1 brings the whole back.

    llm_modeling_bridge.show("Chapéu", "all", level=1)       # every id
    llm_modeling_bridge.show("Chapéu", "h>555")              # a new level: only these
    llm_modeling_bridge.show("Chapéu", "v12", level="add")   # add v12 to what is shown
    llm_modeling_bridge.mark_loop("Chapéu", "loop v117-v118")    # only this loop
    llm_modeling_bridge.mark_loop("Chapéu", "loop v124-v125", level="add")
    llm_modeling_bridge.show_faces("Chapéu", "faces h>800")
"""

import bpy

SHOW_VERTEX = "llm_bridge_show_vertex"
LOOP = "llm_bridge_loop"
SHOW_FACE = "llm_bridge_show_face"


class LabelError(Exception):
    pass


def _values(mesh, name, domain):
    attr = mesh.attributes.get(name)
    n = {"POINT": len(mesh.vertices), "EDGE": len(mesh.edges), "FACE": len(mesh.polygons)}[domain]
    if attr is None or attr.domain != domain:
        return [0] * n
    return [int(d.value) for d in attr.data]


def shown(values):
    """True for the elements at the highest level present (never level 0)."""
    top = max(values, default=0)
    return [top > 0 and v == top for v in values]


def vertex_show(mesh):
    return shown(_values(mesh, SHOW_VERTEX, "POINT"))


def loop_edges(mesh):
    return shown(_values(mesh, LOOP, "EDGE"))


def face_show(mesh):
    return shown(_values(mesh, SHOW_FACE, "FACE"))


def _attr(mesh, name, domain):
    attr = mesh.attributes.get(name)
    if attr is not None and (attr.domain != domain or attr.data_type != "INT"):
        old = [int(d.value) for d in attr.data] if attr.domain == domain else None
        mesh.attributes.remove(attr)
        attr = mesh.attributes.new(name, "INT", domain)
        if old is not None:  # a boolean made by hand keeps its marks as level 1
            attr.data.foreach_set("value", old)
    return attr or mesh.attributes.new(name, "INT", domain)


def _resolve(name, text):
    from .mesh_ops import select
    from .mesh_io import ID_ATTR

    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise LabelError(f"no mesh object named {name!r}")
    if obj.mode != "OBJECT":
        raise LabelError(f"{name!r} must be in Object Mode")
    picked = select(name, text)
    index = {d.value: i for i, d in enumerate(obj.data.attributes[ID_ATTR].data)}
    verts = {index[int(v[1:])] for v in picked["verts"]}
    return obj, verts


def _mark(obj, name, domain, picked, level):
    """Set picked elements to level: None opens a new level above the
    highest, "add" joins the shown one, 0 clears, a number sets it."""
    attr = _attr(obj.data, name, domain)
    top = max((int(d.value) for d in attr.data), default=0)
    if level is None:
        level = top + 1
    elif level == "add":
        level = max(top, 1)
    elif not isinstance(level, int) or level < 0:
        raise LabelError('level must be None, "add" or a number from 0')
    for i in picked:
        attr.data[i].value = level
    obj.data.update()
    return {"marked": len(picked), "level": level, "shown": sum(shown([int(d.value) for d in attr.data]))}


def show(name, text, level=None):
    """Label the selection's vertices with their ids (see _mark for level)."""
    obj, verts = _resolve(name, text)
    return _mark(obj, SHOW_VERTEX, "POINT", verts, level)


def mark_loop(name, text, level=None):
    """Draw the edges between selected vertices as loops (see _mark for
    level: by default a new level, so only these show)."""
    obj, verts = _resolve(name, text)
    edges = [e.index for e in obj.data.edges if e.vertices[0] in verts and e.vertices[1] in verts]
    return _mark(obj, LOOP, "EDGE", edges, level)


def show_faces(name, text, level=None):
    """Label the faces whose vertices are all selected (see _mark for
    level: by default a new level, so only these show)."""
    obj, verts = _resolve(name, text)
    faces = [p.index for p in obj.data.polygons if all(v in verts for v in p.vertices)]
    return _mark(obj, SHOW_FACE, "FACE", faces, level)
