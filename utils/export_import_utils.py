import copy

from scenariogeneration.xodr.opendrive import Road
import bpy
import numpy as np
import json
from scenariogeneration import xodr
import xml.etree.ElementTree as ET
import pathlib
from math import acos, ceil, pi, radians, dist



from mathutils import Vector

from . import basic_element_utils
from . import road_utils
from .. import map_scene_data

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def save_element(src, target):
    target['type'] = src['type']

    target['start_point'] = []
    target['start_point'].append(src['start_point'].x)
    target['start_point'].append(src['start_point'].y)
    target['start_point'].append(src['start_point'].z)

    target['end_point'] = []
    target['end_point'].append(src['end_point'].x)
    target['end_point'].append(src['end_point'].y)
    target['end_point'].append(src['end_point'].z)

    target['start_tangent'] = []
    target['start_tangent'].append(src['start_tangent'].x)
    target['start_tangent'].append(src['start_tangent'].y)
    target['start_tangent'].append(src['start_tangent'].z)

    target['end_tangent'] = []
    target['end_tangent'].append(src['end_tangent'].x)
    target['end_tangent'].append(src['end_tangent'].y)
    target['end_tangent'].append(src['end_tangent'].z)

def read_element(src, target):
    target['type'] = src['type']
    target['start_point'] = Vector((src['start_point'][0], src['start_point'][1], src['start_point'][2]))
    target['end_point'] = Vector((src['end_point'][0], src['end_point'][1], src['end_point'][2]))
    target['start_tangent'] = Vector((src['start_tangent'][0], src['start_tangent'][1], src['start_tangent'][2]))
    target['end_tangent'] = Vector((src['end_tangent'][0], src['end_tangent'][1], src['end_tangent'][2]))

def save_reference_line_sections(reference_line_sections_src, reference_line_sections_target):
    for reference_line_section in reference_line_sections_src:
        reference_line_section_data = []

        for element in reference_line_section:
            element_data = {}
            save_element(element, element_data)
            reference_line_section_data.append(element_data)

        reference_line_sections_target.append(reference_line_section_data)

def read_reference_line_sections(reference_line_sections_src, reference_line_sections_target):
    for reference_line_section in reference_line_sections_src:
        reference_line_section_data = []

        for element in reference_line_section:
            element_data = {}
            read_element(element, element_data)
            reference_line_section_data.append(element_data)

        reference_line_sections_target.append(reference_line_section_data)

def save_lane_sections(lane_sections_src, lane_sections_target):
    def save_boundary_curve_elements(src, target):
        for element in src:
            element_data = {}
            save_element(element, element_data)
            target.append(element_data)

    def save_cubic_curve_factors_per_width(src, target):
        for cubic_curve_factors in src:
            target.append(cubic_curve_factors)

    def save_curve_fit_sections(src, target):
        for curve_fit_section in src:
            curve_fit_section_data = []
            
            for element in curve_fit_section:
                element_data = {}
                save_element(element, element_data)
                curve_fit_section_data.append(element_data)

            target.append(curve_fit_section_data)

    for lane_section in lane_sections_src:
        lane_section_data = {}
        lane_section_data['left_most_lane_index'] = lane_section['left_most_lane_index']
        lane_section_data['right_most_lane_index'] = lane_section['right_most_lane_index']
        lane_section_data['lanes'] = {}


        for lane_id, lane_value in lane_section['lanes'].items():
            lane_data = {}

            lane_data['boundary_curve_elements'] = []
            boundary_curve_elements = lane_value['boundary_curve_elements']
            save_boundary_curve_elements(boundary_curve_elements, lane_data['boundary_curve_elements'])

            lane_data['draw_lane_boundary'] = lane_value['draw_lane_boundary']
            lane_data['draw_segmenting_line_for_curve_fitting'] = lane_value['draw_segmenting_line_for_curve_fitting']
            lane_data['draw_cubic_curve_points'] = lane_value['draw_cubic_curve_points']

            lane_data['cubic_curve_factors_per_width'] = []
            cubic_curve_factors_per_width = lane_value['cubic_curve_factors_per_width']
            save_cubic_curve_factors_per_width(cubic_curve_factors_per_width, lane_data['cubic_curve_factors_per_width'])

            lane_data['curve_fit_sections'] = []
            curve_fit_sections = lane_value['curve_fit_sections']
            save_curve_fit_sections(curve_fit_sections, lane_data['curve_fit_sections'])

            lane_section_data['lanes'][str(lane_id)] = lane_data

        lane_sections_target.append(lane_section_data)

