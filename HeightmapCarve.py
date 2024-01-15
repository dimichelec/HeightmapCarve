bl_info = {
    "name": "Heightmap Carve",
    "author": "Carmen DiMichele",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Toolbar",
    "description": "Create a grid from a heightmap image",
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty
from bpy.types import Operator, Panel

from typing import Final
import random


TEXTURE_NAME: Final = "HMCTexture"
MESH_NAME: Final =    "HMCMesh"


class VIEW3D_PT_HeightmapCarve(Panel):
    """Creates a Panel in the View 3D window"""
    
    bl_label = "Heightmap Carve"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Heightmap Carve"
    
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator('import.open_image', text='Open Heightmap Image', icon='FILE')

        if TEXTURE_NAME in bpy.data.textures:
            img = bpy.data.textures[TEXTURE_NAME].image

            row = layout.row()
            row.label(text=img.name)
            
            row = layout.row()
            row.label(text="%d x %d"%(img.size[0],img.size[1]))
            
            row = layout.row()
            row.prop(context.scene,"grid_rows")
            
            row = layout.row()
            row.prop(context.scene,"height")
            
            row = layout.row()
            row.prop(context.scene,"invert")
            
            row = layout.row()
            row.prop(context.scene,"flip_alpha")
            
            row = layout.row()
            ops = row.operator('mesh.create_grid', text='(Re)create Grid', icon='MESH_GRID')
            ops.grid_rows = context.scene.grid_rows
            ops.height = context.scene.height
            ops.invert = context.scene.invert
            ops.flip_alpha = context.scene.flip_alpha
            
            if MESH_NAME in bpy.data.meshes:
                mesh = bpy.data.meshes[MESH_NAME]
                
                row = layout.row()
                row.label(text="%d vertices"%len(mesh.vertices))
    

class IMPORT_OT_OpenImage(Operator, ImportHelper):
    """Import an image"""

    bl_idname = 'import.open_image'
    bl_label = "Open Image"

    filter_glob: StringProperty(
        default="*.jpg;*.jpeg;*.png;*.bmp;*.psd;*.tiff",
        options={'HIDDEN'},
        maxlen=255
    )

    def execute(self, context):
        if TEXTURE_NAME in bpy.data.textures:
            tex = bpy.data.textures[TEXTURE_NAME]
            if tex.image:
                bpy.data.images.remove(tex.image)
            bpy.data.textures.remove(tex)
            
        tex = bpy.data.textures.new(name=TEXTURE_NAME, type='IMAGE')

        tex.image = bpy.data.images.load(self.filepath)
        tex.extension = 'CLIP'
        return {'FINISHED'}


class MESH_OT_CreateGrid(Operator):
    """Creates, or recreates, a grid from a heightmap image"""
    
    bl_idname = 'mesh.create_grid'
    bl_label = "Create Grid"

    grid_rows: bpy.props.IntProperty()
    height: bpy.props.FloatProperty()
    invert: bpy.props.BoolProperty()
    flip_alpha: bpy.props.BoolProperty()
    
    def execute(self, context):
        if MESH_NAME in bpy.data.meshes:
            bpy.data.meshes.remove(bpy.data.meshes[MESH_NAME])

        img = bpy.data.textures[TEXTURE_NAME].image
        img_width = img.size[0]
        img_length = img.size[1]

        grid_width = self.grid_rows
        
        scale = grid_width / img_width 
        grid_length = int(scale * img_length)

        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions = grid_width,
            y_subdivisions = grid_length,
            scale = (scale, scale, 1.0)
        )
        obj = bpy.context.active_object
        obj.name = MESH_NAME
        mesh = obj.data
        mesh.name = MESH_NAME
        
        img2 = img.copy()
        img2.scale(grid_width+1,grid_length+1)

        verts = mesh.vertices
        
        img2_index = 0
        for i in range(len(verts)):
            r = img2.pixels[img2_index]
            g = img2.pixels[img2_index + 1]
            b = img2.pixels[img2_index + 2]
            h = (r + g + b) / 3.0
            if not self.invert:
                h = 1.0 - h
            a = img2.pixels[img2_index + 3]
            if a == 0.0:
                if self.flip_alpha ^ self.invert:
                    h = 1.0
                else:
                    h = 0.0
            h = self.height * h
            
            img2_index += 4
            verts[i].co[2] = h
        
        bpy.data.images.remove(img2)

        return {"FINISHED"}


def register():
    bpy.types.Scene.grid_rows = IntProperty(name="Grid rows", default=20, min=10, max=300)
    bpy.types.Scene.height = FloatProperty(name="Height", default=0.5, min=0.0001, max=1.0)
    bpy.types.Scene.invert = BoolProperty(name="Invert", default=False)
    bpy.types.Scene.flip_alpha = BoolProperty(name="Flip alpha", default=False)

    bpy.utils.register_class(VIEW3D_PT_HeightmapCarve)
    bpy.utils.register_class(IMPORT_OT_OpenImage)
    bpy.utils.register_class(MESH_OT_CreateGrid)


def unregister():
    del bpy.types.Scene.grid_rows
    del bpy.types.Scene.height
    del bpy.types.Scene.invert
    del bpy.types.Scene.flip_alpha
    
    bpy.utils.unregister_class(VIEW3D_PT_HeightmapCarve)
    bpy.utils.unregister_class(IMPORT_OT_OpenImage)
    bpy.utils.unregister_class(MESH_OT_CreateGrid)


if __name__ == "__main__":
    register()

