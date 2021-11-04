from math import dist, sqrt
from scipy.optimize import curve_fit

from numpy import power

from . import draw_utils
from . import math_utils
from . import basic_element_utils
from .. import map_scene_data

def cubic_curve_function(x, a, b, c, d):
    return a + b*x + c*power(x,2) + d*power(x,3) # 此处不能用math包里面的pow函数，因为math包里面的pow函数不能接受以数组形式传入的x。
    
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
            draw_utils.draw_line('static_segmenting_line_for_curve_fitting_' + str(road_id) + '_' + str(section_id) + '_' + str(lane_id) + '_' + str(draw_utils.generate_unique_id()), 
                intersected_point_on_lane_boundary, 
                intersected_point_on_adjacent_lane_boundary)

def remove_static_segmenting_line_for_curve_fitting(road_id, section_id, lane_id):
    draw_utils.remove_line_by_feature('static_segmenting_line_for_curve_fitting_' + str(road_id) + '_' + str(section_id) + '_' + str(lane_id))

def prepare_arrays_for_curve_fit(center_lane_boundary, lane_boundary, adjacent_lane_boundary):
    x_array = [] # 保存 s 坐标
    y_array = [] # 保存车道在采样位置的宽度值

    curve_length = basic_element_utils.computer_curve_length(center_lane_boundary)
    divisions = 20 # 沿center_lane_boundary采样20个点
    sampling_step = curve_length / divisions

    def prepare_array_item(curve_distance):
        intersected_point_on_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, lane_boundary)
        intersected_point_on_adjacent_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, adjacent_lane_boundary)
        
        if intersected_point_on_lane_boundary != None and intersected_point_on_adjacent_lane_boundary != None:
            sampled_width = dist(intersected_point_on_lane_boundary, intersected_point_on_adjacent_lane_boundary)
            x_array.append(curve_distance)
            y_array.append(sampled_width)

    curve_distance = 0.001 * curve_length # 从一个非常接近起始点的位置开始采样，避免采样失败。
    prepare_array_item(curve_distance)

    for index in range(1, divisions):
        curve_distance = sampling_step * index
        prepare_array_item(curve_distance)

    curve_distance = 0.999 * curve_length # 从一个非常接近结束点的位置开始采样，避免采样失败。
    prepare_array_item(curve_distance)

    return x_array, y_array

def show_cubic_curve_points(lane_identification, cubic_curve_factors, center_lane_boundary, lane_boundary, adjacent_lane_boundary):
    a, b, c, d = cubic_curve_factors
    curve_length = basic_element_utils.computer_curve_length(center_lane_boundary)
    divisions = 50 # 显示50个拟合结果参考点
    sampling_step = curve_length / divisions
    for index in range(1, divisions):
        curve_distance = sampling_step * index
        intersected_point_on_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, lane_boundary)
        intersected_point_on_adjacent_lane_boundary = basic_element_utils.get_interseted_point_at_curve_distance(center_lane_boundary, curve_distance, adjacent_lane_boundary)
        
        if intersected_point_on_lane_boundary != None and intersected_point_on_adjacent_lane_boundary != None:
            direction = math_utils.vector_subtract(intersected_point_on_lane_boundary, intersected_point_on_adjacent_lane_boundary)
            direction.normalize()
            math_utils.vector_scale_ref(direction, cubic_curve_function(curve_distance, a, b, c, d))
            check_point = math_utils.vector_add(intersected_point_on_adjacent_lane_boundary, direction)
            draw_utils.draw_point('cubic_curve_point_' + lane_identification + '_' + str(draw_utils.generate_unique_id()), check_point)

def hide_cubic_curve_points(lane_identification):
    draw_utils.remove_point_by_feature('cubic_curve_point_' + lane_identification)

def update_cubic_curve_factors(lane_section, lane_id):
    lane = lane_section['lanes'][lane_id]
    lane['cubic_curve_factors_per_width'].clear()
    curve_fit_sections = lane['curve_fit_sections']

    center_lane_boundary = None
    lane_boundary = None
    adjacent_lane_boundary = None

    if lane_id > 0: # 左侧车道
        lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
        adjacent_lane_boundary = lane_section['lanes'][lane_id - 1]['boundary_curve_elements']
    elif lane_id < 0: # 右侧车道
        lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
        adjacent_lane_boundary = lane_section['lanes'][lane_id + 1]['boundary_curve_elements']

    for section in curve_fit_sections:
        center_lane_boundary = section
        x_array, y_array = prepare_arrays_for_curve_fit(center_lane_boundary, lane_boundary, adjacent_lane_boundary)
        cubic_curve_factors, _ = curve_fit(cubic_curve_function, x_array, y_array)
        lane['cubic_curve_factors_per_width'].append(cubic_curve_factors)

def draw_cubic_curve_fitting_result(road_id, section_id, lane_id):
    road_data = map_scene_data.get_road_data(road_id)
    lane_sections = road_data['lane_sections']
    lane_section = lane_sections[section_id]
    lane = lane_section['lanes'][lane_id]

    lane_identification = str(road_id) + '_' + str(section_id) + '_' + str(lane_id)
    hide_cubic_curve_points(lane_identification) # 清除之前绘制的拟合结果参考点。

    center_lane_boundary = None
    lane_boundary = None
    adjacent_lane_boundary = None

    if lane_id > 0: # 左侧车道
        lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
        adjacent_lane_boundary = lane_section['lanes'][lane_id - 1]['boundary_curve_elements']
    elif lane_id < 0: # 右侧车道
        lane_boundary = lane_section['lanes'][lane_id]['boundary_curve_elements']
        adjacent_lane_boundary = lane_section['lanes'][lane_id + 1]['boundary_curve_elements']

    curve_fit_sections = lane['curve_fit_sections']
    for index in range(0, len(curve_fit_sections)):
        center_lane_boundary = curve_fit_sections[index]
        cubic_curve_factors = lane['cubic_curve_factors_per_width'][index]
        show_cubic_curve_points(lane_identification, cubic_curve_factors, center_lane_boundary, lane_boundary, adjacent_lane_boundary)   

def remove_cubic_curve_fitting_result(road_id, section_id, lane_id):
    lane_identification = str(road_id) + '_' + str(section_id) + '_' + str(lane_id)
    hide_cubic_curve_points(lane_identification)


