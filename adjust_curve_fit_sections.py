import bpy

from .utils import draw_utils
from .utils import math_utils
from .utils import road_utils
from . import helpers
from . import map_scene_data

from . draw_curve_base import DrawCurveBase



class AdjustCurveFitSections(DrawCurveBase):
    bl_idname = 'dsc.adjust_curve_fit_sections'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        DrawCurveBase.__init__(self)

        self.selected_lane = None

    

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if self.selected_lane != None:
            DrawCurveBase.modal(self, context, event)

        if event.type == 'MOUSEMOVE':


            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            
           
            self.clean_up(context)

            return {'FINISHED'}
            
        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type in {'MIDDLEMOUSE'}:
            if event.alt:
                bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        draw_utils.set_context(context)

        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        context.workspace.status_text_set(None)

        bpy.context.window.cursor_modal_restore()

        if bpy.context.active_object:
            if bpy.context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
 