def read_lane_sections(lane_sections_src, lane_sections_target):
    def read_boundary_curve_elements(src, target):
        for element in src:
            element_data = {}
            read_element(element, element_data)
            target.append(element_data)

    def read_cubic_curve_factors_per_width(src, target):
        for cubic_curve_factors in src:
            target.append(cubic_curve_factors)

    def read_curve_fit_sections(src, target):
        for curve_fit_section in src:
            curve_fit_section_data = []
            
            for element in curve_fit_section:
                element_data = {}
                read_element(element, element_data)
                curve_fit_section_data.append(element_data)

            target.append(curve_fit_section_data)

    for lane_section in lane_sections_src:
        lane_section_data = {}
        lane_section_data['left_most_lane_index'] = lane_section['left_most_lane_index']
        lane_section_data['right_most_lane_index'] = lane_section['right_most_lane_index']
        lane_section_data['lanes'] = {}

        for lane_id, lane_value in lane_section['lanes'].items():
            lane_data = {}

            lane_data['boundary_curve_elements'] = []
            boundary_curve_elements = lane_value['boundary_curve_elements']
            read_boundary_curve_elements(boundary_curve_elements, lane_data['boundary_curve_elements'])

            lane_data['draw_lane_boundary'] = lane_value['draw_lane_boundary']
            lane_data['draw_segmenting_line_for_curve_fitting'] = lane_value['draw_segmenting_line_for_curve_fitting']
            lane_data['draw_cubic_curve_points'] = lane_value['draw_cubic_curve_points']

            lane_data['cubic_curve_factors_per_width'] = []
            cubic_curve_factors_per_width = lane_value['cubic_curve_factors_per_width']
            read_cubic_curve_factors_per_width(cubic_curve_factors_per_width, lane_data['cubic_curve_factors_per_width'])

            lane_data['curve_fit_sections'] = []
            curve_fit_sections = lane_value['curve_fit_sections']
            read_curve_fit_sections(curve_fit_sections, lane_data['curve_fit_sections'])

            lane_section_data['lanes'][int(lane_id)] = lane_data

        lane_sections_target.append(lane_section_data)

def save_map_date(file_path):
    map_data = {}

    map = map_scene_data.get_map_data()
    for road_id, road_value in map.items():
        road_data = {}
        road_data['reference_line_sections'] = []
        road_data['lane_sections'] = []

        reference_line_sections = road_value['reference_line_sections']
        save_reference_line_sections(reference_line_sections, road_data['reference_line_sections'])

        lane_sections = road_value['lane_sections']
        save_lane_sections(lane_sections, road_data['lane_sections'])

        map_data[str(road_id)] = road_data
        
    with open(file_path + str('.json'), 'w') as outfile:
        json.dump(map_data, outfile, indent = 4, cls = NumpyEncoder)

def read_map_data(file_path):
    with open(file_path) as json_file:
        file_map_data = json.load(json_file)
        for road_id, road_data in file_map_data.items():
            memory_road_data = {}
            memory_road_data['reference_line_sections'] = []
            memory_road_data['lane_sections'] = []

            reference_line_sections = road_data['reference_line_sections']
            read_reference_line_sections(reference_line_sections, memory_road_data['reference_line_sections'])

            lane_sections = road_data['lane_sections']
            read_lane_sections(lane_sections, memory_road_data['lane_sections'])

            map_scene_data.set_road_data(int(road_id), memory_road_data)

