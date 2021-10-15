
from mathutils import Vector, geometry
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
from . import utils



def vector_add(first_vector, second_vector):
    result = Vector((0, 0, 0))
    result[0] = first_vector[0] + second_vector[0]
    result[1] = first_vector[1] + second_vector[1]
    result[2] = first_vector[2] + second_vector[2]
    return result

def vector_subtract(first_vector, second_vector):
    result = Vector((0, 0, 0))
    result[0] = first_vector[0] - second_vector[0]
    result[1] = first_vector[1] - second_vector[1]
    result[2] = first_vector[2] - second_vector[2]
    return result

def vector_scale(vector, scale_ratio):
    result = Vector((0, 0, 0))

    result[0] = vector[0] * scale_ratio
    result[1] = vector[1] * scale_ratio
    result[2] = vector[2] * scale_ratio

    return result

def vector_scale_ref(vector, scale_ratio):
    vector[0] *= scale_ratio
    vector[1] *= scale_ratio
    vector[2] *= scale_ratio

def project_point_onto_line(point, line_start_point, line_direction):
    line_end_point = vector_add(line_start_point, line_direction)
    projected_point = geometry.intersect_point_line(point, line_start_point, line_end_point)[0]
    return projected_point

def project_point_onto_finite_line(point, line_start_point, line_end_point):
    projected_point = geometry.intersect_point_line(point, line_start_point, line_end_point)[0]
    projected_point_to_line_start_vector = vector_subtract(line_start_point, projected_point)
    projected_point_to_line_end_vector = vector_subtract(line_end_point, projected_point)
    line_start_to_line_end_vector = vector_subtract(line_end_point, line_start_point)
    if projected_point_to_line_start_vector.magnitude < line_start_to_line_end_vector.magnitude and projected_point_to_line_end_vector.magnitude < line_start_to_line_end_vector.magnitude:
        return projected_point
    else:
        return None

def project_point_onto_finite_arc(point, arc):
    center_point, arc_radian, arc_radius = utils.get_arc_geometry_info(arc)

    center_to_current_point_vector = vector_subtract(point, center_point)
    center_to_current_point_vector.normalize()
    vector_scale_ref(center_to_current_point_vector, 10000)
    point_for_intersection = vector_add(center_point, center_to_current_point_vector)
    projected_point = geometry.intersect_line_sphere(center_point, point_for_intersection, center_point, arc_radius)[0]

    center_to_intersection_point_vector = vector_subtract(projected_point, center_point)
    center_to_arc_start_vector = vector_subtract(arc['start_point'], center_point)
    center_to_arc_end_vector = vector_subtract(arc['end_point'], center_point)
    one_side_normal = center_to_intersection_point_vector.cross(center_to_arc_start_vector)
    another_side_normal = center_to_intersection_point_vector.cross(center_to_arc_end_vector)
    if one_side_normal.z * another_side_normal.z < 0:
        return projected_point
    else:
        return None

def raycast_mouse_to_object(context, event, type):
    '''
    '''
    region = context.region
    rv3d = context.region_data
    co2d = (event.mouse_region_x, event.mouse_region_y)
    view_vector_mouse = region_2d_to_vector_3d(region, rv3d, co2d)
    ray_origin_mouse = region_2d_to_origin_3d(region, rv3d, co2d)
    hit, point, normal, index_face, obj, matrix_world = context.scene.ray_cast(
        depsgraph=context.view_layer.depsgraph,
        origin=ray_origin_mouse,
        direction=view_vector_mouse)

    if hit and 'type' in obj and obj['type'] == type:
        return True, point, obj
    else:
        return False, point, None