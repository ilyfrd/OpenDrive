road_id = 0
road_map = {}

def generate_road_id():
    '''
    生成road的唯一id。
    '''
    return len(road_map)

def set_road_data(id, road_data):
    road_map[id] = road_data

def get_road_data(id):
    return road_map.get(id)

def get_map_data():
    return road_map


