import math
import bpy

from math import acos, ceil, radians, dist
from . import basic_element_utils

def add_lane(lane_section, direction):
    '''
    在lane_section对应的车道段中沿direction方向（left或right）向外侧增加车道。
    '''
    reference_lane_id = 0
    new_lane_id = 0
    if direction == 'left':
        reference_lane_id = lane_section['left_most_lane_index']
        new_lane_id = reference_lane_id + 1
        lane_section['left_most_lane_index'] = new_lane_id
    elif direction == 'right':
        reference_lane_id = lane_section['right_most_lane_index']
        new_lane_id = reference_lane_id - 1
        lane_section['right_most_lane_index'] = new_lane_id

    reference_lane = lane_section['lanes'][reference_lane_id]['boundary_curve_elements']

    new_lane = {
        'boundary_curve_elements': [],
        'lane_boundary_drew': False
    }
    new_lane['boundary_curve_elements'] = basic_element_utils.generate_new_curve_by_offset(reference_lane, 3, direction)

    lane_section['lanes'][new_lane_id] = new_lane

def remove_lane(lane_section, lane_index):
    lane_section['lanes'].pop(lane_index)

    if lane_index > 0:
        lane_section['left_most_lane_index'] -= 1 
    else:
        lane_section['right_most_lane_index'] += 1

def create_lane_section(reference_line_elements):
    default_lane_section = {
        'lanes': {},
        'left_most_lane_index': 0,
        'right_most_lane_index': 0
    }

    center_lane = {
        'boundary_curve_elements': []
    }
    center_lane['boundary_curve_elements'] = reference_line_elements 

    default_lane_section['lanes'][0] = center_lane #中心车道

    add_lane(default_lane_section, 'left')
    add_lane(default_lane_section, 'right')

    return default_lane_section

def remove_duplicated_point(origin_vertices):
    reduced_vertices = []
    reduced_vertices.append(origin_vertices[0])

    for index in range(1, len(origin_vertices)):
        if dist(origin_vertices[index], origin_vertices[index - 1]) > 0.000001:
            reduced_vertices.append(origin_vertices[index])

    origin_vertices = reduced_vertices

def create_band_mesh(up_boundary, down_boundary):
    '''
    创建车道对应的object实物的mesh。
    mesh由四边形和三角形构成，首先创建四边形，直到up_boundary_vertices、down_boundary_vertices中某一边的顶点用完；接着创建三角形，直到另外一边的顶点用完。
    通过vertices组建edge和face的顺序是逆时针。
    '''
    vertices = []
    edges = []
    faces = []

    up_boundary_vertices = basic_element_utils.generate_vertices_from_curve_elements(up_boundary)
    down_boundary_vertices = basic_element_utils.generate_vertices_from_curve_elements(down_boundary)
    remove_duplicated_point(up_boundary_vertices)
    remove_duplicated_point(down_boundary_vertices)

    current_vertice_index = -1

    quadrilateral_loop_up_index = 1
    quadrilateral_loop_down_index = 1

    quadrilateral_left_up_point_index = -1
    quadrilateral_left_down_point_index = -1
    quadrilateral_right_down_point_index = -1
    quadrilateral_right_up_point_index = -1

    vertices.append(up_boundary_vertices[0])
    current_vertice_index += 1
    quadrilateral_left_up_point_index = current_vertice_index

    vertices.append(down_boundary_vertices[0])
    current_vertice_index += 1
    quadrilateral_left_down_point_index = current_vertice_index

    while quadrilateral_loop_up_index < len(up_boundary_vertices) and quadrilateral_loop_down_index < len(down_boundary_vertices):
        vertices.append(down_boundary_vertices[quadrilateral_loop_down_index])
        current_vertice_index += 1
        quadrilateral_right_down_point_index = current_vertice_index

        vertices.append(up_boundary_vertices[quadrilateral_loop_up_index])
        current_vertice_index += 1
        quadrilateral_right_up_point_index = current_vertice_index

        # edges.append((quadrilateral_left_up_point_index, quadrilateral_left_down_point_index))
        # edges.append((quadrilateral_left_down_point_index, quadrilateral_right_down_point_index))
        # edges.append((quadrilateral_right_down_point_index, quadrilateral_right_up_point_index))
        # edges.append((quadrilateral_right_up_point_index, quadrilateral_left_up_point_index))

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
    triangle_right_point_index = -1

    boundary_has_more_vertices = ''
    triangle_loop_index = 0

    if quadrilateral_loop_up_index < len(up_boundary_vertices):
        boundary_has_more_vertices = 'up_boundary'
        triangle_loop_index = quadrilateral_loop_up_index
    elif quadrilateral_loop_down_index < len(down_boundary_vertices):
        boundary_has_more_vertices = 'down_boundary'
        triangle_loop_index = quadrilateral_loop_down_index

    if boundary_has_more_vertices == 'up_boundary':
        while triangle_loop_index < len(up_boundary_vertices):
            vertices.append(up_boundary_vertices[triangle_loop_index])
            current_vertice_index += 1
            triangle_right_point_index = current_vertice_index

            # edges.append((triangle_left_up_point_index, triangle_left_down_point_index))
            # edges.append((triangle_left_down_point_index, triangle_right_point_index))
            # edges.append((triangle_right_point_index, triangle_left_up_point_index))

            faces.append((triangle_left_up_point_index, 
                            triangle_left_down_point_index, 
                            triangle_right_point_index))

            triangle_left_up_point_index = triangle_right_point_index

            triangle_loop_index += 1
    elif boundary_has_more_vertices == 'down_boundary':
        while triangle_loop_index < len(down_boundary_vertices):
            vertices.append(down_boundary_vertices[triangle_loop_index])
            current_vertice_index += 1
            triangle_right_point_index = current_vertice_index

            # edges.append((triangle_left_up_point_index, triangle_left_down_point_index))
            # edges.append((triangle_left_down_point_index, triangle_right_point_index))
            # edges.append((triangle_right_point_index, triangle_left_up_point_index))

            faces.append((triangle_left_up_point_index, 
                            triangle_left_down_point_index, 
                            triangle_right_point_index))

            triangle_left_down_point_index = triangle_right_point_index

            triangle_loop_index += 1

    mesh = bpy.data.meshes.new('lane_mesh')
    mesh.from_pydata(vertices, edges, faces)
    return mesh


        
