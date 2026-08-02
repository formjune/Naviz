import json
import os
import bpy
import bmesh
from mathutils import Vector

bl_info = {
    "name": "PolyToFont",
    "author": "Pitblastbeat",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > My Addon Tab",
    "description": "Делаем надписи из полигона",
    "category": "Interface",
}


def get_fonts():
    fonts = []
    for file in os.listdir(os.path.dirname(__file__)):
        if not file.endswith(".json"):
            continue
        name = os.path.splitext(file)[0]
        fonts.append((name, name, ""))
    return fonts


class PolyToFontProperty(bpy.types.PropertyGroup):
    text: bpy.props.StringProperty(
        name="Text",
        default="улица"
    )

    font: bpy.props.EnumProperty(
        name="Font",
        items=get_fonts()
    )

    size: bpy.props.FloatProperty(
        name="Height",
        default=1,
        min=0.0,
    )

    center: bpy.props.BoolProperty(
        name="Center To Cursor",
        default=True
    )


class PolyToFontPanel(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyToFont'
    bl_label = "Settings"

    def draw(self, context):
        props = context.scene.poly_to_font_props
        layout = self.layout
        layout.prop(props, "text")
        layout.prop(props, "font")
        layout.prop(props, "size")
        layout.prop(props, "center")
        layout.separator()
        layout.operator("object.poly_to_font", icon='TEXT')


class PolyToFontOperator(bpy.types.Operator):
    bl_idname = "object.poly_to_font"
    bl_label = "Create Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        json_data = json.load(open(f"{os.path.dirname(__file__)}/{context.scene.poly_to_font_props.font}.json"))
        offset, pairs, uv_coord = json_data
        mesh_data = bpy.data.meshes.new(name="banner" + "_Data")
        mesh_obj = bpy.data.objects.new(name="banner", object_data=mesh_data)
        bpy.context.collection.objects.link(mesh_obj)
        mesh_obj.rotation_euler = bpy.context.region_data.view_matrix.to_3x3().inverted().to_euler()
        mesh_obj.location = bpy.context.scene.cursor.location
        bm = bmesh.new()
        bm.from_mesh(mesh_obj.data)

        vertices_bottom = []
        vertices_top = []
        width = 0
        u_min, u_max, v_min, v_max = uv_coord[" "]
        height = v_max - v_min

        vertices_bottom.append(bm.verts.new(Vector((0, 0, 0))))
        vertices_top.append(bm.verts.new(Vector((0, height, 0))))
        prev_letter = ""
        for i, letter in enumerate(context.scene.poly_to_font_props.text, 1):
            try:
                u_min, u_max, v_min, v_max = uv_coord[letter]
            except KeyError:
                continue

            pair = prev_letter + letter
            if pair in pairs:
                u_min += pairs[pair] * offset
            if i == len(context.scene.poly_to_font_props.text):
                u_max += offset
            prev_letter = letter

            width += u_max - u_min
            vertices_bottom.append(bm.verts.new(Vector((width, 0, 0))))
            vertices_top.append(bm.verts.new(Vector((width, height, 0))))

            new_face = bm.faces.new((vertices_bottom[-2], vertices_bottom[-1], vertices_top[-1], vertices_top[-2]))
            uv_layer = bm.loops.layers.uv.verify()
            new_face.loops[0][uv_layer].uv = u_min, v_min
            new_face.loops[1][uv_layer].uv = u_max, v_min
            new_face.loops[2][uv_layer].uv = u_max, v_max
            new_face.loops[3][uv_layer].uv = u_min, v_max

        if context.scene.poly_to_font_props.center:
            for vertex in bm.verts:
                vertex.co -= Vector((width / 2, height / 2, 0))

        bm.to_mesh(mesh_obj.data)
        bm.free()
        mesh_obj.data.update()
        mesh_obj.scale = [context.scene.poly_to_font_props.size / height] * 3
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        return {'FINISHED'}


classes = PolyToFontProperty, PolyToFontOperator, PolyToFontPanel


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.poly_to_font_props = bpy.props.PointerProperty(type=PolyToFontProperty)


def unregister():
    del bpy.types.Scene.poly_to_font_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
