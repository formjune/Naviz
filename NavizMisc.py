import os
import re
import random
import bpy
import bmesh
import mathutils


bl_info = {
    "name": "Naviz Misc",
    "author": "Formjune",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > My Addon Tab",
    "category": "Interface",
}


class NavizProperty(bpy.types.PropertyGroup):

    root_folder: bpy.props.StringProperty(name="Root Folder", default="")
    resolution: bpy.props.EnumProperty(
        name="Resolution",
        items=[
            ("_128", "128", ""),
            ("_256", "256", ""),
            ("_512", "512", ""),
            ("_1024", "1024", ""),
            ("_2048", "2048", ""),
            ("_4096", "4096", ""),
            ("_8192", "8192", ""),
            ("_", "original", "")
        ]
    )
    linker_collection: bpy.props.StringProperty(name="Collection", default="")
    linker_filename: bpy.props.StringProperty(name="Filename", default="")


class NavizMisc(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Naviz Misc'
    bl_label = "Naviz Misc"

    def draw(self, context):
        layout = self.layout
        props = context.scene.naviz_property
        layout.operator("object.naviz_randomize_material_colors", text="Randomize Material Colors")
        layout.operator("object.naviz_remove_materials", text="Remove Materials")
        layout.operator("object.naviz_select_by_materials_count", text="Select meshes with 11+ materials")
        layout.operator("object.naviz_split_by_materials", text="Split by 10 materials")
        layout.separator(type="LINE")
        layout.operator("object.naviz_create_uv", text="Create UV")
        layout.operator("object.naviz_rename_ucx", text="Rename UCX")
        layout.operator("object.naviz_export_geometry", text="Export Geometry")
        layout.separator(type="LINE")
        row = layout.row()
        row.prop(props, "root_folder")
        row.operator("object.naviz_get_path", text="Get .blend Directory")
        layout.operator("object.naviz_load_obj", text="Load OBJ")
        layout.separator()
        layout.prop(props, "resolution")
        layout.operator("object.naviz_reload_textures", text="Reload Textures")
        layout.separator()
        layout.prop(props, "linker_filename")
        layout.prop(props, "linker_collection")
        layout.operator("object.naviz_linker_exporter", text="Export to Global Coordinates")


class LinkerExporter(bpy.types.Operator):
    bl_idname = "object.naviz_linker_exporter"
    bl_label = "Linker Exporter"
    bl_description = "Export objects to global coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    SKIP_NAMES = {"ref_local", "ref_global"}

    @staticmethod
    def buildMatrix(point_1, point_2):
        vector_1 = point_2 - point_1
        vector_1.normalize()
        vector_up = mathutils.Vector((0, 0, 1))
        vector_2 = vector_1.cross(vector_up)

        matrix = mathutils.Matrix((
            (vector_1.x, vector_1.y, 0, point_2.x),
            (vector_2.x, vector_2.y, 0, point_2.y),
            (0, 0, 1, point_2.z),
            (0, 0, 0, 1)
        ))
        return matrix

    def execute(self, context):
        mesh = bpy.data.objects["ref_local"]

        bm = bmesh.new()
        bm.from_mesh(mesh.data)

        for edge in bm.edges:
            vertex_1 = mesh.matrix_world @ edge.verts[0].co
            vertex_2 = mesh.matrix_world @ edge.verts[1].co
            if abs(vertex_1.z - vertex_2.z) < 1e-3:
                index_1 = edge.verts[0].index
                index_2 = edge.verts[1].index
                break
        else:
            return {"FINISHED"}

        mesh = bpy.data.objects["ref_local"]
        point_1 = mesh.matrix_world @ mesh.data.vertices[index_1].co
        point_2 = mesh.matrix_world @ mesh.data.vertices[index_2].co
        matrix_in = self.buildMatrix(point_1, point_2).inverted()

        mesh = bpy.data.objects["ref_global"]
        point_1 = mesh.matrix_world @ mesh.data.vertices[index_1].co
        point_2 = mesh.matrix_world @ mesh.data.vertices[index_2].co
        matrix_out = self.buildMatrix(point_1, point_2)

        restore_data = []
        for mesh in bpy.data.collections[context.scene.naviz_property.linker_collection].objects:
            if mesh.type != "MESH" or mesh.name in self.SKIP_NAMES:
                continue
            restore_data.append((mesh, mesh.matrix_world.copy()))
            mesh.matrix_world = matrix_out @ matrix_in @ mesh.matrix_world

        bpy.ops.wm.save_as_mainfile(filepath=context.scene.naviz_property.linker_filename, copy=True)
        for mesh, matrix in restore_data:
            mesh.matrix_world = matrix
        return {"FINISHED"}


class GetPath(bpy.types.Operator):
    bl_idname = "object.naviz_get_path"
    bl_label = "Get .blend Path"
    bl_description = "Get .blend path"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.naviz_property.root_folder = os.path.dirname(bpy.data.filepath)
        return {"FINISHED"}


class LoadObj(bpy.types.Operator):
    bl_idname = "object.naviz_load_obj"
    bl_label = "Load Objects"
    bl_description = "Load objects from root folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        root_folder = context.scene.naviz_property.root_folder
        for folder, _, files in os.walk(root_folder):
            for file in files:
                if not file.endswith(".obj"):
                    continue
                bpy.ops.wm.obj_import(filepath=os.path.join(folder, file))
                for obj in bpy.context.selected_objects:
                    obj.name = f"{os.path.split(folder)[1]}_{file}"
        return {"FINISHED"}


class ReloadTextures(bpy.types.Operator):
    bl_idname = "object.naviz_reload_textures"
    bl_label = "Reload Textures"
    bl_description = "Reload textures for selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        root_folder = context.scene.naviz_property.root_folder
        suffix = context.scene.naviz_property.resolution
        if suffix == "_":
            suffix = ""

        for mesh in bpy.context.selected_objects:
            if mesh.type != "MESH":
                continue

            for i, mat_slot in enumerate(mesh.material_slots):

                result = re.findall("(.*)_(.*)\\.(.*)", mesh.name)
                if not result:
                    continue
                folder, obj = result[0][:2]
                texture_number = f"_{i}" if i else ""
                texture_name = f"{root_folder}/{folder}/{obj}{texture_number}{suffix}.jpg"

                if os.path.isfile(texture_name):
                    image = bpy.data.images.load(texture_name)
                else:
                    continue
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        prev_image = node.image
                        node.image = image
                        bpy.data.images.remove(prev_image)
        return {"FINISHED"}


class RandomizeMaterialColors(bpy.types.Operator):
    bl_idname = "object.naviz_randomize_material_colors"
    bl_label = "Randomize Material Colors"
    bl_description = "Randomize material colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        # Loop through all selected mesh objects
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes:
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links

                    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
                    if principled:
                        color = principled.inputs['Base Color']
                        for link in list(color.links):
                            links.remove(link)
                        color.default_value = random.random(), random.random(), random.random(), 1.0
        return {"FINISHED"}


class RemoveMaterials(bpy.types.Operator):
    bl_idname = "object.naviz_remove_materials"
    bl_label = "Remove Materials"
    bl_description = "Remove materials from selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mesh in bpy.context.selected_objects:
            if mesh.type == "MESH":
                mesh.data.materials.clear()
        return {"FINISHED"}

class SelectByMaterialCount(bpy.types.Operator):
    bl_idname = "object.naviz_select_by_materials_count"
    bl_label = "Select by material count"
    bl_description = "Select meshes with 11+ materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mesh in bpy.data.objects:
            mesh.select_set(mesh.type == "MESH" and len(mesh.material_slots) > 10)
        return {"FINISHED"}


class SplitByMaterials(bpy.types.Operator):
    bl_idname = "object.naviz_split_by_materials"
    bl_label = "Split by Materials"
    bl_description = "Split selected by materials (10 per part)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mesh in tuple(context.selected_objects):
            if mesh.type != "MESH" or len(mesh.material_slots) <= 10:
                continue

            orig_name = mesh.name
            orig_name = orig_name.replace("_part1", "")
            mesh.name = "tmp_name"

            for chunk_index, i in enumerate(range(0, len(mesh.material_slots), 10), 1):
                materials = range(i, i + 10)

                bpy.ops.object.select_all(action="DESELECT")
                mesh.select_set(True)
                bpy.context.view_layer.objects.active = mesh

                bpy.ops.object.duplicate()
                new_mesh = bpy.context.active_object
                new_mesh.name = f"{orig_name}_part{chunk_index}"

                bm = bmesh.new()
                bm.from_mesh(new_mesh.data)
                bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in materials], context="FACES")
                bm.to_mesh(new_mesh.data)
                bm.free()
                bpy.ops.object.material_slot_remove_unused()

            # let's delete source
            bpy.ops.object.select_all(action='DESELECT')
            mesh.select_set(True)
            bpy.context.view_layer.objects.active = mesh
            bpy.ops.object.delete()
        return {"FINISHED"}


