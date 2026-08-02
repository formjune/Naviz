import json
import os
import bpy
import bmesh
import mathutils

FOLDER = r"E:\input"


def main() -> None:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for file in os.listdir(FOLDER):
        if file.endswith("_low.fbx"):
            bpy.ops.import_scene.fbx(filepath=os.path.join(FOLDER, file))
    bpy.context.window.workspace = bpy.data.workspaces['Layout']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER, "full_scene.blend"))


main()