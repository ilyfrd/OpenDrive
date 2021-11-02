import bpy
from .utils import export_import_utils



class ExportOpenDriveMap(bpy.types.Operator):
    bl_idname = 'dsc.export_open_drive_map'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        export_import_utils.export_open_drive_map()

        return {'FINISHED'}
