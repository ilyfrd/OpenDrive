
import bpy

from .utils import draw_utils
from .utils import math_utils
from .utils import basic_element_utils
from . import map_scene_data


class DrawLaneBoundary(bpy.types.Operator):
    bl_idname = 'dsc.draw_lane_boundary'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        ''''''
    def generate_lane_boundary_mesh(self, dotted_curve):
        '''
        dotted_curve中相邻的element在空间中的位置不是相连的，有一定的gap距离，以实现绘制虚边界线的目的。
        '''
        vertices = []
        edges = []
        faces = []

        vertex_index = -1

        left_dotted_curve = basic_element_utils.generate_new_curve_by_offset(dotted_curve, 0.2, 'left')
        right_dotted_curve = basic_element_utils.generate_new_curve_by_offset(dotted_curve, 0.2, 'right')

        for index in range(0, len(dotted_curve)):
            left_element = left_dotted_curve[index]
            right_element = right_dotted_curve[index]

            if left_element['type'] == 'line':
                vertices.append(left_element['start_point'])
                vertices.append(right_element['start_point'])
                vertices.append(right_element['end_point'])
                vertices.append(left_element['end_point'])

                vertex_index += 4
                faces.append((vertex_index-3, vertex_index-2, vertex_index-1, vertex_index))

            elif left_element['type'] == 'arc':
                left_vertices = basic_element_utils.generate_vertices_from_arc(left_element)
                right_vertices = basic_element_utils.generate_vertices_from_arc(right_element)

                left_pre_index = 0
                left_current_index = 0
                right_pre_index = 0
                right_current_index = 0

                vertices.append(left_vertices[0])
                vertex_index += 1
                left_current_index = vertex_index

                vertices.append(right_vertices[0])
                vertex_index += 1
                right_current_index = vertex_index

                arc_vertex_index = 0
                while arc_vertex_index < len(left_vertices): # 遍历从arc element生成的所有点（blender中在edit mode下可以看到arc上生成的点的位置）。
                    vertices.append(left_vertices[arc_vertex_index])
                    left_pre_index = left_current_index
                    vertex_index += 1
                    left_current_index = vertex_index

                    vertices.append(right_vertices[arc_vertex_index])
                    right_pre_index = right_current_index
                    vertex_index += 1
                    right_current_index = vertex_index

                    faces.append((left_pre_index, right_pre_index, right_current_index, left_current_index))

                    arc_vertex_index += 1

        mesh = bpy.data.meshes.new('lane_boundary')
        mesh.from_pydata(vertices, edges, faces)
        return mesh
   
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])
                section_id = int(name_sections[last_index - 1])
                lane_id = int(name_sections[last_index])

                selected_road = map_scene_data.get_road_data(road_id)
                road_object = selected_road['road_object']
                selected_section = selected_road['lane_sections'][section_id]
                lane_boundary_elements = selected_section['lanes'][lane_id]['boundary_curve_elements']

                if selected_section['lanes'][lane_id]['draw_lane_boundary'] == False: # 如果该车道的边界线尚未绘制，则绘制该车道的边界线。
                    dotted_curve = basic_element_utils.generate_dotted_curve_from_solid_curve(lane_boundary_elements, 3, 2)
                    mesh = self.generate_lane_boundary_mesh(dotted_curve)
                    object_name = 'lane_boundary_object_' + str(road_id) + '_' + str(section_id) + '_' + str(lane_id)
                    object = bpy.data.objects.new(object_name, mesh)
                    object.location[2] += 0.05
                    object.parent = road_object
                    context.scene.collection.objects.link(object)

                    selected_section['lanes'][lane_id]['draw_lane_boundary'] = True
                else: # 如果该车道的边界线已经绘制，则删除该车道在场景中对应的边界线object实物。
                    boundary_name = 'lane_boundary_object_' + str(road_id) + '_' + str(section_id) + '_' + str(lane_id)
                    boundary_object = context.scene.objects.get(boundary_name)
                    bpy.data.objects.remove(boundary_object, do_unlink=True)

                    selected_section['lanes'][lane_id]['draw_lane_boundary'] = False

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:

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
 

