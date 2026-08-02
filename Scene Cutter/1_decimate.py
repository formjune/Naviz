import os
import bpy
import bmesh
import mathutils


FOLDER = r"E:\Yandex.Disk\2026.01.14 - NCV Msc Models\_work\Batch_11_TverskoyBulvar\Mesh"
MERGE_THRESHOLD = .1
BUILD_FINAL_SCENE = True
SKIP_EXISTING = True


def clearScene() -> None:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def main() -> None:
    for file in sorted(os.listdir(FOLDER), key=lambda x: x.lower()):
        if not file.endswith(".fbx") or file.endswith("_low.fbx"):
            continue
        filename = os.path.join(FOLDER, file)
        filename_out = filename.replace(".fbx", "_low.fbx")
        if SKIP_EXISTING and os.path.exists(filename_out):
            continue

        clearScene()
        bpy.ops.import_scene.fbx(filepath=filename)
        for mesh in bpy.context.scene.objects:
            if not mesh.type == 'MESH':
                continue
            modifier = mesh.modifiers.new(name="Merge", type='WELD')
            modifier.merge_threshold = MERGE_THRESHOLD
            bpy.ops.object.convert(target='MESH')

        bpy.ops.export_scene.fbx(
            filepath=filename_out,
            use_selection=False,
            use_mesh_modifiers=True,
            axis_forward='-Z',
            axis_up='Y'
        )

    # create scene
    clearScene()
    if BUILD_FINAL_SCENE:
        for file in os.listdir(FOLDER):
            if file.endswith("_low.fbx"):
                bpy.ops.import_scene.fbx(filepath=os.path.join(FOLDER, file))
        bpy.context.window.workspace = bpy.data.workspaces['Layout']
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER, "full_scene.blend"))


main()