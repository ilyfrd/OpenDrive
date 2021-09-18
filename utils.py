from mathutils import geometry, Vector, Matrix
from math import acos, ceil
from numpy import deg2rad


def generate_vertices_from_arc(arc):
    vertices = []

    center_point, arc_radian = get_arc_geometry_info(arc)
    plan_radian_per_division = deg2rad(1)
    divisions = ceil(arc_radian / plan_radian_per_division)
    actual_radian_per_division = arc_radian / divisions

    vertices.append(arc['startPoint'])

    center_to_start_point_vector = arc['startPoint'] - center_point
    for i in range(1, divisions):
        current_vector = center_to_start_point_vector.rotate(Matrix.Rotation(actual_radian_per_division * i, 4, 'Z'))
        current_point = center_point + current_vector
        vertices.append(current_point)

    vertices.append(arc['endPoint'])

    return vertices

def get_arc_geometry_info(arc_element):
    normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))

    # 计算arc的中心点坐标
    start_point_to_center_vector = arc_element['startTangent'].cross(normal_vector_of_xy_plane)
    start_point_to_center_vector_end_point = arc_element['startPoint'] + start_point_to_center_vector
    end_point_to_center_vector = arc_element['endTangent'].cross(normal_vector_of_xy_plane)
    end_point_to_center_vector_end_point = arc_element['endPoint'] + end_point_to_center_vector
    center_point = geometry.intersect_line_line(arc_element['startPoint'], 
                                                start_point_to_center_vector_end_point, 
                                                arc_element['endPoint'], 
                                                end_point_to_center_vector_end_point)
    # 计算arc的弧度值
    arc_radian =  acos(start_point_to_center_vector.dot(end_point_to_center_vector) / (start_point_to_center_vector.magnitude * end_point_to_center_vector.magnitude))

    return center_point, arc_radian