class CreateUV(bpy.types.Operator):
    bl_idname = "object.naviz_create_uv"
    bl_label = "Create UV"
    bl_description = "Create UV and set Texel Density to 1024. Requires Texel Density plugin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        bpy.context.scene.td.units = "1"
        bpy.context.scene.td.texture_size = "2048"
        grid_image = bpy.data.images.new(name="uvgrid", width=1024, height=1024)
        grid_image.generated_type = 'UV_GRID'

        for mesh in context.selected_objects:
            if mesh.type != 'MESH':
                continue

            bpy.context.view_layer.objects.active = mesh
            for mat_index, mat_slot in enumerate(mesh.material_slots):
                material = mat_slot.material

                # apply material
                nodes = material.node_tree.nodes
                links = material.node_tree.links

                bsdf_node = nodes.get("Principled BSDF")
                coord_node = nodes.new(type="ShaderNodeTexCoord")
                mapping_node = nodes.new(type="ShaderNodeMapping")
                texture_node = nodes.new(type="ShaderNodeTexImage")

                x, y = bsdf_node.location
                coord_node.location = (x - 700, y)
                mapping_node.location = (x - 500, y)
                texture_node.location = (x - 300, y)

                links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
                links.new(mapping_node.outputs["Vector"], texture_node.inputs["Vector"])
                links.new(texture_node.outputs["Color"], bsdf_node.inputs["Base Color"])

                texture_node.image = grid_image

                # cube mapping
                bm = bmesh.new()
                bm.from_mesh(mesh.data)
                for face in bm.faces:
                    face.select = face.material_index == mat_index
                bm.to_mesh(mesh.data)

                # resize uv (needs texel density plugin)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=False)
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.texel_density_preset_set(td_value="1024")
                bpy.ops.object.texel_density_set()
        return {"FINISHED"}


