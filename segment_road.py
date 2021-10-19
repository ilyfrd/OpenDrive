
import bpy

from .utils import basic_element_utils
from .utils import draw_utils
from .utils import math_utils
from .utils import road_utils
from . import helpers
from . import map_scene_data

'''
通过选中道路参考线确定要进行分段的道路。
'''
class SegmentRoad(bpy.types.Operator):
    bl_idname = 'dsc.segment_road'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.selected_road_id = 0 # 当前选中的road的id。

        self.projected_point = None # 记当前光标位置raycast到xy平面上的点为 raycast_point， projected_point即为raycast_point投影到道路参考线上的点的坐标。
        self.pre_section = None
        self.next_section = None

    def refresh_segmenting(self, context):
        '''
        道路的分段情况发生了变化，根据新的 reference_line_sections 信息，重新生成 lane_sections ，并创建相应的车道object实物。
        '''
        road_data = map_scene_data.get_road_data(self.selected_road_id)
        lane_to_object_map = road_data['lane_to_object_map']
        lane_sections = road_data['lane_sections']
        road_object = road_data['road_object']
        reference_line_sections = road_data['reference_line_sections']

        # 删除当前场景中的车道object实物。
        for object in lane_to_object_map.values():
            bpy.data.objects.remove(object, do_unlink=True)
        lane_to_object_map.clear()

        lane_sections.clear()

        for index in range(0, len(reference_line_sections)):
            lane_section = road_utils.create_lane_section(reference_line_sections[index])
            lane_sections.append(lane_section)

            lane_mesh = road_utils.create_band_mesh(lane_section['lanes'][1]['boundary_curve_elements'], lane_section['lanes'][0]['boundary_curve_elements'])
            lane_object_name = 'lane_object_' + str(self.selected_road_id) + '_' + str(index) + '_' + str(1)
            lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
            lane_object['type'] = 'lane'
            lane_object.parent = road_object
            context.scene.collection.objects.link(lane_object)

            lane_to_object_map[(index, 1)] = lane_object

            lane_mesh = road_utils.create_band_mesh(lane_section['lanes'][0]['boundary_curve_elements'], lane_section['lanes'][-1]['boundary_curve_elements'])
            lane_object_name = 'lane_object_' + str(self.selected_road_id) + '_' + str(index) + '_' + str(-1)
            lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
            lane_object['type'] = 'lane'
            lane_object.parent = road_object
            context.scene.collection.objects.link(lane_object)

            lane_to_object_map[(index, -1)] = lane_object

        helpers.select_activate_object(context, road_object)

    def draw_segmenting_line(self, raycast_point, projected_point):
        '''
        绘制分段线，提示分段位置。
        '''
        projected_point_to_raycast_point_vector = math_utils.vector_subtract(raycast_point, projected_point)
        projected_point_to_raycast_point_vector.normalize()
        math_utils.vector_scale_ref(projected_point_to_raycast_point_vector, 5)
        one_side_point = math_utils.vector_add(projected_point, projected_point_to_raycast_point_vector)
        math_utils.vector_scale_ref(projected_point_to_raycast_point_vector, -1)
        another_side_point = math_utils.vector_add(projected_point, projected_point_to_raycast_point_vector)

        draw_utils.draw_line('segmenting_line', one_side_point, another_side_point)

    def remove_segmenting_line(self):
        draw_utils.remove_line('segmenting_line')

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            if self.selected_road_id != 0:
                raycast_point = helpers.mouse_to_xy_plane(context, event)

                road_data = map_scene_data.get_road_data(self.selected_road_id)
                reference_line_sections = road_data['reference_line_sections']
                last_reference_line_section = reference_line_sections[len(reference_line_sections) - 1] # 道路分段总是对最后一个lane section进行分段。
                # 如果分段成功，projected_point不为None，最后一个lane section被分成 pre_section和 next_section。
                self.projected_point, self.pre_section, self.next_section = basic_element_utils.split_reference_line_segment(last_reference_line_section, raycast_point)

                if self.projected_point != None:
                    self.draw_segmenting_line(raycast_point, self.projected_point)

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.selected_road_id == 0: # 尚未选中road
                hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'road_reference_line')
                if not hit:
                    return {'RUNNING_MODAL'}
                else:
                    helpers.select_activate_object(context, raycast_object) # 高亮显示当前选中的道路参考线。
                    name_sections = raycast_object.name.split('_')
                    self.selected_road_id = int(name_sections[len(name_sections) - 1])
            else: # 已经选中road
                if self.projected_point != None:
                    road_data = map_scene_data.get_road_data(self.selected_road_id)
                    reference_line_sections = road_data['reference_line_sections']
                    # 删除最后一个lane section，并添加分段得到的两个lane sections。
                    reference_line_sections.pop() 
                    reference_line_sections.append(self.pre_section) 
                    reference_line_sections.append(self.next_section)

                    self.refresh_segmenting(context)

            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}: # 回退之前的分段操作。
            road_data = map_scene_data.get_road_data(self.selected_road_id)
            reference_line_sections = road_data['reference_line_sections']
            segments_count = len(reference_line_sections)

            if segments_count >= 2:
                merged_segment = basic_element_utils.merge_reference_line_segment(reference_line_sections[segments_count-2], reference_line_sections[segments_count-1])
                reference_line_sections.pop()
                reference_line_sections.pop()
                reference_line_sections.append(merged_segment)

                self.refresh_segmenting(context)

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            self.remove_segmenting_line()
           
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
 

