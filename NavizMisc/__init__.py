import bpy
import bmesh


bl_info = {
    "name": "Naviz Misc",
    "author": "Formjune",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > My Addon Tab",
    "category": "Interface",
}


class NavizMisc(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Naviz Misc'
    bl_label = "Naviz Misc"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.naviz_split_by_materials", text="Split by 10 materials")
        layout.operator("object.naviz_create_uv", text="Create UV")
        layout.operator("object.naviz_rename_ucx", text="Rename UCX")


class SplitByMaterials(bpy.types.Operator):
    bl_idname = "object.naviz_split_by_materials"
    bl_label = "Split by Materials"
    bl_description = "Split by Materials (10 per part)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        if not obj or obj.type != 'MESH':
            return

        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        total_mats = len(obj.material_slots)
        if total_mats <= 10:
            bpy.ops.object.material_slot_remove_unused()
            return {"FINISHED"}

        orig_name = obj.name
        orig_name = orig_name.replace("_part1", "")
        obj.name = orig_name

        mat_slots = [slot.material for slot in obj.material_slots]

        chunks = [mat_slots[i:i + 10] for i in range(0, total_mats, 10)]

        for chunk_idx, chunk_mats in enumerate(chunks):
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.duplicate()
            new_obj = bpy.context.active_object
            new_obj.name = f"{orig_name}_part{chunk_idx + 1}"

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            keep_names = {m.name for m in chunk_mats if m}

            for poly in new_obj.data.polygons:
                slot = new_obj.material_slots[poly.material_index]
                if not slot.material or slot.material.name not in keep_names:
                    poly.select = True

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.material_slot_remove_unused()

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.delete()
        return {"FINISHED"}


class CreateUV(bpy.types.Operator):
    bl_idname = "object.naviz_create_uv"
    bl_label = "Create UV"
    bl_description = "Create UV and set Texel Density to 1024"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mesh in context.selected_objects:
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

                grid_image = bpy.data.images.new(name="uvgrid", width=1024, height=1024)
                grid_image.generated_type = 'UV_GRID'
                texture_node.image = grid_image

                # cube mapping
                bm = bmesh.new()
                bm.from_mesh(mesh.data)
                for face in bm.faces:
                    face.select = face.material_index == mat_index
                bm.to_mesh(mesh.data)

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.uv.cube_project(cube_size=1.0,correct_aspect=True,clip_to_bounds=False,scale_to_bounds=False)
                bpy.ops.object.mode_set(mode='OBJECT')

            bpy.context.scene.td.units = "1"
            bpy.context.scene.td.texture_size = "2048"

            bpy.ops.object.texel_density_preset_set(td_value="1024")
            bpy.ops.object.texel_density_set()
        return {"FINISHED"}


class RenameUCX(bpy.types.Operator):
    bl_idname = "object.naviz_rename_ucx"
    bl_label = "Rename UCX"
    bl_description = "Rename all objects in UCX collection"
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


CLASSES = NavizMisc, CreateUV, RenameUCX, SplitByMaterials


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
