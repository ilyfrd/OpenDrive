import bpy
import random
from mathutils import Vector

from . import helpers
from . import utils


debug_line_map = {}
debug_arc_map = {}
debug_point_map = {}


current_context = None

def set_context(context):
    global current_context
    current_context = context

def draw_debug_arc(id, arc):
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

def draw_debug_line(id, point_a, point_b):
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

def remove_debug_line(id):
    if id in debug_line_map:
        segmenting_line = debug_line_map[id]
        bpy.data.objects.remove(segmenting_line, do_unlink=True)
        del debug_line_map[id]

def draw_debug_point(id, point):
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
