import bpy

from math import fabs, dist, acos

from . import math_utils
from .. import helpers
from .. import map_scene_data
from . import basic_element_utils
from . import road_utils




line_map = {}
dashed_line_map = {}
arc_map = {}
point_map = {}
curve_map = {}

unique_id = 0

current_context = None

def set_context(context):
    global current_context
    current_context = context


def generate_unique_id():
    '''
    生成唯一id。
    '''
    global unique_id
    unique_id += 1
    return unique_id

def draw_curve(id, curve):
    vertices = []
    edges = []
    faces = []

    vertices = basic_element_utils.generate_vertices_from_curve_elements(curve)
    road_utils.remove_duplicated_point(vertices) # 从elements生成的点中，前后相连element的首尾顶点是相同的，这里进行去重处理。

    for index in range(0, len(vertices) - 1):
        edges.append((index, index + 1))

    curve_mesh = bpy.data.meshes.new('curve_mesh')
    curve_mesh.from_pydata(vertices, edges, faces)

    if id in curve_map:
        curve_object = curve_map[id]
        helpers.replace_mesh(curve_object, curve_mesh)
    else:
        curve_object = bpy.data.objects.new('curve_object', curve_mesh)
        current_context.scene.collection.objects.link(curve_object)
        curve_map[id] = curve_object

def remove_curve(id):
    if id in curve_map:
        curve = curve_map[id]
        bpy.data.objects.remove(curve, do_unlink=True)
        del curve_map[id]

def draw_arc(id, arc):
    vertices = basic_element_utils.generate_vertices_from_arc(arc)
    edges = []
    for index in range(0, len(vertices) - 1):
        edges.append((index, index + 1))
    faces = []
    arc_mesh = bpy.data.meshes.new('arc_mesh')
    arc_mesh.from_pydata(vertices, edges, faces)

    if id in arc_map:
        arc_object = arc_map[id]
        helpers.replace_mesh(arc_object, arc_mesh)
    else:
        arc_object = bpy.data.objects.new('arc_object', arc_mesh)
        current_context.scene.collection.objects.link(arc_object)
        arc_map[id] = arc_object

def draw_dashed_line(id, start_point, end_point, dash_size, gap_size):
    '''
    绘制首尾顶点分别为start_point和end_point的虚直线，dash和gap的长度分别为dash_size和gap_size。
    首先绘制gap，然后绘制dash，交替进行。
    '''
    vertices = []
    edges = []
    faces = []

    vertex_index = -1

    line_length = dist(start_point, end_point)

    line_direction = math_utils.vector_subtract(end_point, start_point)
    line_direction.normalize()

    drewLength = 0.0
    drawDash = False
    while drewLength < line_length:
      if drawDash:
        startPoint = math_utils.vector_add(start_point, math_utils.vector_scale(line_direction, drewLength))
        endPoint = math_utils.vector_add(start_point, math_utils.vector_scale(line_direction, drewLength + dash_size))

        vertices.append(startPoint)
        vertices.append(endPoint)
        vertex_index += 2
        edges.append((vertex_index - 1, vertex_index))

        drewLength += dash_size
      else:
        drewLength += gap_size

      drawDash = not drawDash

    dashed_line_mesh = bpy.data.meshes.new('dashed_line_mesh')
    dashed_line_mesh.from_pydata(vertices, edges, faces)

    if id in dashed_line_map:
        dashed_line_object = dashed_line_map[id]
        helpers.replace_mesh(dashed_line_object, dashed_line_mesh)
    else:
        dashed_line_object = bpy.data.objects.new('dashed_line_object', dashed_line_mesh)
        current_context.scene.collection.objects.link(dashed_line_object)
        dashed_line_map[id] = dashed_line_object

def remove_dashed_line(id):
    if id in dashed_line_map:
        dashed_line = dashed_line_map[id]
        bpy.data.objects.remove(dashed_line, do_unlink=True)
        del dashed_line_map[id]

def get_dashed_line(id):
    result = None
    if id in dashed_line_map:
        result = dashed_line_map[id]
    return result

def draw_line(id, point_a, point_b):
    vertices = [point_a, point_b]
    edges = [(0, 1)]
    faces = []
    line_mesh = bpy.data.meshes.new('line_mesh')
    line_mesh.from_pydata(vertices, edges, faces)

    if id in line_map:
        line_object = line_map[id]
        helpers.replace_mesh(line_object, line_mesh)
    else:
        line_object = bpy.data.objects.new('line_object', line_mesh)
        current_context.scene.collection.objects.link(line_object)
        line_map[id] = line_object

def remove_line(id):
    if id in line_map:
        line = line_map[id]
        bpy.data.objects.remove(line, do_unlink=True)
        del line_map[id]

def remove_line_by_feature(feature):
    for key, value in list(line_map.items()):
        if isinstance(key, str) and feature in key:
            bpy.data.objects.remove(value, do_unlink=True)
            line_map.pop(key)

def draw_point(id, point):
    vertices = [point]
    edges = []
    faces = []
    point_mesh = bpy.data.meshes.new('point_mesh')
    point_mesh.from_pydata(vertices, edges, faces)

    point_object = None

    if id in point_map:
        point_object = point_map[id]
        helpers.replace_mesh(point_object, point_mesh)
    else:
        point_object = bpy.data.objects.new('point_object', point_mesh)
        current_context.scene.collection.objects.link(point_object)
        point_map[id] = point_object
    
def remove_point(id):
    if id in point_map:
        point = point_map[id]
        bpy.data.objects.remove(point, do_unlink=True)
        del point_map[id]

def remove_point_by_feature(feature):
    for key, value in list(point_map.items()):
        if isinstance(key, str) and feature in key:
            bpy.data.objects.remove(value, do_unlink=True)
            point_map.pop(key)

def get_point(id):
    result = None
    if id in point_map:
        result = point_map[id]
    return result

def draw_static_segmenting_line_for_curve_fitting(road_id, section_id, lane_id):
    remove_static_segmenting_line_for_curve_fitting(road_id, section_id, lane_id)

    road_data = map_scene_data.get_road_data(road_id)
    lane_sections = road_data['lane_sections']
    lane_section = lane_sections[section_id]
    lane = lane_section['lanes'][lane_id]

    curve_fit_sections = lane['curve_fit_sections']
    for index in range(1, len(curve_fit_sections)):
        curve_fit_section = curve_fit_sections[index]

        if lane_id > 0: # 左侧车道
            lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
            adjacent_lane_boundary = lane_section['lanes'][lane_id - 1]['boundary_curve_elements']
        elif lane_id < 0: # 右侧车道
            lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
            adjacent_lane_boundary = lane_section['lanes'][lane_id + 1]['boundary_curve_elements']

        curve_length = basic_element_utils.computer_curve_length(curve_fit_section)
        intersected_point_on_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(curve_fit_section, 0.001 * curve_length, lane_boundary)
        intersected_point_on_adjacent_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(curve_fit_section, 0.001 * curve_length, adjacent_lane_boundary)
        if intersected_point_on_lane_boundary != None and intersected_point_on_adjacent_lane_boundary != None:
            draw_line('static_segmenting_line_for_curve_fitting_' + str(road_id) + '_' + str(section_id) + '_' + str(lane_id) + '_' + str(generate_unique_id()), 
                intersected_point_on_lane_boundary, 
                intersected_point_on_adjacent_lane_boundary)

def remove_static_segmenting_line_for_curve_fitting(road_id, section_id, lane_id):
    remove_line_by_feature('static_segmenting_line_for_curve_fitting_' + str(road_id) + '_' + str(section_id) + '_' + str(lane_id))