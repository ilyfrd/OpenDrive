import bpy

from .utils import draw_utils
from .utils import math_utils
from .utils import road_utils
from . import map_scene_data



class AdjustLaneNumbers(bpy.types.Operator):
    bl_idname = 'dsc.adjust_lane_numbers'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        ''''''

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
            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                selected_section = selected_road['lane_sections'][section_id]
                road_object = selected_road['road_object']
                lane_to_object_map = selected_road['lane_to_object_map']

                if lane_id == selected_section['left_most_lane_index']:
                    road_utils.add_lane(selected_section, 'left')
                    left_most_lane_index = selected_section['left_most_lane_index']
                    lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][left_most_lane_index]['boundary_curve_elements'], selected_section['lanes'][left_most_lane_index - 1]['boundary_curve_elements'])
                    lane_object_name = 'lane_object_' + str(road_id) + '_' + str(section_id) + '_' + str(left_most_lane_index)
                    lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
                    lane_object['type'] = 'lane'
                    lane_object.parent = road_object
                    context.scene.collection.objects.link(lane_object)

                    lane_to_object_map[(section_id, left_most_lane_index)] = lane_object

                elif lane_id == selected_section['right_most_lane_index']:
                    road_utils.add_lane(selected_section, 'right')
                    right_most_lane_index = selected_section['right_most_lane_index']   
                    lane_mesh = road_utils.create_band_mesh(selected_section['lanes'][right_most_lane_index + 1]['boundary_curve_elements'], selected_section['lanes'][right_most_lane_index]['boundary_curve_elements'])
                    lane_object_name = 'lane_object_' + str(road_id) + '_' + str(section_id) + '_' + str(right_most_lane_index)
                    lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
                    lane_object['type'] = 'lane'
                    lane_object.parent = road_object
                    context.scene.collection.objects.link(lane_object)

                    lane_to_object_map[(section_id, right_most_lane_index)] = lane_object

            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}:
            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                selected_section = selected_road['lane_sections'][section_id]
                lane_to_object_map = selected_road['lane_to_object_map']

                if lane_id == selected_section['left_most_lane_index'] or lane_id == selected_section['right_most_lane_index']:
                    road_utils.remove_lane(selected_section, lane_id)
                    bpy.data.objects.remove(raycast_object, do_unlink=True)
                    lane_to_object_map.pop((section_id, lane_id))

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
           
            self.clean_up(context)

            return {'FINISHED'}
            
        elif event.type in {'LEFT_SHIFT'} and event.value in {'RELEASE'}:
           

            return {'RUNNING_MODAL'}
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
 

