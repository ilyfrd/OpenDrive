import bpy
from .utils import export_import_utils



class ReloadMapData(bpy.types.Operator):
    bl_idname = 'dsc.reload_map_data'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        export_import_utils.reload_map_scene(context)

        return {'FINISHED'}
