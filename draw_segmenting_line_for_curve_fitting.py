import bpy

from .utils import draw_utils
from .utils import math_utils
from .utils import cubic_curve_fitting_utils

from . import map_scene_data


class DrawSegmentingLineForCurveFitting(bpy.types.Operator):
    bl_idname = 'dsc.draw_segmenting_line_for_curve_fitting'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        ''''''

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                road_data = map_scene_data.get_road_data(road_id)
                lane_sections = road_data['lane_sections']
                section = lane_sections[section_id]
                lane = section['lanes'][lane_id]

                if lane['draw_segmenting_line_for_curve_fitting'] == False: # 分段线尚未显示，显示分段线。
                    cubic_curve_fitting_utils.draw_static_segmenting_line_for_curve_fitting(road_id, section_id, lane_id)
                    lane['draw_segmenting_line_for_curve_fitting'] = True
                else: # 分段线已经显示，隐藏分段线。
                    cubic_curve_fitting_utils.remove_static_segmenting_line_for_curve_fitting(road_id, section_id, lane_id)
                    lane['draw_segmenting_line_for_curve_fitting'] = False

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
 