def reload_map_scene(context, file_path):
    for object in bpy.context.scene.objects:
        bpy.data.objects.remove(object, do_unlink=True)

    read_map_data(file_path)
    map_data = map_scene_data.get_map_data()
    for road_id, road_data in map_data.items():
        road_object_name = 'road_object_' + str(road_id)
        road_object = bpy.data.objects.new(road_object_name, None)
        context.scene.collection.objects.link(road_object)
        road_data['road_object'] = road_object

        # 创建车道实物对象
        road_data['lane_to_object_map'] = {}
        lane_sections = road_data['lane_sections']
        for index in range(0, len(lane_sections)):
            lane_section = lane_sections[index]

            def construct_lane_object(up_boundary, down_boundary):
                lane_mesh = road_utils.create_band_mesh(up_boundary, down_boundary)
                lane_object_name = 'lane_object_' + str(road_id) + '_' + str(index) + '_' + str(lane_id) 
                lane_object = bpy.data.objects.new(lane_object_name, lane_mesh)
                lane_object['type'] = 'lane' 
                lane_object.parent = road_object
                context.scene.collection.objects.link(lane_object)

                road_data['lane_to_object_map'][(index, lane_id)] = lane_object

            for lane_id in range(lane_section['left_most_lane_index'], 0, -1):
                construct_lane_object(lane_section['lanes'][lane_id]['boundary_curve_elements'], lane_section['lanes'][lane_id - 1]['boundary_curve_elements'])
            for lane_id in range(lane_section['right_most_lane_index'], 0, 1):
                construct_lane_object(lane_section['lanes'][lane_id + 1]['boundary_curve_elements'], lane_section['lanes'][lane_id]['boundary_curve_elements'])      

        # 创建道路参考线实物对象。
        reference_line_elements = construct_reference_line_elements(copy.deepcopy(road_data['reference_line_sections']))
        left_side_curve = basic_element_utils.generate_new_curve_by_offset(reference_line_elements, 0.1, 'left')
        right_side_curve = basic_element_utils.generate_new_curve_by_offset(reference_line_elements, 0.1, 'right')
        mesh = road_utils.create_band_mesh(left_side_curve, right_side_curve)
        object_name = 'reference_line_object_' + str(road_id) 
        object = bpy.data.objects.new(object_name, mesh)
        object.location[2] += 0.05
        object['type'] = 'road_reference_line'
        object.parent = road_object
        context.scene.collection.objects.link(object)

def export_open_drive_map(file_path):
    odr = xodr.OpenDrive('open_drive_map')

    map_data = map_scene_data.get_map_data()
    for road_id, road_data in map_data.items():
        reference_line_elements = construct_reference_line_elements(copy.deepcopy(road_data['reference_line_sections']))
        first_element = reference_line_elements[0]

        planview = xodr.PlanView()
        planview.set_start_point(first_element['start_point'].x, first_element['start_point'].y, compute_heading_from_tangent(first_element['start_tangent']))

        for element in reference_line_elements:
            if element['type'] == 'line':
                line = xodr.Line(basic_element_utils.get_element_length(element))
                planview.add_geometry(line)
            elif element['type'] == 'arc':
                center_point, arc_radian, arc_radius = basic_element_utils.get_arc_geometry_info(element)

                normal_vector =  element['start_tangent'].cross(element['end_tangent'])
                if normal_vector.z < 0:
                    arc_radius = -arc_radius
                    
                arc = xodr.Arc(curvature = 1 / arc_radius, length = basic_element_utils.get_element_length(element))
                planview.add_geometry(arc)

        planview.adjust_geometries()

        lanes = xodr.Lanes()

        lane_sections = road_data['lane_sections']
        lane_section_s = 0
        for index in range(0, len(lane_sections)):
            lane_section = lane_sections[index]

            centerlane = xodr.Lane(lane_type = xodr.LaneType.median)
            centerlane.add_roadmark(xodr.STD_ROADMARK_SOLID)

            lanesection = xodr.LaneSection(lane_section_s, centerlane)  

            left_lane_num = lane_section['left_most_lane_index']
            while left_lane_num > 0:
                lane = xodr.Lane(xodr.LaneType.driving)
                lane.add_roadmark(xodr.STD_ROADMARK_SOLID)
                lanesection.add_left_lane(lane)
                left_lane_num -= 1

            right_lane_num = -lane_section['right_most_lane_index']
            while right_lane_num > 0:
                lane = xodr.Lane(xodr.LaneType.driving)
                lane.add_roadmark(xodr.STD_ROADMARK_SOLID)
                lanesection.add_right_lane(lane)
                right_lane_num -= 1

            lanes.add_lanesection(lanesection)

            lane_section_s += basic_element_utils.computer_curve_length(lane_section['lanes'][0]['boundary_curve_elements'])

        road = xodr.Road(road_id, planview, lanes, name = str(road_id)) # name不能缺失，否则我们的高精度地图使用端的API无法正常读取地图数据。
        odr.add_road(road)

    adjust_xodr_file_data(odr, file_path)

