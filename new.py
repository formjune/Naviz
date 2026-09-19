import bpy
import bmesh
import mathutils


def buildMatrix(center, point_1, point_2):
    vector_1 = point_1 - center
    vector_2 = point_2 - center
    vector_3 = vector_1.cross(vector_2)
    vector_2 = vector_3.cross(vector_1)
    vector_1.normalize()
    vector_2.normalize()
    vector_3.normalize()
    matrix = mathutils.Matrix((
        (vector_1.x, vector_1.y, vector_1.z, center.x),
        (vector_2.x, vector_2.y, vector_2.z, center.y),
        (vector_3.x, vector_3.y, vector_3.z, center.z),
        (0, 0, 0, 1)
    ))
    return matrix








active = bpy.context.active_object
bm = bmesh.new()
bm.from_mesh(active.data)
for item in bm.select_history:
    print(item)





bm.edges
sel_edges = [edge for edge in bm.edges if edge.select]
verts_1 = list(sel_edges[0].verts)
verts_2 = list(sel_edges[1].verts)

if verts_1[1] not in verts_2:
    verts_1.reverse()
if verts_2[0] not in verts_1:
    verts_2.reverse()
bm.free()

points = [
    active.matrix_world @ verts_1[0].co,
    active.matrix_world @ verts_1[1].co,
    active.matrix_world @ verts_2[1].co
]

m_out = buildMatrix(*points)
