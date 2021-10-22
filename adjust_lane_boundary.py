import bpy

from mathutils import geometry, Vector, Matrix

from .utils import draw_utils
from .utils import math_utils
from .utils import road_utils
from . import helpers
from . import map_scene_data

from . draw_curve_base import DrawCurveBase



class AdjustLaneBoundary(DrawCurveBase):
    bl_idname = 'dsc.adjust_lane_boundary'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        DrawCurveBase.__init__(self)

        self.selected_lane = None # 要修改边界的车道
        self.lane_boundary = None 

        self.lane_start_reference_line = None
        self.lane_end_reference_line = None

        self.start_line_one_side_point = None
        self.start_line_another_side_point = None
        self.end_line_one_side_point = None
        self.end_line_another_side_point = None

        self.projected_point_on_start_line = None
        self.projected_point_on_end_line = None

    def draw_lane_boundary(self):
        '''
        绘制车道边界线，以提示新车道边界线位置。
        '''
        draw_utils.draw_curve('lane_boundary', self.reference_line_elements)

    def remove_lane_boundary(self):
        draw_utils.remove_curve('lane_boundary')

    def draw_end_tangent(self):
        '''
        绘制当前element的end_tangent，供参考。
        '''
        last_element = self.reference_line_elements[len(self.reference_line_elements) - 1]

        line_direction = last_element['end_tangent'].copy()
        line_direction.normalize()
        math_utils.vector_scale_ref(line_direction, 10)

        line_start_point = last_element['end_point'].copy()
        line_end_point = math_utils.vector_add(line_start_point, line_direction)

        draw_utils.draw_dashed_line('adjust_lane_boundary', line_start_point, line_end_point, 0.5, 0.3)

    def remove_end_tangent(self):
        draw_utils.remove_dashed_line('adjust_lane_boundary')

    def finish_adjusting(self):
        self.remove_lane_boundary()
        self.remove_end_tangent()

        draw_utils.remove_dashed_line('lane_start_reference_line')
        draw_utils.remove_dashed_line('lane_end_reference_line')

        draw_utils.remove_point('projected_point_on_start_line')
        draw_utils.remove_point('projected_point_on_end_line')

        if len(self.reference_line_elements) > 1: 
            self.reference_line_elements.pop() # 删除dynamic element。

            name_sections = self.selected_lane.name.split('_')
            last_index = len(name_sections) - 1
            road_id = int(name_sections[last_index - 2])
            section_id = int(name_sections[last_index - 1])
            lane_id = int(name_sections[last_index])

            selected_road = map_scene_data.get_road_data(road_id)
            selected_section = selected_road['lane_sections'][section_id]
            selected_section['lanes'][lane_id]['boundary_curve_elements'] = self.reference_line_elements.copy() # 用新的道路边界构成元素替换原来的。

            # 更新lane在场景中对应的object实物。
            new_lane_mesh = None
            if lane_id == selected_section['left_most_lane_index']:
                new_lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][lane_id]['boundary_curve_elements'], selected_section['lanes'][lane_id - 1]['boundary_curve_elements'])
            elif lane_id == selected_section['right_most_lane_index']:
                new_lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][lane_id + 1]['boundary_curve_elements'], selected_section['lanes'][lane_id]['boundary_curve_elements'])
            helpers.replace_mesh(self.selected_lane, new_lane_mesh)
        
        if self.selected_lane != None:
            self.selected_lane.hide_set(False) # 显示该车道对应的object实物。

    def create_geometries_for_capturing(self, selected_reference_line_section):
        normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
        line_length = 30
        dash_size = 0.5
        gap_size = 0.3

        # 创建边界线初始点以及初始点定位线位置参考。
        draw_utils.draw_point('projected_point_on_start_line', Vector((0, 0, 0)))
        self.projected_point_on_start_line = draw_utils.get_point('projected_point_on_start_line')
        self.projected_point_on_start_line.hide_set(False)

        start_point = selected_reference_line_section[0]['start_point']
        start_tangent = selected_reference_line_section[0]['start_tangent']

        direction = normal_vector_of_xy_plane.cross(start_tangent).normalized()
        self.start_line_one_side_point = math_utils.vector_add(start_point, math_utils.vector_scale(direction, line_length))
        self.start_line_another_side_point = math_utils.vector_add(start_point, math_utils.vector_scale(direction, -line_length))
        draw_utils.draw_dashed_line('lane_start_reference_line', self.start_line_one_side_point, self.start_line_another_side_point, dash_size, gap_size)

        self.lane_start_reference_line = draw_utils.get_dashed_line('lane_start_reference_line')
        self.lane_start_reference_line.hide_set(False)

        # 创建边界线结束点以及结束点定位线位置参考。
        draw_utils.draw_point('projected_point_on_end_line', Vector((0, 0, 0)))
        self.projected_point_on_end_line = draw_utils.get_point('projected_point_on_end_line')
        self.projected_point_on_end_line.hide_set(True)

        last_element_index = len(selected_reference_line_section) - 1
        end_point = selected_reference_line_section[last_element_index]['end_point']
        end_tangent = selected_reference_line_section[last_element_index]['end_tangent']

        direction = normal_vector_of_xy_plane.cross(end_tangent).normalized()
        self.end_line_one_side_point = math_utils.vector_add(end_point, math_utils.vector_scale(direction, line_length))
        self.end_line_another_side_point = math_utils.vector_add(end_point, math_utils.vector_scale(direction, -line_length))
        draw_utils.draw_dashed_line('lane_end_reference_line', self.end_line_one_side_point, self.end_line_another_side_point, dash_size, gap_size)

        self.lane_end_reference_line = draw_utils.get_dashed_line('lane_end_reference_line')
        self.lane_end_reference_line.hide_set(True)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        self.current_selected_point = helpers.mouse_to_xy_plane(context, event)

        if self.selected_lane != None:
            if self.lane_start_reference_line.hide_get() == False:
                line_direction = math_utils.vector_subtract(self.start_line_another_side_point, self.start_line_one_side_point)
                start_line_projected_point = math_utils.project_point_onto_line(self.current_selected_point, self.start_line_one_side_point, line_direction)
                draw_utils.draw_point('projected_point_on_start_line', start_line_projected_point) # 更新投影点位置。
                self.current_selected_point = start_line_projected_point # 捕捉起始点

            if self.lane_end_reference_line.hide_get() == False:
                end_line_projected_point = Vector((0, 0, 0))

                if self.dynamic_element['type'] == 'line':
                    line1_point1 = self.dynamic_element['start_point']
                    line1_point2 = self.dynamic_element['end_point']
                    line2_point1 = self.end_line_one_side_point
                    line2_point2 = self.end_line_another_side_point
                    cross_point = geometry.intersect_line_line(line1_point1, line1_point2, line2_point1, line2_point2)[0]
                    if cross_point != None:
                        end_line_projected_point = cross_point
                elif self.dynamic_element['type'] == 'arc':
                    line_direction = math_utils.vector_subtract(self.end_line_another_side_point, self.end_line_one_side_point)
                    end_line_projected_point = math_utils.project_point_onto_line(self.current_selected_point, self.end_line_one_side_point, line_direction)
                
                draw_utils.draw_point('projected_point_on_end_line', end_line_projected_point) # 更新投影点位置。
                self.current_selected_point = end_line_projected_point # 捕捉结束点

            DrawCurveBase.modal(self, context, event)

        if event.type == 'MOUSEMOVE':
            if len(self.reference_line_elements) > 0:
                self.draw_lane_boundary()
                self.draw_end_tangent()

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.selected_lane != None:
                if self.lane_start_reference_line.hide_get() == False:
                    self.lane_start_reference_line.hide_set(True)
                    self.projected_point_on_start_line.hide_set(True)

                if self.lane_end_reference_line.hide_get() == False:
                    # self.lane_end_reference_line.hide_set(True)
                    # self.projected_point_on_end_line.hide_set(True)

                    self.finish_adjusting()
                    self.clean_up(context)
                    return {'FINISHED'}
            else:
                hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
                if hit:
                    name_sections = raycast_object.name.split('_')
                    last_index = len(name_sections) - 1
                    road_id = int(name_sections[last_index - 2])
                    section_id = int(name_sections[last_index - 1])
                    lane_id = int(name_sections[last_index])

                    selected_road = map_scene_data.get_road_data(road_id)
                    selected_section = selected_road['lane_sections'][section_id]
                    reference_line_sections = selected_road['reference_line_sections']
                    selected_reference_line_section = reference_line_sections[section_id]
                    if lane_id == selected_section['left_most_lane_index'] or lane_id == selected_section['right_most_lane_index']: # 只能对最外侧的车道进行修改边界的操作。
                        self.selected_lane = raycast_object
                        self.selected_lane.hide_set(True) # 隐藏该车道对应的object实物。

                        self.create_geometries_for_capturing(selected_reference_line_section)
                        
            return {'RUNNING_MODAL'}

        elif event.type == 'S' and event.value == 'RELEASE': # S是Start的首字母，表示启动捕捉车道边界线的起始点。
            # if self.selected_lane != None:
            #     if self.lane_start_reference_line.hide_get() == True:
            #         self.lane_start_reference_line.hide_set(False)
            #         self.projected_point_on_start_line.hide_set(False)
            #     else:
            #         self.lane_start_reference_line.hide_set(True)
            #         self.projected_point_on_start_line.hide_set(True)

            return {'RUNNING_MODAL'}

        elif event.type == 'E' and event.value == 'RELEASE': # E是End的首字母，表示启动捕捉车道边界线的结束点。
            if self.selected_lane != None:
                if self.lane_end_reference_line.hide_get() == True:
                    self.lane_end_reference_line.hide_set(False)
                    self.projected_point_on_end_line.hide_set(False)
                else:
                    self.lane_end_reference_line.hide_set(True)
                    self.projected_point_on_end_line.hide_set(True)

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            self.remove_lane_boundary()
            self.remove_end_tangent()

            draw_utils.remove_dashed_line('lane_start_reference_line')
            draw_utils.remove_dashed_line('lane_end_reference_line')

            draw_utils.remove_point('projected_point_on_start_line')
            draw_utils.remove_point('projected_point_on_end_line')

            if len(self.reference_line_elements) > 1: 
                self.reference_line_elements.pop() # 删除dynamic element。

                name_sections = self.selected_lane.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                selected_section = selected_road['lane_sections'][section_id]
                selected_section['lanes'][lane_id]['boundary_curve_elements'] = self.reference_line_elements.copy() # 用新的道路边界构成元素替换原来的。

                # 更新lane在场景中对应的object实物。
                new_lane_mesh = None
                if lane_id == selected_section['left_most_lane_index']:
                    new_lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][lane_id]['boundary_curve_elements'], selected_section['lanes'][lane_id - 1]['boundary_curve_elements'])
                elif lane_id == selected_section['right_most_lane_index']:
                    new_lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][lane_id + 1]['boundary_curve_elements'], selected_section['lanes'][lane_id]['boundary_curve_elements'])
                helpers.replace_mesh(self.selected_lane, new_lane_mesh)
            
            if self.selected_lane != None:
                self.selected_lane.hide_set(False) # 显示该车道对应的object实物。
           
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
 

