
import bpy

from math import acos, ceil, radians, dist
from mathutils import geometry, Vector, Matrix

import numpy as np
from scipy.optimize import curve_fit

from .utils import basic_element_utils
from .utils import draw_utils
from .utils import math_utils
from .utils import road_utils
from . import helpers
from . import map_scene_data

def cubic_curve_function(x, a, b, c, d):
    return a + b*x + c*pow(x,2) + d*pow(x,3) 

class CheckLaneWidthCurveFit(bpy.types.Operator):
    bl_idname = 'dsc.check_lane_width_curve_fit'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        ''''''

    def prepare_arrays_for_curve_fit(self, center_lane_boundary, lane_boundary, adjacent_lane_boundary):
        x_array = []
        y_array = []

        curve_length = basic_element_utils.computer_curve_length(center_lane_boundary)
        divisions = 20
        sampling_step = curve_length / divisions

        def prepare_array_item(curve_distance):
            intersected_point_on_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, lane_boundary)
            intersected_point_on_adjacent_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, adjacent_lane_boundary)
            sampled_width = dist(intersected_point_on_lane_boundary, intersected_point_on_adjacent_lane_boundary)
            x_array.append(curve_distance)
            y_array.append(sampled_width)

        curve_distance = 0.001 * curve_length
        prepare_array_item(curve_distance)

        for index in range(1, divisions):
            curve_distance = sampling_step * index
            prepare_array_item(curve_distance)

        curve_distance = 0.999 * curve_length
        prepare_array_item(curve_distance)

        return x_array, y_array

    def show_cubic_curve_points(self, lane_identification, cubic_curve_factors, center_lane_boundary, lane_boundary, adjacent_lane_boundary):
        a, b, c, d = cubic_curve_factors
        curve_length = basic_element_utils.computer_curve_length(center_lane_boundary)
        divisions = 50
        sampling_step = curve_length / divisions
        for index in range(1, divisions):
            curve_distance = sampling_step * index
            intersected_point_on_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, lane_boundary)
            intersected_point_on_adjacent_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, adjacent_lane_boundary)
            direction = math_utils.vector_subtract(intersected_point_on_lane_boundary, intersected_point_on_adjacent_lane_boundary)
            direction.normalize()
            math_utils.vector_scale_ref(direction, cubic_curve_function(curve_distance, a, b, c, d))
            check_point = math_utils.vector_add(intersected_point_on_adjacent_lane_boundary, direction)
            draw_utils.draw_point('cubic_curve_point_' + lane_identification + '_' + str(draw_utils.generate_unique_id()), check_point)

    def hide_cubic_curve_points(self, lane_identification):
        draw_utils.remove_point_by_feature('cubic_curve_point_' + lane_identification)

    def check_lane_width(self, road_id, section_id, lane_id):
        if lane_id == 0: # 车道号为0的中心车道是没有宽度的，不需要检查。
            return

        road_data = map_scene_data.get_road_data(road_id)
        lane_sections = road_data['lane_sections']
        lane_section = lane_sections[section_id]
        lane = lane_section['lanes'][lane_id]

        lane_identification = str(road_id) + '_' + str(section_id) + '_' + str(lane_id)

        if lane['draw_cubic_curve_points'] == False: # 三次曲线点尚未显示，显示之。
            curve_fit_sections = lane['curve_fit_sections']
            for section in curve_fit_sections:
                center_lane_boundary = section
                lane_boundary = None
                adjacent_lane_boundary = None
                
                if lane_id > 0: # 左侧车道
                    lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
                    adjacent_lane_boundary = lane_section['lanes'][lane_id - 1]['boundary_curve_elements']
                elif lane_id < 0: # 右侧车道
                    lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
                    adjacent_lane_boundary = lane_section['lanes'][lane_id + 1]['boundary_curve_elements']

                x_array, y_array = self.prepare_arrays_for_curve_fit(center_lane_boundary, lane_boundary, adjacent_lane_boundary)
                cubic_curve_factors, _ = curve_fit(cubic_curve_function, x_array, y_array)
                lane_section['lanes'][lane_id]['cubic_curve_factors_per_width'].append(cubic_curve_factors)

                self.show_cubic_curve_points(lane_identification, cubic_curve_factors, center_lane_boundary, lane_boundary, adjacent_lane_boundary)   

            lane['draw_cubic_curve_points'] = True
        else: # # 三次曲线点已经显示，隐藏之。
            self.hide_cubic_curve_points(lane_identification)

            lane['draw_cubic_curve_points'] = False

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                self.check_lane_width(road_id, section_id, lane_id)

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
 

