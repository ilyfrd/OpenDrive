
from mathutils import Vector, geometry


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
    vector[0] *= scale_ratio
    vector[1] *= scale_ratio
    vector[2] *= scale_ratio

def project_point_onto_line(point, line_start_point, line_direction):
    line_end_point = vector_add(line_start_point, line_direction)
    projected_point = geometry.intersect_point_line(point, line_start_point, line_end_point)[0]
    return projected_point