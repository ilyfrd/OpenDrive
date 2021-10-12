road_id = 0
road_map = {}

def generate_road_id():
    global road_id
    road_id += 1
    return road_id

def set_road_data(id, road_data):
    road_map[id] = road_data

def get_road_data(id):
    return road_map.get(id)


