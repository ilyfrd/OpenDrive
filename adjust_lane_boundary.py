
import bpy

from . import utils
from . import draw_utils
from . import math_utils
from . import road_utils
from . import helpers
from . import map_scene_data

from . draw_curve_base import DrawCurveBase



class AdjustLaneBoundary(DrawCurveBase):
    bl_idname = 'dsc.adjust_lane_boundary'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        DrawCurveBase.__init__(self)

        self.selected_lane = None
        self.lane_boundary = None 

    def draw_lane_boundary(self):
        draw_utils.draw_curve('lane_boundary', self.reference_line_elements)

    def remove_lane_boundary(self):
        draw_utils.remove_curve('lane_boundary')

    def draw_end_tangent(self):
        last_element = self.reference_line_elements[len(self.reference_line_elements) - 1]

        line_direction = last_element['end_tangent'].copy()
        line_direction.normalize()
        math_utils.vector_scale_ref(line_direction, 10)

        line_start_point = last_element['end_point'].copy()
        line_end_point = math_utils.vector_add(line_start_point, line_direction)

        draw_utils.draw_dashed_line('adjust_lane_boundary', line_start_point, line_end_point, 0.5, 0.3)

    def remove_end_tangent(self):
        draw_utils.remove_dashed_line('adjust_lane_boundary')

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("Place object by clicking, hold CTRL to snap to grid, "
            "press RIGHTMOUSE to cancel selection, press ESCAPE to exit.")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if self.selected_lane != None:
            DrawCurveBase.modal(self, context, event)

        if event.type == 'MOUSEMOVE':
            if len(self.reference_line_elements) > 0:
                self.draw_lane_boundary()
                self.draw_end_tangent()

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.selected_lane != None:
                return {'RUNNING_MODAL'}

            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                selected_section = selected_road['lane_sections'][section_id]
                if lane_id == selected_section['left_most_lane_index'] or lane_id == selected_section['right_most_lane_index']:
                    self.selected_lane = raycast_object
                    self.selected_lane.hide_set(True)

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            self.remove_lane_boundary()
            self.remove_end_tangent()

            if len(self.reference_line_elements) > 1: 
                self.reference_line_elements.pop()

                name_sections = self.selected_lane.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                selected_section = selected_road['lane_sections'][section_id]
                selected_section['lanes'][lane_id]['boundary_curve_elements'] = self.reference_line_elements.copy()

                new_lane_mesh = None
                if lane_id == selected_section['left_most_lane_index']:
                    new_lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][lane_id]['boundary_curve_elements'], selected_section['lanes'][lane_id - 1]['boundary_curve_elements'])
                elif lane_id == selected_section['right_most_lane_index']:
                    new_lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][lane_id + 1]['boundary_curve_elements'], selected_section['lanes'][lane_id]['boundary_curve_elements'])
                helpers.replace_mesh(self.selected_lane, new_lane_mesh)
            
            if self.selected_lane != None:
                self.selected_lane.hide_set(False)
           
            self.clean_up(context)

            return {'FINISHED'}
            
        # Zoom
        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type in {'MIDDLEMOUSE'}:
            if event.alt:
                bpy.ops.view3d.view_center_cursor()

        # Catch everything else arriving here
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
 

