
import bpy
from math import fabs, dist, acos

from .utils import basic_element_utils
from .utils import math_utils
from . import helpers


class DrawCurveBase(bpy.types.Operator):
    '''
    道路参考线的构成元素是line和arc，元素信息包括type、start_point、start_tangent、end_point、end_tangent。
    道路参考线的第一个元素必须是line，除第一个元素外，其它元素的start_point等于它前面元素的end_point，
    start_tangent等于它前面元素的end_tangent。
    reference_line_elements中的元素由确定元素（数组中除最后一个元素以外的元素）和动态非确定元素（数组中最后一个元素）构成。
    
    '''
    bl_idname = 'dsc.draw_curve_base'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.last_selected_point = None # 上一次点击鼠标左键选择的点。
        self.raycast_point = None # 当前光标所在位置raycast到xy平面得到的点。
        self.varing_element_was_set = False
        self.reference_line_elements = [] # 保存道路参考线的构成元素，即line和arc元素。
        self.current_element = { # current_element是随鼠标位置动态变化的未确定的元素，是reference_line_elements中的最后一个元素。
            'type': 'line', # 元素类型，line或者arc。
            'start_point': None, # 该元素起始点的坐标向量。
            'start_tangent': None, # 该元素起始点处的切向量。
            'end_point': None, # 该元素结束点的坐标向量。
            'end_tangent': None # 该元素结束点处的切向量。
        }

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            self.raycast_point = helpers.mouse_to_xy_plane(context, event)

            if self.last_selected_point is None: # 道路参考线第一个元素的start point尚未确定。
                return {'RUNNING_MODAL'} 

            if dist(self.last_selected_point, self.raycast_point) < 0.0001:
                return {'RUNNING_MODAL'} 

            current_element_number = len(self.reference_line_elements)

            if self.current_element['type'] == 'line': # 当前正在绘制的元素是line。
                self.current_element['start_point'] = self.last_selected_point

                if current_element_number < 2: # reference_line_elements中尚没有确定的元素。
                    self.current_element['end_point'] = self.raycast_point
                else: # reference_line_elements中已经有确定的元素了。
                    pre_element = self.reference_line_elements[current_element_number - 2]
                    self.current_element['end_point'] = math_utils.project_point_onto_line(self.raycast_point, pre_element['end_point'], pre_element['end_tangent'])

                tangent = math_utils.vector_subtract(self.current_element['end_point'], self.current_element['start_point'])
                self.current_element['start_tangent'] = tangent
                self.current_element['end_tangent'] = tangent

            elif self.current_element['type'] == 'arc': # 当前正在绘制的元素是arc。
                self.current_element['start_point'] = self.last_selected_point
                self.current_element['end_point'] = self.raycast_point
                self.current_element['start_tangent'] = self.reference_line_elements[current_element_number - 2]['end_tangent']
                self.current_element['end_tangent'] = basic_element_utils.computer_arc_end_tangent(self.current_element['start_point'],
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

    