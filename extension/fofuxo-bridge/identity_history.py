"""Restore recorded vertex identities when native undo reloads older id data."""

MAX_STATES = 256


def vertex_signatures(positions, edges, faces):
    neighbors = [[] for _ in positions]
    incident_faces = [[] for _ in positions]
    for first, second in edges:
        neighbors[first].append(positions[second])
        neighbors[second].append(positions[first])
    for face in faces:
        coordinates = tuple(sorted(positions[index] for index in face))
        for index in face:
            incident_faces[index].append(coordinates)
    return [
        (point, tuple(sorted(neighbors[index])), tuple(sorted(incident_faces[index])))
        for index, point in enumerate(positions)
    ]


def geometry(obj):
    if obj.mode == "EDIT":
        import bmesh
        cage = bmesh.from_edit_mesh(obj.data)
        vertices = list(cage.verts)
        indices = {vertex: index for index, vertex in enumerate(vertices)}
        positions = [tuple(vertex.co) for vertex in vertices]
        edges = [tuple(indices[vertex] for vertex in edge.verts) for edge in cage.edges]
        faces = [tuple(indices[vertex] for vertex in face.verts) for face in cage.faces]
    else:
        vertices = list(obj.data.vertices)
        positions = [tuple(vertex.co) for vertex in vertices]
        edges = [tuple(edge.vertices) for edge in obj.data.edges]
        faces = [tuple(face.vertices) for face in obj.data.polygons]
    signatures = vertex_signatures(positions, edges, faces)
    return (obj.name, tuple(sorted(signatures))), signatures, vertices, cage if obj.mode == "EDIT" else obj.data


def remember(obj, ids, history):
    key, signatures, vertices, owner = geometry(obj)
    if len(ids) != len(vertices) or len(ids) != len(set(ids)):
        return False
    buckets = {}
    for signature, vid in zip(signatures, ids):
        buckets.setdefault(signature, []).append(vid)
    history.pop(key, None)
    history[key] = {signature: tuple(values) for signature, values in buckets.items()}
    while len(history) > MAX_STATES:
        history.pop(next(iter(history)))
    return True


def restore(obj, history):
    from .mesh_io import ID_ATTR
    key, signatures, vertices, owner = geometry(obj)
    snapshot = history.get(key)
    if snapshot is None:
        return False
    available = {signature: list(values) for signature, values in snapshot.items()}
    if obj.mode == "EDIT":
        import bmesh
        cage = owner
        layer = cage.verts.layers.int.get(ID_ATTR)
        current = [vertex[layer] if layer else -1 for vertex in vertices]
    else:
        attribute = obj.data.attributes.get(ID_ATTR)
        current = [item.value for item in attribute.data] if attribute else [-1] * len(vertices)
    restored = []
    for signature, vid in zip(signatures, current):
        candidates = available[signature]
        chosen = vid if vid in candidates else candidates[0]
        candidates.remove(chosen)
        restored.append(chosen)
    if restored != current:
        if obj.mode == "EDIT":
            if layer is None:
                layer = cage.verts.layers.int.new(ID_ATTR)
                vertices = list(cage.verts)
            for vertex, vid in zip(vertices, restored):
                vertex[layer] = vid
            bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        else:
            attribute = attribute or obj.data.attributes.new(ID_ATTR, "INT", "POINT")
            attribute.data.foreach_set("value", restored)
    return True
