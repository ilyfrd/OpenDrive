
import bpy

from . import utils
from . import debug_utils
from . import math_utils
from . import helpers
from . import map_scene_data





class SegmentRoad(bpy.types.Operator):
    bl_idname = 'dsc.segment_road'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.selected_road_id = 0

        self.projected_point = None
        self.pre_segment = None
        self.next_segment = None

    def refresh_segmenting(self, context):
        road_data = map_scene_data.get_road_data(self.selected_road_id)
        lane_to_object_map = road_data['lane_to_object_map']
        lane_sections = road_data['lane_sections']
        road_object = road_data['road_object']
        reference_line_segments = road_data['reference_line_segments']

        for object in lane_to_object_map.values():
            bpy.data.objects.remove(object, do_unlink=True)
        lane_to_object_map.clear()

        lane_sections.clear()

        for index in range(0, len(reference_line_segments)):
            lane_section = utils.create_lane_section(reference_line_segments[index])
            lane_sections.append(lane_section)

            lane_mesh = utils.create_band_mesh(lane_section['lanes'][1]['boundary_curve_elements'], lane_section['lanes'][0]['boundary_curve_elements'])
            lane_object_name = 'lane_object_' + str(self.selected_road_id) + '_' + str(index) + '_' + str(1)
            lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
            lane_object['type'] = 'lane'
            lane_object.parent = road_object
            context.scene.collection.objects.link(lane_object)

            lane_to_object_map[(index, 1)] = lane_object

            lane_mesh = utils.create_band_mesh(lane_section['lanes'][0]['boundary_curve_elements'], lane_section['lanes'][-1]['boundary_curve_elements'])
            lane_object_name = 'lane_object_' + str(self.selected_road_id) + '_' + str(index) + '_' + str(-1)
            lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
            lane_object['type'] = 'lane'
            lane_object.parent = road_object
            context.scene.collection.objects.link(lane_object)

            lane_to_object_map[(index, -1)] = lane_object

        helpers.select_activate_object(context, road_object)

    def draw_segmenting_line(self, raycast_point, projected_point):
        projected_point_to_raycast_point_vector = math_utils.vector_subtract(raycast_point, projected_point)
        projected_point_to_raycast_point_vector.normalize()
        math_utils.vector_scale(projected_point_to_raycast_point_vector, 5)
        one_side_point = math_utils.vector_add(projected_point, projected_point_to_raycast_point_vector)
        math_utils.vector_scale(projected_point_to_raycast_point_vector, -1)
        another_side_point = math_utils.vector_add(projected_point, projected_point_to_raycast_point_vector)

        debug_utils.draw_debug_line('segmenting_line', one_side_point, another_side_point)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("Place object by clicking, hold CTRL to snap to grid, "
            "press RIGHTMOUSE to cancel selection, press ESCAPE to exit.")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            if self.selected_road_id != 0:
                raycast_point = helpers.mouse_to_xy_plane(context, event)

                road_data = map_scene_data.get_road_data(self.selected_road_id)
                reference_line_segments = road_data['reference_line_segments']
                current_reference_line_segment = reference_line_segments[len(reference_line_segments) - 1]
                self.projected_point, self.pre_segment, self.next_segment = utils.split_reference_line_segment(current_reference_line_segment, raycast_point)

                if self.projected_point != None:
                    self.draw_segmenting_line(raycast_point, self.projected_point)

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.selected_road_id == 0: # 尚未选中road
                hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'road_reference_line')
                if not hit:
                    return {'RUNNING_MODAL'}
                else:
                    helpers.select_activate_object(context, raycast_object)
                    name_sections = raycast_object.name.split('_')
                    self.selected_road_id = int(name_sections[len(name_sections) - 1])
            else: # 选中road
                if self.projected_point != None:
                    road_data = map_scene_data.get_road_data(self.selected_road_id)
                    reference_line_segments = road_data['reference_line_segments']
                    reference_line_segments.pop()
                    reference_line_segments.append(self.pre_segment)
                    reference_line_segments.append(self.next_segment)

                    self.refresh_segmenting(context)

            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}:
            road_data = map_scene_data.get_road_data(self.selected_road_id)
            reference_line_segments = road_data['reference_line_segments']
            segments_count = len(reference_line_segments)

            if segments_count >= 2:
                merged_segment = utils.merge_reference_line_segment(reference_line_segments[segments_count-2], reference_line_segments[segments_count-1])
                reference_line_segments.pop()
                reference_line_segments.pop()
                reference_line_segments.append(merged_segment)

                self.refresh_segmenting(context)

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            debug_utils.remove_debug_line('segmenting_line')
           
            self.clean_up(context)

            return {'FINISHED'}
            
        elif event.type in {'LEFT_SHIFT'} and event.value in {'RELEASE'}:

            return {'RUNNING_MODAL'}

        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type in {'MIDDLEMOUSE'}:
            if event.alt:
                bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        debug_utils.set_context(context)

        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        context.workspace.status_text_set(None)

        bpy.context.window.cursor_modal_restore()

        if bpy.context.active_object:
            if bpy.context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
 

