import math
import bpy
import copy


from mathutils import geometry, Vector, Matrix
from math import acos, ceil, pi, radians, dist
from numpy import deg2rad

from . import draw_utils
from . import math_utils
from . import road_utils



def generate_new_curve_by_offset(curve, offset, direction):
    '''
    把curve中的elements朝direction方向偏移offset的距离，产生新的elements。
    '''
    def generate_new_point(origin, tangent):
        normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
        normal_vector = normal_vector_of_xy_plane.cross(tangent).normalized()
        math_utils.vector_scale_ref(normal_vector, offset)

        if direction == 'right':
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

def generate_dotted_curve_from_solid_curve(solid_curve, dash_size, gap_size):
    '''
    solid_curve中的element的空间位置是前后相连的，本函数根据dash_size和gap_size从solid_curve的elements中截取出新的elements，
    这些elements并不保证空间位置前后相连，以实现虚边界线的绘制。
    '''
    dotted_curve = []

    is_generating_dash = True

    copyed_solid_curve = copy.deepcopy(solid_curve) # 为了不改变solid_curve中的数据，产生一个副本。 
    copyed_dash_size = dash_size
    copyed_gap_size = gap_size

    while len(copyed_solid_curve) > 0:
        element = copyed_solid_curve[0] # 每次都从copyed_solid_curve中的第一个element开始截取。

        if is_generating_dash == True: # 截取dash的逻辑。
            element_length = 0
            pre_element = None
            next_element = None

            if element['type'] == 'line': # 当前是在line element上截取。
                element_length = dist(element['start_point'], element['end_point'])
                # 当前元素的长度大于要截取的dash的长度，把当前元素一分为二，其中pre_element的长度和要截取的dash的长度相等。
                if element_length > copyed_dash_size: 
                    split_point = get_point_on_line_by_distance(element, copyed_dash_size)
                    pre_element, next_element = split_line(element, split_point)

            elif element['type'] == 'arc':  # 当前是在arc element上截取。
                center_point, arc_radian, arc_radius = get_arc_geometry_info(element)
                element_length = arc_radian * arc_radius
                if element_length > copyed_dash_size:
                    split_point = get_point_on_arc_by_distance(element, copyed_dash_size)
                    pre_element, next_element = split_arc(element, split_point)

            if element_length > copyed_dash_size: # 当前元素的长度大于要截取的dash的长度，当前元素足够完成dash的截取。
                dotted_curve.append(pre_element) # pre_element即为要截取的element。
                copyed_solid_curve.pop(0) # 从copyed_solid_curve中删除当前element。
                copyed_solid_curve.insert(0, next_element) # 把截取剩下的element插到copyed_solid_curve的前面，成为被截取element。

                is_generating_dash = not is_generating_dash
                copyed_dash_size = dash_size
            else: # 当前元素的长度小于要截取的dash的长度，截取当前element全长，不足dash长度的部分从后面的element中截取。
                dotted_curve.append(element)
                copyed_solid_curve.pop(0)

                copyed_dash_size -= element_length # dash剩余需要截取的长度。
                if copyed_dash_size < 0.001:
                    is_generating_dash = not is_generating_dash
                    copyed_dash_size = dash_size
        else: # 截取gap的逻辑。
            element_length = 0
            pre_element = None
            next_element = None

            if element['type'] == 'line':
                element_length = dist(element['start_point'], element['end_point'])
                if element_length > copyed_gap_size:
                    split_point = get_point_on_line_by_distance(element, copyed_gap_size)
                    pre_element, next_element = split_line(element, split_point)
            elif element['type'] == 'arc':
                center_point, arc_radian, arc_radius = get_arc_geometry_info(element)
                element_length = arc_radian * arc_radius
                if element_length > copyed_gap_size:
                    split_point = get_point_on_arc_by_distance(element, copyed_gap_size)
                    pre_element, next_element = split_arc(element, split_point)

            if element_length > copyed_gap_size:
                copyed_solid_curve.pop(0)
                copyed_solid_curve.insert(0, next_element)

                is_generating_dash = not is_generating_dash
                copyed_gap_size = gap_size
            else:
                copyed_solid_curve.pop(0)

                copyed_gap_size -= element_length
                if copyed_gap_size < 0.001:
                    is_generating_dash = not is_generating_dash
                    copyed_gap_size = gap_size

    return dotted_curve
        
