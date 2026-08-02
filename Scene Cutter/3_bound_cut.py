import os
import itertools
import bpy
import bmesh
import mathutils
from mathutils.geometry import intersect_point_tri_2d

FOLDER_IN = r"E:\Yandex.Disk\2026.01.14 - NCV Msc Models\_work\Batch_10_Nikolskaya-Zone_1\Mesh"
FOLDER_OUT = r"E:/output_cut1"
SKIP_EXISTING = True
PREFIX = "bound_"

# 2D или 3D, второй проверяет вхождение точки в регион [min z, max z]
METHOD = "2D"

# временная папка для экономии оперативки. папка чистится во время работы, не указывать на рабочие
FOLDER_TMP = r"E:/tmp"
USE_TMP = True


def getCutter(mesh) -> list:
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    up_vector = mathutils.Vector((0, 0, 1))
    triangles = []
    for face in bm.faces:
        if up_vector.angle(face.normal) < 0.31415:
            triangles.append([(mesh.matrix_world @ v.co).to_2d() for v in face.verts])
    bm.to_mesh(mesh.data)
    bm.free()
    return triangles


def doOverlap(rect1: tuple, rect2: tuple) -> bool:
    x_min1, x_max1, y_min1, y_max1 = rect1[:4]
    x_min2, x_max2, y_min2, y_max2 = rect2[:4]
    if x_max1 <= x_min2 or x_max2 <= x_min1 or y_max1 <= y_min2 or y_max2 <= y_min1:
        return False
    return True


def getBoundary(mesh) -> tuple:
    world_corners = [mesh.matrix_world @ mathutils.Vector(corner) for corner in mesh.bound_box]
    x_max = max(world_corners, key=lambda v: v.x).x
    x_min = min(world_corners, key=lambda v: v.x).x
    y_max = max(world_corners, key=lambda v: v.y).y
    y_min = min(world_corners, key=lambda v: v.y).y
    z_max = max(world_corners, key=lambda v: v.z).z
    z_min = min(world_corners, key=lambda v: v.z).z
    return x_min, x_max, y_min, y_max, z_min, z_max


def performSplit(mesh, triangles: list, min_z, max_z) -> None:
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    delete = []
    if METHOD == "2D":
        for vertex in bm.verts:
            p = (mesh.matrix_world @ vertex.co).to_2d()
            if not any(map(lambda t: intersect_point_tri_2d(p, *t), triangles)):
                delete.append(vertex)
    else:
        for vertex in bm.verts:
            p = mesh.matrix_world @ vertex.co
            if not min_z <= p.z <= max_z or not any(map(lambda t: intersect_point_tri_2d(p.to_2d(), *t), triangles)):
                delete.append(vertex)

    bmesh.ops.delete(bm, geom=delete, context='VERTS')
    bm.to_mesh(mesh.data)
    bm.free()


def deleteHighMeshes(low_mesh_names: set) -> None:
    bpy.ops.object.select_all(action='DESELECT')
    for mesh in bpy.context.scene.objects:
        if mesh.name not in low_mesh_names:
            mesh.select_set(True)
    bpy.ops.object.delete(use_global=False)


def saveFbx(name: str, *meshes):
    bpy.ops.object.select_all(action='DESELECT')
    for mesh in meshes:
        mesh.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=name,
        use_selection=True,
        use_mesh_modifiers=True,
        axis_forward='-Z',
        axis_up='Y'
    )


def main() -> None:
    os.makedirs(FOLDER_OUT, exist_ok=True)
    high_mesh_bounds = {}
    low_mesh_names = set()
    counter = itertools.count()
    # bpy.ops.ed.undo_push()

    for mesh in bpy.context.scene.objects:
        if mesh.type == 'MESH':
            continue
        elif mesh.name.startswith(PREFIX):
            low_mesh_names.add(mesh.name)
        else:
            high_mesh_bounds[mesh.name] = getBoundary(mesh)

    # start loading for every figure
    deleteHighMeshes(low_mesh_names)
    for low_mesh in tuple(bpy.context.scene.objects):
        name_out = os.path.join(FOLDER_OUT, low_mesh.name.replace(PREFIX, "", 1) + ".fbx")
        if SKIP_EXISTING and os.path.isfile(name_out):
            continue

        # clean temp folder
        if USE_TMP:
            os.makedirs(FOLDER_TMP, exist_ok=True)
            for file in os.listdir(FOLDER_TMP):
                os.remove(os.path.join(FOLDER_TMP, file))

        # perform cut
        low_bounds = getBoundary(low_mesh)
        cutter = getCutter(low_mesh)
        deleteHighMeshes(low_mesh_names)
        for high_name, bbox in high_mesh_bounds.items():
            if doOverlap(low_bounds, bbox):
                bpy.ops.import_scene.fbx(filepath=os.path.join(FOLDER_IN, high_name + ".fbx"))
                high_mesh = bpy.context.scene.objects[high_name]
                performSplit(high_mesh, cutter, *low_bounds[4:])
                if not len(high_mesh.data.vertices):
                    bpy.data.objects.remove(high_mesh, do_unlink=True)
                elif USE_TMP:
                    saveFbx(os.path.join(FOLDER_TMP, f"{next(counter)}.fbx"), high_mesh)
                    bpy.data.objects.remove(high_mesh, do_unlink=True)

        # save meshes
        if USE_TMP:
            deleteHighMeshes(low_mesh_names)
            for file in os.listdir(FOLDER_TMP):
                bpy.ops.import_scene.fbx(filepath=os.path.join(FOLDER_TMP, file))
        saveFbx(name_out, low_mesh, *[m for m in bpy.context.scene.objects if m.name not in low_mesh_names])

    # bpy.ops.ed.undo()
    # reimport low fbx at the end
    deleteHighMeshes(low_mesh_names)
    for file in os.listdir(FOLDER_IN):
        if file.endswith("_low.fbx"):
            bpy.ops.import_scene.fbx(filepath=os.path.join(FOLDER_IN, file))


main()
