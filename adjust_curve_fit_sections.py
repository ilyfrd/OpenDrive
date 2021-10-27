import bpy
import copy

from .utils import draw_utils
from .utils import math_utils
from .utils import road_utils
from .utils import basic_element_utils

from . import helpers
from . import map_scene_data

from . draw_curve_base import DrawCurveBase



class AdjustCurveFitSections(DrawCurveBase):
    bl_idname = 'dsc.adjust_curve_fit_sections'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        DrawCurveBase.__init__(self)

        self.road_id = None
        self.section_id = None
        self.lane_id = None

    def draw_dynamic_segmenting_line_for_curve_fitting(self, raycast_point, projected_point):
        '''
        绘制动态分段线，提示分段位置。
        '''
        road_data = map_scene_data.get_road_data(self.road_id)
        lane_sections = road_data['lane_sections']
        lane_section = lane_sections[self.section_id]

        if self.lane_id > 0: # 左侧车道
            lane_boundary = lane_section['lanes'][self.lane_id]['boundary_curve_elements']
            adjacent_lane_boundary = lane_section['lanes'][self.lane_id - 1]['boundary_curve_elements']
        elif self.lane_id < 0: # 右侧车道
            lane_boundary = lane_section['lanes'][self.lane_id]['boundary_curve_elements']
            adjacent_lane_boundary = lane_section['lanes'][self.lane_id + 1]['boundary_curve_elements']

        intersected_point_on_lane_boundary = basic_element_utils.intersect_line_curve(raycast_point, projected_point, lane_boundary)
        intersected_point_on_adjacent_lane_boundary = basic_element_utils.intersect_line_curve(raycast_point, projected_point, adjacent_lane_boundary)
        draw_utils.draw_line('dynamic_segmenting_line_for_curve_fitting', intersected_point_on_lane_boundary, intersected_point_on_adjacent_lane_boundary)

    def remove_dynamic_segmenting_line_for_curve_fitting(self):
        draw_utils.remove_line('dynamic_segmenting_line_for_curve_fitting')

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        self.current_selected_point = helpers.mouse_to_xy_plane(context, event)

        if self.lane_id != None:
            DrawCurveBase.modal(self, context, event)

        if event.type == 'MOUSEMOVE':
            if self.lane_id != None:
                raycast_point = helpers.mouse_to_xy_plane(context, event)

                road_data = map_scene_data.get_road_data(self.road_id)
                lane_sections = road_data['lane_sections']
                section = lane_sections[self.section_id]
                lane = section['lanes'][self.lane_id]
                curve_fit_sections = lane['curve_fit_sections']
                last_curve_fit_section = curve_fit_sections[len(curve_fit_sections) - 1] # 车道的三次曲线拟合分段总是对最后一个curve fit section进行分段。
                # 如果分段成功，projected_point不为None，最后一个lane section被分成 pre_section和 next_section。
                self.projected_point, self.pre_section, self.next_section = basic_element_utils.split_reference_line_segment(last_curve_fit_section, raycast_point)

                if self.projected_point != None:
                    self.draw_dynamic_segmenting_line_for_curve_fitting(raycast_point, self.projected_point)

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.lane_id == None: # 尚未选中车道
                hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
                if not hit:
                    return {'RUNNING_MODAL'}
                else:
                    name_sections = raycast_object.name.split('_')
                    last_index = len(name_sections) - 1
                    self.road_id = int(name_sections[last_index - 2])
                    self.section_id = int(name_sections[last_index - 1])
                    self.lane_id = int(name_sections[last_index])

                    road_data = map_scene_data.get_road_data(self.road_id)
                    lane_sections = road_data['lane_sections']
                    lane_section = lane_sections[self.section_id]
                    lane = lane_section['lanes'][self.lane_id]
                    
                    center_lane = lane_section['lanes'][0]['boundary_curve_elements']
                    lane['curve_fit_sections'] = [copy.deepcopy(center_lane)] # 清除上次分段的结果。

                    helpers.select_activate_object(context, raycast_object) # 高亮显示当前选中的车道。

            else: # 已经选中车道
                if self.projected_point != None:
                    road_data = map_scene_data.get_road_data(self.road_id)
                    lane_sections = road_data['lane_sections']
                    lane_section = lane_sections[self.section_id]
                    lane = lane_section['lanes'][self.lane_id]
                    curve_fit_sections = lane['curve_fit_sections']
                    # 删除最后一个section，并添加分段得到的两个sections。
                    curve_fit_sections.pop() 
                    curve_fit_sections.append(self.pre_section) 
                    curve_fit_sections.append(self.next_section)

                    draw_utils.draw_static_segmenting_line_for_curve_fitting(self.road_id, self.section_id, self.lane_id)

            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}: # 回退之前的分段操作。
            road_data = map_scene_data.get_road_data(self.road_id)
            lane_sections = road_data['lane_sections']
            section = lane_sections[self.section_id]
            lane = section['lanes'][self.lane_id]
            curve_fit_sections = lane['curve_fit_sections']
            segments_count = len(curve_fit_sections)

            if segments_count >= 2:
                merged_segment = basic_element_utils.merge_reference_line_segment(curve_fit_sections[segments_count-2], curve_fit_sections[segments_count-1])
                curve_fit_sections.pop()
                curve_fit_sections.pop()
                curve_fit_sections.append(merged_segment)

                draw_utils.draw_static_segmenting_line_for_curve_fitting(self.road_id, self.section_id, self.lane_id)

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            if self.lane_id != None:
                self.remove_dynamic_segmenting_line_for_curve_fitting()
                draw_utils.remove_static_segmenting_line_for_curve_fitting(self.road_id, self.section_id, self.lane_id)

            bpy.ops.object.select_all(action='DESELECT')
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
 