class RenameUCX(bpy.types.Operator):
    bl_idname = "object.naviz_rename_ucx"
    bl_label = "Rename UCX"
    bl_description = "Rename all objects in UCX collection. Make sure to have SM_*_part1 object in scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mesh in bpy.data.objects:
            if mesh.name.endswith("part1"):
                main_name = mesh.name
                break
        else:
            return {"FINISHED"}
        for i, mesh in enumerate(bpy.data.collections["UCX"].objects):
            mesh.name = f"UCX_{main_name}_{i:03}" if i else f"UCX_{main_name}"
        return {"FINISHED"}


class Export(bpy.types.Operator):
    bl_idname = "object.naviz_export_geometry"
    bl_label = "Export Geometry"
    bl_description = "Create folders and export geometry. Opened file must be placed in /blender"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not bpy.data.filepath:
            return {"FINISHED"}
        project_dir, file_dir = os.path.split(os.path.dirname(bpy.data.filepath))
        if file_dir.lower() != "blender":
            return {"FINISHED"}
        os.makedirs(os.path.join(project_dir, "Preview"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "Texture"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "_OUT"), exist_ok=True)

        for mesh in bpy.data.collections["mesh"].objects:
            bpy.ops.object.select_all(action="DESELECT")
            mesh.select_set(True)
            if mesh.name.endswith("_part1"):
                for ucx_mesh in bpy.data.collections["UCX"].objects:
                    ucx_mesh.select_set(True)
            bpy.ops.export_scene.fbx(
                filepath=os.path.join(project_dir, "_OUT", mesh.name + ".fbx"),
                use_selection=True,
                use_mesh_modifiers=True,
                use_triangles=True,
                axis_forward="X",
                axis_up="Z",
                global_scale=1.0,
                apply_unit_scale=True
            )
        return {"FINISHED"}


CLASSES = (NavizProperty, NavizMisc, CreateUV, RenameUCX, SplitByMaterials, SelectByMaterialCount, Export, LoadObj,
           ReloadTextures, GetPath, RemoveMaterials, RandomizeMaterialColors, LinkerExporter)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.naviz_property = bpy.props.PointerProperty(type=NavizProperty)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.naviz_property
