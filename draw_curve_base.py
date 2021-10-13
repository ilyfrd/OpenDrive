
import bpy
import bmesh
from mathutils import Vector, Matrix, geometry
from math import fabs, dist, acos

from . import utils
from . import debug_utils
from . import math_utils
from . import helpers
from . import map_scene_data


class DrawCurveBase(bpy.types.Operator):
    bl_idname = 'dsc.draw_curve_base'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.last_selected_point = None
        self.raycast_point = None
        self.varing_element_was_set = False
        self.reference_line_elements = []
        self.current_element = {
            'type': 'line',
            'start_point': None,
            'start_tangent': None,
            'end_point': None,
            'end_tangent': None
        }

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            self.raycast_point = helpers.mouse_to_xy_plane(context, event)

            if self.last_selected_point is None: # 道路参考线的第一个顶点尚未确定。
                return {'RUNNING_MODAL'} 

            if dist(self.last_selected_point, self.raycast_point) < 0.0001:
                return {'RUNNING_MODAL'} 

            current_element_number = len(self.reference_line_elements)

            if self.current_element['type'] == 'line':
                self.current_element['start_point'] = self.last_selected_point

                if current_element_number < 2:
                    self.current_element['end_point'] = self.raycast_point
                else:
                    pre_element = self.reference_line_elements[current_element_number - 2]
                    self.current_element['end_point'] = math_utils.project_point_onto_line(self.raycast_point, pre_element['end_point'], pre_element['end_tangent'])

                tangent = math_utils.vector_subtract(self.current_element['end_point'], self.current_element['start_point'])
                self.current_element['start_tangent'] = tangent
                self.current_element['end_tangent'] = tangent

            elif self.current_element['type'] == 'arc':
                self.current_element['start_point'] = self.last_selected_point
                self.current_element['end_point'] = self.raycast_point
                self.current_element['start_tangent'] = self.reference_line_elements[current_element_number - 2]['end_tangent']
                self.current_element['end_tangent'] = utils.computer_arc_end_tangent(self.current_element['start_point'],
                                                                                    self.current_element['start_tangent'],
                                                                                    self.current_element['end_point'])

            if self.varing_element_was_set == False:
                self.reference_line_elements.append(self.current_element.copy())
                self.varing_element_was_set = True
            else:
                varing_element = self.reference_line_elements[len(self.reference_line_elements) - 1]
                varing_element['type'] = self.current_element['type']
                varing_element['start_point'] = self.current_element['start_point'].copy()
                varing_element['end_point'] = self.current_element['end_point'].copy()
                varing_element['start_tangent'] = self.current_element['start_tangent'].copy()
                varing_element['end_tangent'] = self.current_element['end_tangent'].copy()

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.last_selected_point is None: # 第一次下点
                self.last_selected_point = self.raycast_point
                return {'RUNNING_MODAL'}

            self.varing_element_was_set = False
            self.last_selected_point = self.current_element['end_point']

            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}:
            current_element_number = len(self.reference_line_elements)
            if current_element_number < 2:
                return {'RUNNING_MODAL'}

            self.last_selected_point = self.reference_line_elements[current_element_number - 2]['start_point']
            self.reference_line_elements.pop()
            self.reference_line_elements.pop()
            self.varing_element_was_set = False

            return {'RUNNING_MODAL'}
            
        elif event.type in {'LEFT_SHIFT'} and event.value in {'RELEASE'}:
            if self.current_element['type'] == 'line':
                if len(self.reference_line_elements) <= 1:
                    return {'RUNNING_MODAL'} # 第一个元素必须是line，因为如果是arc，则该arc起始点处的切线方向是不确定的。
                self.current_element['type'] = 'arc'
            else:
                self.current_element['type'] = 'line'

            return {'RUNNING_MODAL'}


        return {'RUNNING_MODAL'}

    