
from math import dist, sqrt, pow
from mathutils import Vector, geometry
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
from . import draw_utils
from . import basic_element_utils



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

def intersect_line_sphere_ABANDON(line_a, line_b, sphere_center, sphere_radius): # 太慢，影响交互性。
    projected_point = project_point_onto_line(sphere_center, line_a, line_b)
    distance_between_sphere_center_and_projected_point = dist(sphere_center, projected_point)

    if distance_between_sphere_center_and_projected_point < sphere_radius: # 相交
        distance_between_intersected_point_and_projected_point = sqrt(pow(sphere_radius, 2) - pow(distance_between_sphere_center_and_projected_point, 2))
        line_direction = vector_subtract(line_a, line_b)
        line_direction.normalize()
        intersected_point_a = vector_add(projected_point, vector_scale(line_direction, distance_between_intersected_point_and_projected_point))
        intersected_point_b = vector_add(projected_point, vector_scale(line_direction, -distance_between_intersected_point_and_projected_point))
        return [intersected_point_a, intersected_point_b]
    else:
        return []

def project_point_onto_line(point, line_start_point, line_end_point):
    '''
    把point投影到由line_start_point和line_direction确定的直线上（无限长直线），得到投影点projected_point。
    '''
    projected_point = geometry.intersect_point_line(point, line_start_point, line_end_point)[0]
    return projected_point

def project_point_onto_finite_line(point, line_start_point, line_end_point):
    '''
    把point投影到由 line_start_point 和 line_end_point 确定的直线上（有限长直线），得到投影点projected_point。
    '''
    projected_point = geometry.intersect_point_line(point, line_start_point, line_end_point)[0]
    
    line_element = {
        'type': 'line',
        'start_point': line_start_point,
        'end_point': line_end_point
    }

    if basic_element_utils.check_point_on_element(projected_point, line_element) == True:
        return projected_point
    else:
        return None

def project_point_onto_finite_arc(point, arc):
    '''
    把point投影到arc上，得到投影点projected_point。
    '''
    center_point, arc_radian, arc_radius = basic_element_utils.get_arc_geometry_info(arc)
    one_side_point, another_side_point = generate_infinite_line(point, center_point)
    projected_points = geometry.intersect_line_sphere(one_side_point, another_side_point, center_point, arc_radius)
    for point in projected_points:
        if point != None and basic_element_utils.check_point_on_element(point, arc) == True:
            return point
    
    return None

def generate_infinite_line(line_point_a, line_point_b):
    origin_point = line_point_a
    direction = vector_subtract(line_point_b, line_point_a)
    direction.normalize()
    one_side_point = vector_add(origin_point, vector_scale(direction, 100))
    another_side_point = vector_add(origin_point, vector_scale(direction, -100))

    return one_side_point, another_side_point

def raycast_mouse_to_object(context, event, type):
    '''
    type用于过滤场景中的object实物，即raycast只对 obj['type'] == type 的物体有效。
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