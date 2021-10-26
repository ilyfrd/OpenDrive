
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
        self.display_cubic_curve_points = False

    def get_interseted_point_at_curve_distance(self, center_lane_boundary, curve_distance, target_boundary):
        normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
        line_length = 30 # 直线长度需足够长，才能保证与curve相交。
        position, tangent = basic_element_utils.get_position_and_tangent_on_curve_by_distance(center_lane_boundary, curve_distance)
        direction = normal_vector_of_xy_plane.cross(tangent).normalized()
        one_side_point = math_utils.vector_add(position, math_utils.vector_scale(direction, line_length))
        another_side_point = math_utils.vector_add(position, math_utils.vector_scale(direction, -line_length))
        intersected_point_on_target_boundary = basic_element_utils.intersect_line_curve(one_side_point, another_side_point, target_boundary)
        return intersected_point_on_target_boundary

    def prepare_arrays_for_curve_fit(self, center_lane_boundary, lane_boundary, adjacent_lane_boundary):
        x_array = []
        y_array = []

        curve_length = basic_element_utils.computer_curve_length(center_lane_boundary)
        divisions = 20
        sampling_step = curve_length / divisions

        def prepare_array_item(curve_distance):
            intersected_point_on_lane_boundary = self.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, lane_boundary)
            intersected_point_on_adjacent_lane_boundary = self.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, adjacent_lane_boundary)
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

    def show_cubic_curve_points(self, cubic_curve_factors, center_lane_boundary, lane_boundary, adjacent_lane_boundary):
        a, b, c, d = cubic_curve_factors
        curve_length = basic_element_utils.computer_curve_length(center_lane_boundary)
        divisions = 100
        sampling_step = curve_length / divisions
        for index in range(1, divisions):
            curve_distance = sampling_step * index
            intersected_point_on_lane_boundary = self.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, lane_boundary)
            intersected_point_on_adjacent_lane_boundary = self.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, adjacent_lane_boundary)
            direction = math_utils.vector_subtract(intersected_point_on_lane_boundary, intersected_point_on_adjacent_lane_boundary)
            direction.normalize()
            math_utils.vector_scale_ref(direction, cubic_curve_function(curve_distance, a, b, c, d))
            check_point = math_utils.vector_add(intersected_point_on_adjacent_lane_boundary, direction)
            draw_utils.draw_point('cubic_curve_point_' + str(draw_utils.generate_unique_id()), check_point)

    def hide_cubic_curve_points(self):
        draw_utils.remove_point_by_feature('cubic_curve_point_')

    def check_lane_width(self, selected_road):
        if self.display_cubic_curve_points == False: # 当前没有显示三次曲线点
            for lane_section in selected_road['lane_sections']:
                for lane_id in lane_section['lanes']:
                    if lane_id == 0: # 车道号为0的中心车道是没有宽度的，不需要检查。
                        continue

                    center_lane_boundary = lane_section['lanes'][0]['boundary_curve_elements']
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

                    self.show_cubic_curve_points(cubic_curve_factors, center_lane_boundary, lane_boundary, adjacent_lane_boundary)   

            self.display_cubic_curve_points = True   
        else:
            self.hide_cubic_curve_points()
            self.display_cubic_curve_points = False   
 
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
                road_id = int(name_sections[len(name_sections) - 3])
                selected_road = map_scene_data.get_road_data(road_id)
                self.check_lane_width(selected_road)

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
 

