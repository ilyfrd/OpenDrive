import bpy
from bpy.props import StringProperty, BoolProperty 

from .utils import export_import_utils



class SaveMapScene(bpy.types.Operator):
    bl_idname = 'dsc.save_map_scene'
    bl_label = '确定'
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    filter_glob: StringProperty( 
        default='*.json; *.xodr', 
        options={'HIDDEN'} )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context): 
        export_import_utils.save_map_date(self.filepath)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