def generate_vertices_from_curve_elements(curve_elements):
    '''
    从elements生成顶点，用于创建mesh。
    '''
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
    '''
    按照一定的弧度角间距在arc上生成顶点（比如每隔1°产生一个顶点）。
    '''
    vertices = []

    center_point, arc_radian, arc_radius = get_arc_geometry_info(arc)
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
    '''
    获取arc的圆心点坐标，弧度值，半径等信息。
    '''
    normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
    infinite_line_multiplier = 10000

    # 计算arc的中心点坐标
    start_point_to_center_vector = arc_element['start_tangent'].cross(normal_vector_of_xy_plane)
    start_point_to_center_vector.normalize()
    math_utils.vector_scale_ref(start_point_to_center_vector, infinite_line_multiplier) 
    start_point_to_center_vector_end_point = math_utils.vector_add(arc_element['start_point'], start_point_to_center_vector)
    end_point_to_center_vector = arc_element['end_tangent'].cross(normal_vector_of_xy_plane)
    end_point_to_center_vector.normalize()
    math_utils.vector_scale_ref(end_point_to_center_vector, infinite_line_multiplier) 
    end_point_to_center_vector_end_point = math_utils.vector_add(arc_element['end_point'], end_point_to_center_vector)

    center_point = geometry.intersect_line_line(arc_element['start_point'], 
                                                start_point_to_center_vector_end_point, 
                                                arc_element['end_point'], 
                                                end_point_to_center_vector_end_point)[0]
    # 计算arc的弧度值
    arc_radian =  acos(start_point_to_center_vector.dot(end_point_to_center_vector) / (start_point_to_center_vector.magnitude * end_point_to_center_vector.magnitude))

    arc_radius = math_utils.vector_subtract(arc_element['start_point'], center_point).magnitude

    return center_point, arc_radian, arc_radius

def computer_arc_end_tangent(start_point, start_tangent, end_point):
    '''
    根据start_point, start_tangent, end_point值计算arc元素的end_tangent值。
    '''
    normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
    center_line_vector = normal_vector_of_xy_plane.cross(end_point - start_point)
    end_tangent = start_tangent.reflect(center_line_vector)

    return end_tangent

def computer_curve_length(curve):
    curve_length = 0

    for element in curve:
        curve_length += get_element_length(element)

    return curve_length

def get_element_length(element):
    if element['type'] == 'line':
        return dist(element['start_point'], element['end_point'])
    elif element['type'] == 'arc':
        center_point, arc_radian, arc_radius = get_arc_geometry_info(element)
        return arc_radian * arc_radius

def get_point_on_line_by_distance(line, distance):
    '''
    获取沿直线distance远处点的position。
    '''
    start_point = line['start_point']
    line_direction = line['start_tangent'].copy()
    line_direction.normalize()
    math_utils.vector_scale_ref(line_direction, distance)

    return math_utils.vector_add(start_point, line_direction)

def get_point_on_arc_by_distance(arc, distance):
    '''
    获取沿弧线distance远处点的position。
    '''
    center_point, arc_radian, arc_radius = get_arc_geometry_info(arc)
    radian = distance / arc_radius

    normal_vector =  arc['start_tangent'].cross(arc['end_tangent'])
    if normal_vector.z < 0:
        radian = -radian

    current_vector = math_utils.vector_subtract(arc['start_point'], center_point)
    current_vector.rotate(Matrix.Rotation(radian, 4, 'Z'))
    current_point = math_utils.vector_add(center_point, current_vector)

    return current_point

def get_tangent_on_arc_by_distance(arc, distance):
    '''
    获取沿弧线distance远处点的tangent。
    '''
    center_point, arc_radian, arc_radius = get_arc_geometry_info(arc)
    radian = distance / arc_radius

    normal_vector =  arc['start_tangent'].cross(arc['end_tangent'])
    if normal_vector.z < 0:
        radian = -radian

    result_tangent = arc['start_tangent'].copy()
    result_tangent.rotate(Matrix.Rotation(radian, 4, 'Z'))

    return result_tangent 

def get_position_and_tangent_on_curve_by_distance(curve, distance):
    for element in curve:
        element_length = get_element_length(element)

        if distance > element_length:
            distance -= element_length
        else:
            if element['type'] == 'line':
                position = get_point_on_line_by_distance(element, distance)
                tangent = element['start_tangent']
                return position, tangent
            elif element['type'] == 'arc': 
                position = get_point_on_arc_by_distance(element, distance)
                tangent = get_tangent_on_arc_by_distance(element, distance)
                return position, tangent

def intersect_line_curve(line_point_a, line_point_b, curve):
    for element in curve:
        if element['type'] == 'line':
            intersected_point = geometry.intersect_line_line(element['start_point'], 
                                                        element['end_point'], 
                                                        line_point_a,
                                                        line_point_b)[0]

            if check_point_on_element(intersected_point, element) == True:
                return intersected_point

        elif element['type'] == 'arc': 
            one_side_point, another_side_point = math_utils.generate_infinite_line(line_point_a, line_point_b)
            center_point, arc_radian, arc_radius = get_arc_geometry_info(element)
            intersected_points = geometry.intersect_line_sphere(one_side_point, another_side_point, center_point, arc_radius)

            for point in intersected_points:
                if point != None and check_point_on_element(point, element) == True:
                    return point
    return None

