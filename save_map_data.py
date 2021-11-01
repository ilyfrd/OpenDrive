import bpy
import numpy as np
import json

from mathutils import Vector

from .utils import draw_utils
from .utils import math_utils
from .utils import cubic_curve_fitting_utils

from . import map_scene_data

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

class SaveMapData(bpy.types.Operator):
    bl_idname = 'dsc.save_map_data'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        ''''''

    def save_element(self, src, target):
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

    def save_reference_line_sections(self, reference_line_sections_src, reference_line_sections_target):
        for reference_line_section in reference_line_sections_src:
            reference_line_section_data = []

            for element in reference_line_section:
                element_data = {}
                self.save_element(element, element_data)
                reference_line_section_data.append(element_data)

            reference_line_sections_target.append(reference_line_section_data)

    def save_lane_sections(self, lane_sections_src, lane_sections_target):
        def save_boundary_curve_elements(src, target):
            for element in src:
                element_data = {}
                self.save_element(element, element_data)
                target.append(element_data)

        def save_cubic_curve_factors_per_width(src, target):
            for cubic_curve_factors in src:
                target.append(cubic_curve_factors)

        def save_curve_fit_sections(src, target):
            for curve_fit_section in src:
                curve_fit_section_data = []
                
                for element in curve_fit_section:
                    element_data = {}
                    self.save_element(element, element_data)
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

    def save_map_date(self):
        map_data = {}

        map = map_scene_data.get_map_data()
        for road_id, road_value in map.items():
            road_data = {}
            road_data['reference_line_sections'] = []
            road_data['lane_sections'] = []

            reference_line_sections = road_value['reference_line_sections']
            self.save_reference_line_sections(reference_line_sections, road_data['reference_line_sections'])

            lane_sections = road_value['lane_sections']
            self.save_lane_sections(lane_sections, road_data['lane_sections'])

            map_data[str(road_id)] = road_data
            
        with open('./data.json', 'w') as outfile:
            json.dump(map_data, outfile, indent = 4, cls = NumpyEncoder)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        self.save_map_date()

        return {'FINISHED'}
