import bpy

from math import fabs, dist, acos

from . import math_utils
from . import helpers
from . import utils
from . import road_utils



debug_line_map = {}
debug_dashed_line_map = {}
debug_arc_map = {}
debug_point_map = {}
debug_curve_map = {}



current_context = None

def set_context(context):
    global current_context
    current_context = context

def draw_curve(id, curve):
    vertices = []
    edges = []
    faces = []

    vertices = utils.generate_vertices_from_curve_elements(curve)
    road_utils.remove_duplicated_point(vertices)

    for index in range(0, len(vertices) - 1):
        edges.append((index, index + 1))

    curve_mesh = bpy.data.meshes.new('curve_mesh')
    curve_mesh.from_pydata(vertices, edges, faces)

    if id in debug_curve_map:
        curve_object = debug_curve_map[id]
        helpers.replace_mesh(curve_object, curve_mesh)
    else:
        curve_object = bpy.data.objects.new('curve_object', curve_mesh)
        current_context.scene.collection.objects.link(curve_object)
        debug_curve_map[id] = curve_object

def remove_curve(id):
    if id in debug_curve_map:
        curve = debug_curve_map[id]
        bpy.data.objects.remove(curve, do_unlink=True)
        del debug_curve_map[id]

def draw_arc(id, arc):
    vertices = utils.generate_vertices_from_arc(arc)
    edges = []
    for index in range(0, len(vertices) - 1):
        edges.append((index, index + 1))
    faces = []
    arc_mesh = bpy.data.meshes.new('arc_mesh')
    arc_mesh.from_pydata(vertices, edges, faces)

    if id in debug_arc_map:
        arc_object = debug_arc_map[id]
        helpers.replace_mesh(arc_object, arc_mesh)
    else:
        arc_object = bpy.data.objects.new('arc_object', arc_mesh)
        current_context.scene.collection.objects.link(arc_object)
        debug_arc_map[id] = arc_object

def draw_dashed_line(id, start_point, end_point, dash_size, gap_size):
    '''
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

    if id in debug_dashed_line_map:
        dashed_line_object = debug_dashed_line_map[id]
        helpers.replace_mesh(dashed_line_object, dashed_line_mesh)
    else:
        dashed_line_object = bpy.data.objects.new('dashed_line_object', dashed_line_mesh)
        current_context.scene.collection.objects.link(dashed_line_object)
        debug_dashed_line_map[id] = dashed_line_object

def remove_dashed_line(id):
    if id in debug_dashed_line_map:
        dashed_line = debug_dashed_line_map[id]
        bpy.data.objects.remove(dashed_line, do_unlink=True)
        del debug_dashed_line_map[id]

def draw_line(id, point_a, point_b):
    vertices = [point_a, point_b]
    edges = [(0, 1)]
    faces = []
    line_mesh = bpy.data.meshes.new('line_mesh')
    line_mesh.from_pydata(vertices, edges, faces)

    if id in debug_line_map:
        line_object = debug_line_map[id]
        helpers.replace_mesh(line_object, line_mesh)
    else:
        line_object = bpy.data.objects.new('line_object', line_mesh)
        current_context.scene.collection.objects.link(line_object)
        debug_line_map[id] = line_object

def remove_line(id):
    if id in debug_line_map:
        line = debug_line_map[id]
        bpy.data.objects.remove(line, do_unlink=True)
        del debug_line_map[id]

def draw_point(id, point):
    point_magnitude = 3

    x_forward = point.copy()
    x_forward.x += point_magnitude

    x_backward = point.copy()
    x_backward.x -= point_magnitude

    y_forward = point.copy()
    y_forward.y += point_magnitude

    y_backward = point.copy()
    y_backward.y -= point_magnitude

    vertices = [x_forward, x_backward, y_forward, y_backward]
    edges = [(0, 1), (2, 3)]
    faces = []
    point_mesh = bpy.data.meshes.new('point_mesh')
    point_mesh.from_pydata(vertices, edges, faces)

    point_object = None

    if id in debug_point_map:
        point_object = debug_point_map[id]
        helpers.replace_mesh(point_object, point_mesh)
    else:
        point_object = bpy.data.objects.new('point_object', point_mesh)
        current_context.scene.collection.objects.link(point_object)
        debug_point_map[id] = point_object

    # point_object.rotation_euler[2] += random.randint(0, 360)
