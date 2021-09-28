import math
import bpy

from mathutils import geometry, Vector, Matrix
from math import acos, ceil, radians, dist
from numpy import deg2rad
from . import math_utils
from . import debug_utils

def remove_duplicated_point(origin_vertices):
    reduced_vertices = []
    reduced_vertices.append(origin_vertices[0])

    for index in range(1, len(origin_vertices)):
        if dist(origin_vertices[index], origin_vertices[index - 1]) > 0.000001:
            reduced_vertices.append(origin_vertices[index])

    origin_vertices = reduced_vertices

def create_band_mesh(up_boundary, down_boundary):
    vertices = []
    edges = []
    faces = []

    up_boundary_vertices = generate_vertices_from_curve_elements(up_boundary)
    down_boundary_vertices = generate_vertices_from_curve_elements(down_boundary)
    remove_duplicated_point(up_boundary_vertices)
    remove_duplicated_point(down_boundary_vertices)
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


def generate_new_curve_by_offset(curve, offset, direction):
    def generate_new_point(origin, tangent):
        normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
        normal_vector = normal_vector_of_xy_plane.cross(tangent).normalized()
        math_utils.vector_scale(normal_vector, offset)

        if direction == 'left':
            normal_vector.negate()

        new_point = Vector((0.0, 0.0, 0.0))
        new_point[0] = origin[0] + normal_vector[0]
        new_point[1] = origin[1] + normal_vector[1]
        new_point[2] = origin[2] + normal_vector[2]

        return new_point

    new_curve = []
    for element in curve:
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
    
        new_curve.append(new_element)

    return new_curve

def generate_vertices_from_curve_elements(curve_elements):
    vertices = []
    for element in curve_elements:
        if element['type'] == 'line':
            vertices.append(element['start_point'].copy())
            vertices.append(element['end_point'].copy())
        elif element['type'] == 'arc':
            arc_vertices = generate_vertices_from_arc(element)
            vertices.extend(arc_vertices)
    return vertices

def generate_vertices_from_arc(arc):
    vertices = []

    center_point, arc_radian = get_arc_geometry_info(arc)
    plan_radian_per_division = radians(1)
    divisions = ceil(arc_radian / plan_radian_per_division)
    actual_radian_per_division = arc_radian / divisions

    normal_vector =  arc['start_tangent'].cross(arc['end_tangent'])
    if normal_vector.z < 0:
        actual_radian_per_division = -actual_radian_per_division

    vertices.append(arc['start_point'].copy())

    current_vector = math_utils.vector_subtract(arc['start_point'], center_point)
    for i in range(1, divisions):
        current_vector.rotate(Matrix.Rotation(actual_radian_per_division, 4, 'Z'))
        current_point = math_utils.vector_add(center_point, current_vector)
        vertices.append(current_point)

    vertices.append(arc['end_point'].copy())

    return vertices

def get_arc_geometry_info(arc_element):
    normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
    infinite_line_multiplier = 10000

    # 计算arc的中心点坐标
    start_point_to_center_vector = arc_element['start_tangent'].cross(normal_vector_of_xy_plane)
    math_utils.vector_scale(start_point_to_center_vector, infinite_line_multiplier) 
    start_point_to_center_vector_end_point = math_utils.vector_add(arc_element['start_point'], start_point_to_center_vector)
    end_point_to_center_vector = arc_element['end_tangent'].cross(normal_vector_of_xy_plane)
    math_utils.vector_scale(end_point_to_center_vector, infinite_line_multiplier) 
    end_point_to_center_vector_end_point = math_utils.vector_add(arc_element['end_point'], end_point_to_center_vector)

    center_point = geometry.intersect_line_line(arc_element['start_point'], 
                                                start_point_to_center_vector_end_point, 
                                                arc_element['end_point'], 
                                                end_point_to_center_vector_end_point)[0]
    # 计算arc的弧度值
    arc_radian =  acos(start_point_to_center_vector.dot(end_point_to_center_vector) / (start_point_to_center_vector.magnitude * end_point_to_center_vector.magnitude))

    return center_point, arc_radian

def computer_arc_end_tangent(start_point, start_tangent, end_point):
    normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
    center_line_vector = normal_vector_of_xy_plane.cross(end_point - start_point)
    end_tangent = start_tangent.reflect(center_line_vector)

    return end_tangent

