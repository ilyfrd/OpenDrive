import bpy
import bmesh
from mathutils import Vector, Matrix, geometry
from math import fabs, dist, acos

from . import helpers
from .utils import basic_element_utils
from .utils import road_utils
from .utils import draw_utils
from . import map_scene_data
from . draw_curve_base import DrawCurveBase



class DrawRoad(DrawCurveBase):
    bl_idname = 'dsc.draw_road'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        DrawCurveBase.__init__(self)

        self.road_object = None
        self.road_id = 0
        self.road_reference_line_object = None

        self.reference_line_segments = []
        self.lane_sections = []
        self.lane_to_object_map = {} # key是(lane_section_index, lane_id)， value是lane_object

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def save_road_data(self):
        road_data = {}
        road_data['reference_line_segments'] = self.reference_line_segments
        road_data['lane_sections'] = self.lane_sections
        road_data['lane_to_object_map'] = self.lane_to_object_map
        road_data['road_object'] = self.road_object

        map_scene_data.set_road_data(self.road_id, road_data)

    def create_road_reference_line(self, context):
        left_side_curve = basic_element_utils.generate_new_curve_by_offset(self.reference_line_elements, 0.1, 'left')
        right_side_curve = basic_element_utils.generate_new_curve_by_offset(self.reference_line_elements, 0.1, 'right')
        mesh = road_utils.create_band_mesh(left_side_curve, right_side_curve)
        object_name = 'reference_line_object_' + str(self.road_id)
        object = bpy.data.objects.new(object_name, mesh)
        object.location[2] += 0.05
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

        self.road_id = map_scene_data.generate_road_id()
        road_object_name = 'road_object_' + str(self.road_id)
        self.road_object = bpy.data.objects.new(road_object_name, None)
        context.scene.collection.objects.link(self.road_object)

        lane_mesh = road_utils.create_band_mesh(self.lane_sections[0]['lanes'][1]['boundary_curve_elements'], self.lane_sections[0]['lanes'][0]['boundary_curve_elements'])
        lane_object_name = 'lane_object_' + str(self.road_id) + '_' + str(0) + '_' + str(1)
        lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
        lane_object['type'] = 'lane'
        lane_object.parent = self.road_object
        context.scene.collection.objects.link(lane_object)

        self.lane_to_object_map[(0, 1)] = lane_object

        lane_mesh = road_utils.create_band_mesh(self.lane_sections[0]['lanes'][0]['boundary_curve_elements'], self.lane_sections[0]['lanes'][-1]['boundary_curve_elements'])
        lane_object_name = 'lane_object_' + str(self.road_id) + '_' + str(0) + '_' + str(-1)
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
        lane_mesh = road_utils.create_band_mesh(self.lane_sections[0]['lanes'][1]['boundary_curve_elements'], self.lane_sections[0]['lanes'][0]['boundary_curve_elements'])
        helpers.replace_mesh(lane_object, lane_mesh)

        lane_object = self.lane_to_object_map[(0, -1)]
        lane_mesh = road_utils.create_band_mesh(self.lane_sections[0]['lanes'][0]['boundary_curve_elements'], self.lane_sections[0]['lanes'][-1]['boundary_curve_elements'])
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
                road_utils.create_band_mesh(lane_section['lanes'][lane_id]['boundary_curve_elements'], lane_section['lanes'][lane_id - 1]['boundary_curve_elements'])
            for lane_id in range(lane_section['right_most_lane_index'], 0, 1):
                road_utils.create_band_mesh(lane_section['lanes'][lane_id + 1]['boundary_curve_elements'], lane_section['lanes'][lane_id]['boundary_curve_elements'])



    def transform_object_wrt_start(self, obj, point_start, heading):
        '''
            Translate and rotate object.
        '''
        mat_translation = Matrix.Translation(point_start)
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        obj.matrix_world = mat_translation @ mat_rotation

    def create_default_lane_section(self):
        default_lane_section = road_utils.create_lane_section(self.reference_line_elements)
        self.lane_sections.append(default_lane_section)

    def update_default_lane_section(self):
        self.lane_sections[0]['left_most_lane_index'] = 0
        self.lane_sections[0]['right_most_lane_index'] = 0

        del self.lane_sections[0]['lanes'][1]['boundary_curve_elements']
        del self.lane_sections[0]['lanes'][-1]['boundary_curve_elements']

        road_utils.add_lane(self.lane_sections[0], 'left')
        road_utils.add_lane(self.lane_sections[0], 'right')

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

        DrawCurveBase.modal(self, context, event)

        if event.type == 'MOUSEMOVE':
            if len(self.reference_line_elements) > 0:
                if self.road_object is None:
                    self.create_default_road(context)

                self.update_default_road()

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            if len(self.reference_line_elements) == 1: # 已经下点，但还没有完成第一个element的绘制
                self.remove_default_road()
            elif len(self.reference_line_elements) > 1:
                self.reference_line_elements.pop()
                self.update_default_road()

                self.reference_line_segments.append(self.reference_line_elements)
                self.create_road_reference_line(context)
                self.save_road_data()

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
 


