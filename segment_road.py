
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
        self.reference_line_selected = False
        self.selected_object_name = ''

        self.split_success = False
        self.pre_segment = None
        self.next_segment = None


    def refresh_segmenting(self):
        '''
        '''

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
            if self.reference_line_selected == False:
                hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'road_reference_line')

                if not hit:
                    return {'RUNNING_MODAL'}
                else:
                    helpers.select_activate_object(context, raycast_object)
                    self.selected_object_name = raycast_object.name
            else:
                raycast_point = helpers.mouse_to_xy_plane(context, event)

                road_data = map_scene_data.get_road_data(self.selected_object_name)
                reference_line_segments = road_data['reference_line_segments']
                current_reference_line_segment = reference_line_segments[len(reference_line_segments) - 1]
                self.split_success, self.pre_segment, self.next_segment = utils.split_reference_line_segment(current_reference_line_segment, raycast_point)

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.selected_object_name != None:
                self.reference_line_selected = True
                return {'RUNNING_MODAL'}

            if self.split_success:
                road_data = map_scene_data.get_road_data(self.selected_object_name)
                reference_line_segments = road_data['reference_line_segments']
                reference_line_segments.pop()
                reference_line_segments.append(self.pre_segment)
                reference_line_segments.append(self.next_segment)

            return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}:
           

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
 