def adjust_xodr_file_data(odr, file_path):
    open_drive_element = odr.get_element()

    road_elements =  open_drive_element.findall('road')
    for road_element in road_elements:
        road_id = int(road_element.get('id'))
        lanes_element = road_element.find('lanes')
        lane_section_elements = lanes_element.findall('laneSection')
        for section_id in range(0, len(lane_section_elements)):
            lane_section_element = lane_section_elements[section_id]

            left_element = lane_section_element.find('left')
            add_lane_width_routine(left_element, road_id, section_id)

            right_element = lane_section_element.find('right')
            add_lane_width_routine(right_element, road_id, section_id)

    open_drive_element_tree = ET.ElementTree(open_drive_element)
    ET.indent(open_drive_element_tree, space = '    ')
    open_drive_element_tree.write(file_path + str('.xodr'))

def add_lane_width_routine(lane_element_parent, road_id, section_id):
    lane_elements = lane_element_parent.findall('lane')
    for lane_element in lane_elements:
        lane_id = int(lane_element.get('id'))
        road_data = map_scene_data.get_road_data(road_id)
        lane_section = road_data['lane_sections'][section_id]
        add_lane_width_per_lane(lane_element, lane_section, lane_id)

def add_lane_width_per_lane(lane_element, lane_section, lane_id):
    width_elements = lane_element.findall('width')
    for width_element in width_elements:
        lane_element.remove(width_element)

    soffset = 0
    cubic_curve_factors_per_width = lane_section['lanes'][lane_id]['cubic_curve_factors_per_width']
    curve_fit_sections = lane_section['lanes'][lane_id]['curve_fit_sections']
    for index in range(0, len(cubic_curve_factors_per_width)):
        a, b, c, d = cubic_curve_factors_per_width[index]
        polynomialdict = {}
        polynomialdict['a'] = str(a)
        polynomialdict['b'] = str(b)
        polynomialdict['c'] = str(c)
        polynomialdict['d'] = str(d)
        polynomialdict['sOffset'] = str(soffset) 
        ET.SubElement(lane_element,'width', attrib=polynomialdict)  

        soffset += basic_element_utils.computer_curve_length(curve_fit_sections[index])  

def construct_reference_line_elements(reference_line_sections):
    while len(reference_line_sections) > 1:
        last_index = len(reference_line_sections) - 1
        result_segment = basic_element_utils.merge_reference_line_segment(reference_line_sections[last_index - 1], reference_line_sections[last_index])
        reference_line_sections.pop()
        reference_line_sections.pop()
        reference_line_sections.append(result_segment)

    return reference_line_sections[0]

def compute_heading_from_tangent(tangent):
    '''
    heading的值是tangent和x轴的夹角。
    '''
    heading = 0

    x_coordinate = Vector((1, 0, 0))
    tangent = tangent.normalized()

    if tangent.x - (-1) < 0.000001 : # 防止acos函数溢出。
        heading = pi
    else:
        heading = acos(x_coordinate.dot(tangent) / (x_coordinate.magnitude * tangent.magnitude))
        if tangent.y < 0:
            heading = -heading

    return heading 