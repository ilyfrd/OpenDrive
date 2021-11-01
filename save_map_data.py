import bpy
from .utils import export_import_utils



class SaveMapData(bpy.types.Operator):
    bl_idname = 'dsc.save_map_data'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        export_import_utils.save_map_date()

        return {'FINISHED'}
