import bpy
import bmesh
from mathutils import Vector, Matrix, geometry
from math import fabs, dist, acos

from . import helpers
from . import utils
from . import math_utils
from . import debug_utils
from . import map_scene_data



class DrawRoad(bpy.types.Operator):
    bl_idname = 'dsc.draw_road'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.road_object = None
        self.road_reference_line_object = None

        self.last_selected_point = None
        self.raycast_point = None
        self.varing_element_was_set = False
        self.reference_line_elements = []
        self.reference_line_segments = []
        self.current_element = {
            'type': 'line',
            'start_point': None,
            'start_tangent': None,
            'end_point': None,
            'end_tangent': None
        }

        self.lane_sections = []

        self.lane_to_object_map = {} # key是(lane_section_index, lane_id)， value是lane_object

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def save_road_data(self):
        road_data = {}
        road_data['reference_line_segments'] = self.reference_line_segments
        road_data['lane_sections'] = self.lane_sections

        map_scene_data.set_road_data(self.road_reference_line_object.name, road_data)

    def create_road_reference_line(self, context):
        left_side_curve = utils.generate_new_curve_by_offset(self.reference_line_elements, 0.1, 'left')
        right_side_curve = utils.generate_new_curve_by_offset(self.reference_line_elements, 0.1, 'right')
        mesh = utils.create_band_mesh(left_side_curve, right_side_curve)
        object_name = 'reference_line_object_' + str(map_scene_data.generate_reference_line_object_id())
        object = bpy.data.objects.new(object_name, mesh)
        object.location[2] += 0.02
        object['type'] = 'road_reference_line'
        object.parent = self.road_object
        context.scene.collection.objects.link(object)

        self.road_reference_line_object = object

    def create_default_road(self, context):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        self.create_default_lane_section()

        self.road_object = bpy.data.objects.new('road_object', None)
        context.scene.collection.objects.link(self.road_object)

        lane_mesh = utils.create_band_mesh(self.lane_sections[0]['lanes'][1], self.lane_sections[0]['lanes'][0])
        lane_object_name = 'lane_object_' + str(map_scene_data.generate_lane_object_id())
        lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
        lane_object['type'] = 'lane'
        lane_object.parent = self.road_object
        context.scene.collection.objects.link(lane_object)

        self.lane_to_object_map[(0, 1)] = lane_object

        lane_mesh = utils.create_band_mesh(self.lane_sections[0]['lanes'][0], self.lane_sections[0]['lanes'][-1])
        lane_object_name = 'lane_object_' + str(map_scene_data.generate_lane_object_id())
        lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
        lane_object['type'] = 'lane'
        lane_object.parent = self.road_object
        context.scene.collection.objects.link(lane_object)

        self.lane_to_object_map[(0, -1)] = lane_object

        helpers.select_activate_object(context, self.road_object)

    def update_default_road(self):
        '''
            默认创建的road是双向双车道。
        '''
        self.update_default_lane_section()

        lane_object = self.lane_to_object_map[(0, 1)]
        lane_mesh = utils.create_band_mesh(self.lane_sections[0]['lanes'][1], self.lane_sections[0]['lanes'][0])
        helpers.replace_mesh(lane_object, lane_mesh)

        lane_object = self.lane_to_object_map[(0, -1)]
        lane_mesh = utils.create_band_mesh(self.lane_sections[0]['lanes'][0], self.lane_sections[0]['lanes'][-1])
        helpers.replace_mesh(lane_object, lane_mesh)

    def remove_default_road(self):
        '''
            Unlink stencil, needs to be in OBJECT mode.
        '''
        bpy.data.objects.remove(self.lane_to_object_map[(0, 1)], do_unlink=True)
        bpy.data.objects.remove(self.lane_to_object_map[(0, -1)], do_unlink=True)
        bpy.data.objects.remove(self.road_object, do_unlink=True)

    def xxxxxxx(self):
        for lane_section in self.lane_sections:
            for lane_id in range(lane_section['left_most_lane_index'], 0, -1):
                utils.create_band_mesh(lane_section['lanes'][lane_id], lane_section['lanes'][lane_id - 1])
            for lane_id in range(lane_section['right_most_lane_index'], 0, 1):
                utils.create_band_mesh(lane_section['lanes'][lane_id + 1], lane_section['lanes'][lane_id])



    def transform_object_wrt_start(self, obj, point_start, heading):
        '''
            Translate and rotate object.
        '''
        mat_translation = Matrix.Translation(point_start)
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        obj.matrix_world = mat_translation @ mat_rotation

    def create_default_lane_section(self):
        default_lane_section = utils.create_lane_section(self.reference_line_elements)
        self.lane_sections.append(default_lane_section)

    def update_default_lane_section(self):
        self.lane_sections[0]['left_most_lane_index'] = 0
        self.lane_sections[0]['right_most_lane_index'] = 0

        del self.lane_sections[0]['lanes'][1]
        del self.lane_sections[0]['lanes'][-1]

        utils.add_lane(self.lane_sections[0], 'left')
        utils.add_lane(self.lane_sections[0], 'right')

    def merge_lane_section(self):
        '''
            Translate and rotate object.
        '''

    def split_lane_section(self):
        '''
            Translate and rotate object.
        '''

    def modal(self, context, event):
        context.workspace.status_text_set("Place object by clicking, hold CTRL to snap to grid, "
            "press RIGHTMOUSE to cancel selection, press ESCAPE to exit.")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

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

            if self.road_object is None:
                self.create_default_road(context)

            self.update_default_road()

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

        elif event.type in {'ESC'}:
            current_element_number = len(self.reference_line_elements)
            if current_element_number <= 1:
                self.remove_default_road()
            else:
                self.reference_line_elements.pop(current_element_number - 1)
                self.update_default_road()

            self.reference_line_segments.append(self.reference_line_elements)
            self.create_road_reference_line(context)
            self.save_road_data()

            self.clean_up(context)

            return {'FINISHED'}
            
        elif event.type in {'LEFT_SHIFT'} and event.value in {'RELEASE'}:
            if self.current_element['type'] == 'line':
                if len(self.reference_line_elements) <= 1:
                    return {'RUNNING_MODAL'} # 第一个元素必须是line，因为如果是arc，则该arc起始点处的切线方向是不确定的。
                self.current_element['type'] = 'arc'
            else:
                self.current_element['type'] = 'line'

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
 


