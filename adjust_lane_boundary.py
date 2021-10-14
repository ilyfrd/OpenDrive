
import bpy

from . import utils
from . import debug_utils
from . import math_utils
from . import helpers
from . import map_scene_data

from . draw_curve_base import DrawCurveBase



class AdjustLaneBoundary(DrawCurveBase):
    bl_idname = 'dsc.adjust_lane_boundary'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        DrawCurveBase.__init__(self)

        self.selected_lane = None
        self.lane_boundary = None 

    def draw_lane_boundary(self):
        debug_utils.draw_debug_curve('lane_boundary', self.reference_line_elements)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("Place object by clicking, hold CTRL to snap to grid, "
            "press RIGHTMOUSE to cancel selection, press ESCAPE to exit.")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if self.selected_lane != None:
            DrawCurveBase.modal(self, context, event)

        if event.type == 'MOUSEMOVE':
            if len(self.reference_line_elements) > 0:
                self.draw_lane_boundary()

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.selected_lane != None:
                return {'RUNNING_MODAL'}

            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                selected_section = selected_road['lane_sections'][section_id]
                if lane_id == selected_section['left_most_lane_index'] or lane_id == selected_section['right_most_lane_index']:
                    self.selected_lane = raycast_object

                    lane_to_object_map = selected_road['lane_to_object_map']
                    lane_object = lane_to_object_map[(section_id, lane_id)]
                    lane_object.hide_set(True)

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            element_number = len(self.reference_line_elements)

            if element_number <= 1:
                return {'RUNNING_MODAL'}
            else:
                debug_utils.remove_debug_curve('lane_boundary')

                self.reference_line_elements.pop()

                name_sections = self.selected_lane.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                selected_section = selected_road['lane_sections'][section_id]
                selected_section['lanes'][lane_id]['boundary_curve_elements'] = self.reference_line_elements.copy()

                lane_to_object_map = selected_road['lane_to_object_map']
                lane_object = lane_to_object_map[(section_id, lane_id)]
                new_lane_mesh = None
                if lane_id == selected_section['left_most_lane_index']:
                    new_lane_mesh = utils.create_band_mesh(selected_section['lanes'][lane_id]['boundary_curve_elements'], selected_section['lanes'][lane_id - 1]['boundary_curve_elements'])
                elif lane_id == selected_section['right_most_lane_index']:
                    new_lane_mesh = utils.create_band_mesh(selected_section['lanes'][lane_id + 1]['boundary_curve_elements'], selected_section['lanes'][lane_id]['boundary_curve_elements'])
                helpers.replace_mesh(lane_object, new_lane_mesh)
                lane_object.hide_set(False)
           
            self.clean_up(context)

            return {'FINISHED'}
            
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
 