def check_point_on_element(focal_point, element):
    if dist(focal_point, element['start_point']) < 0.000001 or dist(focal_point, element['end_point']) < 0.000001: # 当投影点和element的端点重合时，认为该投影点在element上。
        return True

    if element['type'] == 'line':
        focal_point_to_line_start_vector = math_utils.vector_subtract(element['start_point'], focal_point)
        focal_point_to_line_end_vector = math_utils.vector_subtract(element['end_point'], focal_point)
        line_start_to_line_end_vector = math_utils.vector_subtract(element['end_point'], element['start_point'])
        # 当投影点坐标在 element['start_point'] 和 element['end_point'] 之间时，返回该投影点坐标；否则投影点无效。
        if focal_point_to_line_start_vector.magnitude < line_start_to_line_end_vector.magnitude and focal_point_to_line_end_vector.magnitude < line_start_to_line_end_vector.magnitude:
            return True
        else:
            return False

    elif element['type'] == 'arc': 
        start_point_to_focal_point_vector = math_utils.vector_subtract(focal_point, element['start_point'])
        end_point_to_focal_point_vector = math_utils.vector_subtract(focal_point, element['end_point'])
        intersection_angle =  acos(start_point_to_focal_point_vector.dot(end_point_to_focal_point_vector) / (start_point_to_focal_point_vector.magnitude * end_point_to_focal_point_vector.magnitude))

        # 当投影点在arc上时，投影点有效；当投影点在arc之外时，投影点无效。
        if intersection_angle > pi / 2:
            return True
        else:
            return False

def split_line(line, split_point):
    '''
    把line element在split_point处一分为二。
    '''
    pre_line = line.copy()
    pre_line['end_point'] = split_point.copy()

    next_line = line.copy()
    next_line['start_point'] = split_point.copy()

    return pre_line, next_line

def split_arc(arc, split_point):
    '''
    把arc element在split_point处一分为二。
    '''
    center_point, arc_radian, arc_radius = get_arc_geometry_info(arc)
    normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
    split_point_to_center_point_vector = math_utils.vector_subtract(center_point, split_point)
    tangent_at_split_point = normal_vector_of_xy_plane.cross(split_point_to_center_point_vector)

    normal_vector =  arc['start_tangent'].cross(arc['end_tangent'])
    if normal_vector.z > 0:
        math_utils.vector_scale_ref(tangent_at_split_point, -1)

    pre_arc = arc.copy()
    pre_arc['end_point'] = split_point.copy()
    pre_arc['end_tangent'] = tangent_at_split_point.copy()

    next_arc = arc.copy()
    next_arc['start_point'] = split_point.copy()
    next_arc['start_tangent'] = tangent_at_split_point.copy()

    return pre_arc, next_arc

def split_reference_line_segment(curve_elements, split_point):
    '''
    把curve_elements在split_point处一分为二。
    '''
    pre_segment = []
    next_segment = []

    projected_point = None

    for element in curve_elements:
        if projected_point != None:
            next_segment.append(element)
            continue

        if element['type'] == 'line':
            projected_point = math_utils.project_point_onto_finite_line(split_point, element['start_point'], element['end_point'])
            if projected_point != None:
                pre_line, next_line = split_line(element, projected_point)
                pre_segment.append(pre_line)
                next_segment.append(next_line)
            else:
                pre_segment.append(element)
        elif element['type'] == 'arc':
            projected_point = math_utils.project_point_onto_finite_arc(split_point, element)
            if projected_point != None:
                pre_arc, next_arc = split_arc(element, projected_point)
                pre_segment.append(pre_arc)
                next_segment.append(next_arc)
            else:
                pre_segment.append(element)

    return projected_point, pre_segment, next_segment

def merge_reference_line_segment(pre_segment, next_segment):
    '''
    把pre_segment和next_segment合并为一个segment，即将pre_segment的最后一个element和next_segment的第一个element合并。
    '''
    result_segment = []

    pre_segment_len = len(pre_segment)
    next_segment_len = len(next_segment)
    pre_last_element = pre_segment[pre_segment_len - 1]
    next_first_element = next_segment[0]

    for index in range(0, pre_segment_len - 1):
        result_segment.append(pre_segment[index])

    merged_element = pre_last_element.copy()
    merged_element['end_point'] = next_first_element['end_point']
    merged_element['end_tangent'] = next_first_element['end_tangent']
    result_segment.append(merged_element)

    for index in range(1, next_segment_len):
        result_segment.append(next_segment[index])

    return result_segment

def get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, target_boundary):
    normal_vector_of_xy_plane = Vector((0.0, 0.0, 1.0))
    position, tangent = get_position_and_tangent_on_curve_by_distance(center_lane_boundary, curve_distance)
    direction = normal_vector_of_xy_plane.cross(tangent).normalized()
    line_point_a = position
    line_point_b = math_utils.vector_add(position, direction)

    return intersect_line_curve(line_point_a, line_point_b, target_boundary)


    

