import bpy
import bmesh
from mathutils import Vector, Matrix, geometry
from math import fabs, dist, acos

from . import helpers
from . import utils
from . import math_utils
from . import debug_utils


class DrawRoad(bpy.types.Operator):
    bl_idname = 'dsc.draw_road'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.road_object = None

        self.last_selected_point = None
        self.raycast_point = None
        self.varing_element_was_set = False
        self.reference_line_elements = []
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

    def create_object(self, context):
        '''
            Create a junction object
        '''
        raise NotImplementedError()

    def create_default_road(self, context):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        self.create_default_lane_section()

        self.road_object = bpy.data.objects.new('road_object', None)
        context.scene.collection.objects.link(self.road_object)

        lane_mesh = self.create_lane_mesh(self.lane_sections[0]['lanes'][1], self.lane_sections[0]['lanes'][0])
        lane_object = bpy.data.objects.new('lane_object', lane_mesh)
        lane_object.parent = self.road_object
        context.scene.collection.objects.link(lane_object)

        self.lane_to_object_map[(0, 1)] = lane_object

        lane_mesh = self.create_lane_mesh(self.lane_sections[0]['lanes'][0], self.lane_sections[0]['lanes'][-1])
        lane_object = bpy.data.objects.new('lane_object', lane_mesh)
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
        lane_mesh = self.create_lane_mesh(self.lane_sections[0]['lanes'][1], self.lane_sections[0]['lanes'][0])
        helpers.replace_mesh(lane_object, lane_mesh)

        lane_object = self.lane_to_object_map[(0, -1)]
        lane_mesh = self.create_lane_mesh(self.lane_sections[0]['lanes'][0], self.lane_sections[0]['lanes'][-1])
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
                self.create_lane_mesh(lane_section['lanes'][lane_id], lane_section['lanes'][lane_id - 1])
            for lane_id in range(lane_section['right_most_lane_index'], 0, 1):
                self.create_lane_mesh(lane_section['lanes'][lane_id + 1], lane_section['lanes'][lane_id])

    def remove_duplicated_point(self, vertices):
        result = []
        result.append(vertices[0])

        for index in range(1, len(vertices)):
            if dist(vertices[index], vertices[index - 1]) > 0.000001:
                result.append(vertices[index])

        return result

    def generate_vertices_from_lane_boundary(self, lane_boundary):
        vertices = []
        for element in lane_boundary:
            if element['type'] == 'line':
                vertices.append(element['start_point'].copy())
                vertices.append(element['end_point'].copy())
            elif element['type'] == 'arc':
                arc_vertices = utils.generate_vertices_from_arc(element)
                vertices.extend(arc_vertices)
        return vertices

    def create_lane_mesh(self, up_boundary, down_boundary):
        vertices = []
        edges = []
        faces = []

        up_boundary_vertices = self.generate_vertices_from_lane_boundary(up_boundary)
        down_boundary_vertices = self.generate_vertices_from_lane_boundary(down_boundary)
        self.remove_duplicated_point(up_boundary_vertices)
        self.remove_duplicated_point(down_boundary_vertices)
        quadrilateral_loop_up_index = 1
        quadrilateral_loop_down_index = 1

        quadrilateral_left_up_point_index = 0
        quadrilateral_left_down_point_index = 1
        quadrilateral_right_down_point_index = 0
        quadrilateral_right_up_point_index = 0

        vertices.append(up_boundary_vertices[0])
        vertices.append(down_boundary_vertices[0])

        max_vertice_index = 1
        while quadrilateral_loop_up_index < len(up_boundary_vertices) and quadrilateral_loop_down_index < len(down_boundary_vertices):
            vertices.append(down_boundary_vertices[quadrilateral_loop_down_index])
            max_vertice_index += 1
            quadrilateral_right_down_point_index = max_vertice_index

            vertices.append(up_boundary_vertices[quadrilateral_loop_up_index])
            max_vertice_index += 1
            quadrilateral_right_up_point_index = max_vertice_index

            edges.append((quadrilateral_left_up_point_index, quadrilateral_left_down_point_index))
            edges.append((quadrilateral_left_down_point_index, quadrilateral_right_down_point_index))
            edges.append((quadrilateral_right_down_point_index, quadrilateral_right_up_point_index))
            edges.append((quadrilateral_right_up_point_index, quadrilateral_left_up_point_index))

            faces.append((quadrilateral_left_up_point_index, 
                          quadrilateral_left_down_point_index, 
                          quadrilateral_right_down_point_index, 
                          quadrilateral_right_up_point_index))
            
            quadrilateral_left_up_point_index = quadrilateral_right_up_point_index
            quadrilateral_left_down_point_index = quadrilateral_right_down_point_index

            quadrilateral_loop_up_index += 1
            quadrilateral_loop_down_index += 1 


        triangle_left_up_point_index = quadrilateral_right_up_point_index
        triangle_left_down_point_index = quadrilateral_right_down_point_index
        triangle_right_point_index = 0

        boundary_has_more_vertices = ''
        triangle_loop_index = 0

        if len(up_boundary_vertices) > quadrilateral_loop_up_index:
            boundary_has_more_vertices = 'up_boundary'
            triangle_loop_index = quadrilateral_loop_up_index
        elif len(down_boundary_vertices) > quadrilateral_loop_down_index:
            boundary_has_more_vertices = 'down_boundary'
            triangle_loop_index = quadrilateral_loop_down_index

        if boundary_has_more_vertices == 'up_boundary':
            while triangle_loop_index < len(up_boundary_vertices):
                vertices.append(up_boundary_vertices[triangle_loop_index])
                max_vertice_index += 1
                triangle_right_point_index = max_vertice_index

                edges.append((triangle_left_up_point_index, triangle_left_down_point_index))
                edges.append((triangle_left_down_point_index, triangle_right_point_index))
                edges.append((triangle_right_point_index, triangle_left_up_point_index))

                faces.append((triangle_left_up_point_index, 
                              triangle_left_down_point_index, 
                              triangle_right_point_index))

                triangle_left_up_point_index = triangle_right_point_index

                triangle_loop_index += 1
        elif boundary_has_more_vertices == 'down_boundary':
                vertices.append(down_boundary_vertices[triangle_loop_index])
                max_vertice_index += 1
                triangle_right_point_index = max_vertice_index

                edges.append((triangle_left_up_point_index, triangle_left_down_point_index))
                edges.append((triangle_left_down_point_index, triangle_right_point_index))
                edges.append((triangle_right_point_index, triangle_left_up_point_index))

                faces.append((triangle_left_up_point_index, 
                              triangle_left_down_point_index, 
                              triangle_right_point_index))

                triangle_left_down_point_index = triangle_right_point_index

                triangle_loop_index += 1

        mesh = bpy.data.meshes.new('lane_mesh')
        mesh.from_pydata(vertices, edges, faces)
        return mesh

    def transform_object_wrt_start(self, obj, point_start, heading):
        '''
            Translate and rotate object.
        '''
        mat_translation = Matrix.Translation(point_start)
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        obj.matrix_world = mat_translation @ mat_rotation

    def create_default_lane_section(self):
        default_lane_section = {
            'lanes': {},
            'left_most_lane_index': 0,
            'right_most_lane_index': 0
        }
        self.lane_sections.append(default_lane_section)

        self.lane_sections[0]['lanes'][0] = self.reference_line_elements #中心车道

        default_lane_width = 3
        self.add_lane(0, 'left', default_lane_width)
        self.add_lane(0, 'right', default_lane_width)

    def update_default_lane_section(self):
        self.lane_sections[0]['left_most_lane_index'] = 0
        self.lane_sections[0]['right_most_lane_index'] = 0

        del self.lane_sections[0]['lanes'][1]
        del self.lane_sections[0]['lanes'][-1]

        default_lane_width = 3
        self.add_lane(0, 'left', default_lane_width)
        self.add_lane(0, 'right', default_lane_width)

    def merge_lane_section(self):
        '''
            Translate and rotate object.
        '''

    def split_lane_section(self):
        '''
            Translate and rotate object.
        '''

    def add_lane(self, lane_section_index, direction, offset):
        direction_factor = 0
        reference_lane_id = 0
        new_lane_id = 0
        if direction == 'left':
            direction_factor = 1
            reference_lane_id = self.lane_sections[lane_section_index]['left_most_lane_index']
            new_lane_id = reference_lane_id + 1
            self.lane_sections[lane_section_index]['left_most_lane_index'] = new_lane_id
        else:
            direction_factor = -1
            reference_lane_id = self.lane_sections[lane_section_index]['right_most_lane_index']
            new_lane_id = reference_lane_id - 1
            self.lane_sections[lane_section_index]['right_most_lane_index'] = new_lane_id

        normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
        reference_lane = self.lane_sections[lane_section_index]['lanes'][reference_lane_id]

        def generate_new_point(origin, tangent):
            normal_vector = normal_vector_of_xy_plane.cross(tangent).normalized()
            math_utils.vector_scale(normal_vector, offset)

            if direction_factor == -1:
                normal_vector.negate()

            new_point = Vector((0.0, 0.0, 0.0))
            new_point[0] = origin[0] + normal_vector[0]
            new_point[1] = origin[1] + normal_vector[1]
            new_point[2] = origin[2] + normal_vector[2]

            return new_point

        new_lane = []
        for element in reference_lane:
            new_element = {}

            if element['type'] == 'line':
                new_element['type'] = 'line'
                new_element['start_point'] = generate_new_point(element['start_point'], element['start_tangent'])

                new_element['start_tangent'] = element['start_tangent']
                new_element['end_point'] = generate_new_point(element['end_point'], element['end_tangent'])

                new_element['end_tangent'] = element['end_tangent']
            elif element['type'] == 'arc':
                new_element['type'] = 'arc'
                new_element['start_point'] = generate_new_point(element['start_point'], element['start_tangent'])

                new_element['start_tangent'] = element['start_tangent']
                new_element['end_point'] = generate_new_point(element['end_point'], element['end_tangent'])

                new_element['end_tangent'] = element['end_tangent']
        
            new_lane.append(new_element)

        self.lane_sections[lane_section_index]['lanes'][new_lane_id] = new_lane

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
                self.current_element['end_tangent'] = self.computer_arc_end_tangent(self.current_element['start_point'],
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
 
    def computer_arc_end_tangent(self, start_point, start_tangent, end_point):
        normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
        center_line_vector = normal_vector_of_xy_plane.cross(end_point - start_point)
        end_tangent = start_tangent.reflect(center_line_vector)

        return end_tangent

