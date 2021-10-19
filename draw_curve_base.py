
import copy
import bpy
from math import fabs, dist, acos

from .utils import basic_element_utils
from .utils import math_utils
from . import helpers

'''
道路参考线的构成元素是line和arc，元素信息包括type、start_point、start_tangent、end_point、end_tangent。
道路参考线的第一个元素必须是line，除第一个元素外，其它元素的start_point等于它前面元素的end_point，start_tangent等于它前面元素的end_tangent。
reference_line_elements中的元素由static元素（该数组中除最后一个元素以外的元素）和dynamic元素（该数组中最后一个元素）构成。
'''
class DrawCurveBase(bpy.types.Operator):
    bl_idname = 'dsc.draw_curve_base'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.last_selected_point = None # 上一次点击鼠标左键选择的点。
        self.dynamic_element_was_added = False # dynamic元素是否已经加入reference_line_elements。
        self.reference_line_elements = [] # 保存道路参考线的构成元素，即line和arc元素。
        self.dynamic_element = { # dynamic_element 是随鼠标位置动态变化的dynamic元素，是reference_line_elements中的最后一个元素。
            'type': 'line', # 元素类型，line或者arc。
            'start_point': None, # 该元素起始点的坐标向量。
            'start_tangent': None, # 该元素起始点处的切向量。
            'end_point': None, # 该元素结束点的坐标向量。
            'end_tangent': None # 该元素结束点处的切向量。
        }

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            raycast_point = helpers.mouse_to_xy_plane(context, event)

            if self.last_selected_point is None: # 道路参考线第一个元素的start point尚未确定。
                return {'RUNNING_MODAL'} 

            if dist(self.last_selected_point, raycast_point) < 0.0001: # 距离太短可能导致创建mesh失败。
                return {'RUNNING_MODAL'} 

            if self.dynamic_element_was_added == False:
                self.reference_line_elements.append(self.dynamic_element)
                self.dynamic_element_was_added = True

            element_number = len(self.reference_line_elements)

            if self.dynamic_element['type'] == 'line': # 当前正在绘制的元素是line。
                if element_number < 2: # 正在绘制reference_line_elements中的第一个元素。
                    self.dynamic_element['end_point'] = raycast_point
                else: # reference_line_elements中已经有static元素了。
                    pre_element = self.reference_line_elements[element_number - 2]
                    self.dynamic_element['end_point'] = math_utils.project_point_onto_line(raycast_point, pre_element['end_point'], pre_element['end_tangent'])

                tangent = math_utils.vector_subtract(self.dynamic_element['end_point'], self.dynamic_element['start_point'])
                self.dynamic_element['start_tangent'] = tangent.copy()
                self.dynamic_element['end_tangent'] = tangent.copy()

            elif self.dynamic_element['type'] == 'arc': # 当前正在绘制的元素是arc。
                self.dynamic_element['end_point'] = raycast_point
                self.dynamic_element['end_tangent'] = basic_element_utils.computer_arc_end_tangent(self.dynamic_element['start_point'],
                                                                                    self.dynamic_element['start_tangent'],
                                                                                    self.dynamic_element['end_point'])

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.last_selected_point is None: # 第一次下点。
                raycast_point = helpers.mouse_to_xy_plane(context, event)
                self.dynamic_element['start_point'] = raycast_point

                self.last_selected_point = raycast_point

            else: # 后续下点。
                self.reference_line_elements.pop() # 弹出dynamic元素。
                self.reference_line_elements.append(copy.deepcopy(self.dynamic_element)) # 当前dynamic元素转化为static元素。
                self.dynamic_element['start_point'] = self.dynamic_element['end_point'].copy() # 上一个元素的end_point是下一个元素的start_point
                self.dynamic_element['start_tangent'] = self.dynamic_element['end_tangent'].copy() # 上一个元素的 end_tangent 是下一个元素的 start_tangent
                self.dynamic_element_was_added = False
                self.last_selected_point = self.dynamic_element['end_point'].copy()

            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}: # 回退操作。
            element_number = len(self.reference_line_elements)
            if element_number < 2: # 没有可回退的static元素。
                return {'RUNNING_MODAL'}

            element_to_delete = self.reference_line_elements[element_number - 2] # 要回退的static元素。
            self.dynamic_element['start_point'] = element_to_delete['start_point'].copy()
            self.dynamic_element['start_tangent'] = element_to_delete['start_tangent'].copy()
            self.dynamic_element_was_added = False
            self.last_selected_point = element_to_delete['start_point'].copy()

            self.reference_line_elements.pop() # 弹出dynamic元素
            self.reference_line_elements.pop() # 弹出要回退的static元素

            return {'RUNNING_MODAL'}
            
        elif event.type in {'LEFT_SHIFT'} and event.value in {'RELEASE'}: # 切换当前绘制元素的类型。
            if self.dynamic_element['type'] == 'line':
                if len(self.reference_line_elements) <= 1:
                    return {'RUNNING_MODAL'} # 第一个元素必须是line，因为如果是arc，则该arc起始点处的切线方向是不确定的。
                self.dynamic_element['type'] = 'arc'
            else:
                self.dynamic_element['type'] = 'line'

            return {'RUNNING_MODAL'}


        return {'RUNNING_MODAL'}

    