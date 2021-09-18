import bpy
import bmesh
from mathutils import Vector, Matrix

from math import fabs

from . import helpers
from . import utils



class DrawRoad(bpy.types.Operator):
    bl_idname = 'dsc.draw_road'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.mesh_object = None

        self.lastPoint = None
        self.raycast_point = None
        self.reference_line_elements = []
        self.current_element = {
            'type': 'line',
            'startPoint': None,
            'startTangent': None,
            'endPoint': None,
            'endTangent': None
        }

        self.lane_sections = []

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
        mesh = bpy.data.meshes.new("mesh_object")
        vertices, edges, faces = self.get_initial_vertices_edges_faces()
        mesh.from_pydata(vertices, edges, faces)
        self.mesh_object = bpy.data.objects.new("mesh_object", mesh)

        context.scene.collection.objects.link(self.mesh_object)
        helpers.select_activate_object(context, self.mesh_object)

    def update_default_road(self):
        '''
            默认创建的road是双向双车道。
        '''
        self.create_or_update_default_lane_section()

        for lane_section in self.lane_sections:
            for lane_id in range(lane_section['left_most_lane_index'], 0, -1):
                self.create_lane_mesh(lane_section['lanes'][lane_id], lane_section['lanes'][lane_id - 1])
            for lane_id in range(lane_section['right_most_lane_index'], 0, 1):
                self.create_lane_mesh(lane_section['lanes'][lane_id + 1], lane_section['lanes'][lane_id])

        helpers.replace_mesh(self.mesh_object, mesh)
        
    def remove_duplicated_point(self, vertices):
        for index in range(1, vertices.count()):
            if fabs(vertices[index] - vertices[index - 1]) < 0.000001:
                vertices.pop(index)

    def generate_vertices_from_lane_boundary(self, lane_boundary):
        vertices = []
        for element in lane_boundary:
            if element['type'] == 'line':
                vertices.append(element['startPoint'])
                vertices.append(element['endPoint'])
            elif element['type'] == 'arc':
                arc_vertices = utils.generate_vertices_from_arc(element)
                vertices.append(arc_vertices)
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
        while quadrilateral_loop_up_index < up_boundary_vertices.count() and quadrilateral_loop_down_index < down_boundary_vertices.count():
            vertices.append(down_boundary_vertices[quadrilateral_loop_down_index])
            max_vertice_index += 1
            quadrilateral_right_down_point_index = max_vertice_index

            vertices.append(up_boundary_vertices[quadrilateral_loop_up_index])
            max_vertice_index += 1
            quadrilateral_right_up_point_index = max_vertice_index

            edges.append((quadrilateral_left_up_point_index, quadrilateral_left_down_point_index),
                            (quadrilateral_left_down_point_index, quadrilateral_right_down_point_index),
                            (quadrilateral_right_down_point_index, quadrilateral_right_up_point_index),
                            (quadrilateral_right_up_point_index, quadrilateral_left_up_point_index))

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

        if quadrilateral_loop_up_index >= up_boundary_vertices.count():
            boundary_has_more_vertices = 'down_boundary'
            triangle_loop_index = quadrilateral_loop_down_index
        elif quadrilateral_loop_down_index >= down_boundary_vertices.count():
            boundary_has_more_vertices = 'up_boundary'
            triangle_loop_index = quadrilateral_loop_up_index

        if boundary_has_more_vertices == 'up_boundary':
            while triangle_loop_index < up_boundary_vertices.count():
                vertices.append(up_boundary_vertices[triangle_loop_index])
                max_vertice_index += 1
                triangle_right_point_index = max_vertice_index

                edges.append((triangle_left_up_point_index, triangle_left_down_point_index),
                                (triangle_left_down_point_index, triangle_right_point_index),
                                (triangle_right_point_index, triangle_left_up_point_index))

                faces.append((triangle_left_up_point_index, 
                                triangle_left_down_point_index, 
                                triangle_right_point_index))

                triangle_left_up_point_index = triangle_right_point_index

                triangle_loop_index += 1
        elif boundary_has_more_vertices == 'down_boundary':
                vertices.append(down_boundary_vertices[triangle_loop_index])
                max_vertice_index += 1
                triangle_right_point_index = max_vertice_index

                edges.append((triangle_left_up_point_index, triangle_left_down_point_index),
                                (triangle_left_down_point_index, triangle_right_point_index),
                                (triangle_right_point_index, triangle_left_up_point_index))

                faces.append((triangle_left_up_point_index, 
                                triangle_left_down_point_index, 
                                triangle_right_point_index))

                triangle_left_down_point_index = triangle_right_point_index

                triangle_loop_index += 1

        mesh = bpy.data.meshes.new('default_road')
        mesh.from_pydata(vertices, edges, faces)
        return mesh

    def get_initial_vertices_edges_faces(self):
        '''
            Calculate and return the vertices, edges and faces to create the initial stencil mesh.
        '''
        vertices = [(0.0, 0.0, 0.0)]
        edges = []
        faces = []
        return vertices, edges, faces

    def transform_object_wrt_start(self, obj, point_start, heading):
        '''
            Translate and rotate object.
        '''
        mat_translation = Matrix.Translation(point_start)
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        obj.matrix_world = mat_translation @ mat_rotation

    def create_or_update_default_lane_section(self):
        default_lane_width = 3

        if self.lane_sections.count == 0: # 创建默认车道段
            default_lane_section = {
                'lanes': [],
                'left_most_lane_index': 0,
                'right_most_lane_index': 0
            }
            self.lane_sections[0] = default_lane_section

            self.lane_sections[0]['lanes'][0] = self.reference_line_elements #中心车道
            self.add_lane(0, 'left', default_lane_width)
            self.add_lane(0, 'right', default_lane_width)
        else: # 更新默认车道段
            self.lane_sections[0]['left_most_lane_index'] = 0
            self.lane_sections[0]['right_most_lane_index'] = 0

            del self.lane_sections[0]['lanes'][1]
            del self.lane_sections[0]['lanes'][-1]

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

        new_lane = []
        for element in reference_lane:
            new_element = None

            if element['type'] == 'line':
                new_element['type'] = 'line'
                new_element['startPoint'] = element['startPoint'] + direction_factor * offset * normal_vector_of_xy_plane.cross(element['startTangent']).normalize()
                new_element['startTangent'] = element['startTangent']
                new_element['endPoint'] = element['endPoint'] + direction_factor * offset * normal_vector_of_xy_plane.cross(element['endTangent']).normalize()
                new_element['endTangent'] = element['endTangent']
            elif element['type'] == 'arc':
                new_element['type'] = 'arc'
                new_element['startPoint'] = element['startPoint'] + direction_factor * offset * normal_vector_of_xy_plane.cross(element['startTangent']).normalize()
                new_element['startTangent'] = element['startTangent']
                new_element['endPoint'] = element['endPoint'] + direction_factor * offset * normal_vector_of_xy_plane.cross(element['endTangent']).normalize()
                new_element['endTangent'] = element['endTangent']
        
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

            if self.mesh_object is None:
                self.create_default_road(context)

            self.update_default_road()

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.lastPoint is None: #第一次下点。
                if self.current_element['type'] != 'arc': #第一个元素必须是line，因为如果是arc，则该arc起始点处的切线方向是不确定的。
                    self.lastPoint = self.raycast_point
            else:
                self.current_element['startPoint'] = self.lastPoint
                self.current_element['endPoint'] = self.raycast_point
                if self.current_element['type'] == 'line':
                    tangent = self.current_element['endPoint'] - self.current_element['startPoint']
                    self.current_element['startTangent'] = tangent
                    self.current_element['endTangent'] = tangent
                elif self.current_element['type'] == 'arc':
                    self.current_element['startTangent'] = self.reference_line_elements[self.reference_line_elements.count() - 1]['endTangent']
                    self.current_element['endTangent'] = self.computer_arc_end_tangent(
                                                            self.current_element['startPoint'],
                                                            self.current_element['startTangent'],
                                                            self.current_element['endPoint'])

                self.reference_line_elements.append(self.current_element)

            return {'RUNNING_MODAL'}
        # Cancel step by step
        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}:
            # Back to beginning
            if self.state == 'SELECT_END':
                self.remove_stencil()
                self.state = 'INIT'
                return {'RUNNING_MODAL'}
            # Exit
            if self.state == 'SELECT_START':
                self.clean_up(context)
                return {'FINISHED'}
        # Exit immediately
        elif event.type in {'ESC'}:
            self.clean_up(context)
            return {'FINISHED'}
        elif event.type in {'LEFT_SHIFT'}:
            if self.current_element['type'] == 'line':
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
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        # Make sure stencil is removed
        self.remove_stencil()
        # Remove header text with 'None'
        context.workspace.status_text_set(None)
        # Set custom cursor
        bpy.context.window.cursor_modal_restore()
        # Make sure to exit edit mode
        if bpy.context.active_object:
            if bpy.context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
        self.state = 'INIT'

    def computer_arc_end_tangent(self, start_point, start_tangent, end_point):
        normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
        center_line_vector = normal_vector_of_xy_plane.cross(end_point - start_point)
        end_tangent = start_tangent.reflect(center_line_vector)
        
        return end_tangent

