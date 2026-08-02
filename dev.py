import bpy
import os


filepath = bpy.data.filepath.lower().replace("\\", "/")
folders = filepath.split("/")
if folders and folders[-2] == "blender":
    folder = os.path.join(*folders[:-2])
    os.makedirs(os.path.join(folder, "Preview"), exist_ok=True)
    os.makedirs(os.path.join(folder, "Texture"), exist_ok=True)
    os.makedirs(os.path.join(folder, "_OUT"), exist_ok=True)





