
lane_object_id = 0
reference_line_object_id = 0


road_map = {}

def generate_lane_object_id():
    global lane_object_id
    lane_object_id += 1
    return lane_object_id

def generate_reference_line_object_id():
    global reference_line_object_id
    reference_line_object_id += 1
    return reference_line_object_id

def set_road_data(road_id, road_data):
    road_map[road_id] = road_data
