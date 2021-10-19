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


'''
默认创建双向双车道road。
'''
class DrawRoad(DrawCurveBase):
    bl_idname = 'dsc.draw_road'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        DrawCurveBase.__init__(self)

        self.road_object = None # 道路 object，没有实际mesh，用于组织属于该道路的其它object，例如车道 object和道路参考线 object。
        self.road_id = 0 # road id。
        self.road_reference_line_object = None # 道路参考线 object。

        self.reference_line_sections = [] # 通过对道路参考线进行分段实现车道分段功能。
        self.lane_sections = [] # 该road的所有lane section， lane section中保存的是与车道相关的信息，比如车道边界构成元素等，跟车道的object实物表示无关。
        self.lane_to_object_map = {} # key是(lane section index, lane id)， value是lane object，可以通过车道的车道段index和车道id找到该车道在场景中的object实物。

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def save_road_data(self):
        road_data = {}
        road_data['reference_line_sections'] = self.reference_line_sections
        road_data['lane_sections'] = self.lane_sections
        road_data['lane_to_object_map'] = self.lane_to_object_map
        road_data['road_object'] = self.road_object

        map_scene_data.set_road_data(self.road_id, road_data) # 把当前道路信息保存到全局map中。

    def create_road_reference_line(self, context):
        left_side_curve = basic_element_utils.generate_new_curve_by_offset(self.reference_line_elements, 0.1, 'left')
        right_side_curve = basic_element_utils.generate_new_curve_by_offset(self.reference_line_elements, 0.1, 'right')
        mesh = road_utils.create_band_mesh(left_side_curve, right_side_curve)
        object_name = 'reference_line_object_' + str(self.road_id) # 一条道路对应一条道路参考线。
        object = bpy.data.objects.new(object_name, mesh)
        object.location[2] += 0.05
        object['type'] = 'road_reference_line'
        object.parent = self.road_object
        context.scene.collection.objects.link(object)

        self.road_reference_line_object = object

    def create_default_road(self, context):
        self.create_default_lane_section()

        self.road_id = map_scene_data.generate_road_id()
        road_object_name = 'road_object_' + str(self.road_id)
        self.road_object = bpy.data.objects.new(road_object_name, None)
        context.scene.collection.objects.link(self.road_object)

        lane_mesh = road_utils.create_band_mesh(self.lane_sections[0]['lanes'][1]['boundary_curve_elements'], self.lane_sections[0]['lanes'][0]['boundary_curve_elements'])
        # 在lane object的name中包含该lane object所对应的road id，lane section index和lane id信息，以便后续拾取该lane object时知道该lane object所在的road、lane section以及lane。
        lane_object_name = 'lane_object_' + str(self.road_id) + '_' + str(0) + '_' + str(1) 
        lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
        lane_object['type'] = 'lane' # type信息用于raycast时对场景物体进行过滤。
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
        self.update_default_lane_section()

        # 更新1车道在场景中的object实物。
        lane_object = self.lane_to_object_map[(0, 1)]
        lane_mesh = road_utils.create_band_mesh(self.lane_sections[0]['lanes'][1]['boundary_curve_elements'], self.lane_sections[0]['lanes'][0]['boundary_curve_elements'])
        helpers.replace_mesh(lane_object, lane_mesh)

        # 更新-1车道在场景中的object实物。
        lane_object = self.lane_to_object_map[(0, -1)]
        lane_mesh = road_utils.create_band_mesh(self.lane_sections[0]['lanes'][0]['boundary_curve_elements'], self.lane_sections[0]['lanes'][-1]['boundary_curve_elements'])
        helpers.replace_mesh(lane_object, lane_mesh)

    def remove_default_road(self):
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
        '''
        lane object实物是根据lane section中保存的lane的相关信息（例如，boundary_curve_elements）而创建，因此必须先创建lane section。
        '''
        default_lane_section = road_utils.create_lane_section(self.reference_line_elements)
        self.lane_sections.append(default_lane_section)

    def update_default_lane_section(self):
        '''
        reference_line_elements发生了更新， 1车道和-1车道随之更新。
        '''
        self.lane_sections[0]['left_most_lane_index'] = 0
        self.lane_sections[0]['right_most_lane_index'] = 0

        del self.lane_sections[0]['lanes'][1] # 删除当前1车道
        del self.lane_sections[0]['lanes'][-1] # 删除当前-1车道

        road_utils.add_lane(self.lane_sections[0], 'left') # 添加1车道
        road_utils.add_lane(self.lane_sections[0], 'right') # 添加-1车道

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
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
            elements_number = len(self.reference_line_elements)
            if elements_number == 1: # reference_line_elements中只有dynamic element，没有static element，道路创建不成功。
                self.remove_default_road()
            elif elements_number > 1:
                self.reference_line_elements.pop() # 弹出无效的dynamic element。
                self.update_default_road()

                self.reference_line_sections.append(self.reference_line_elements)
                self.create_road_reference_line(context)
                self.save_road_data()

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
 


