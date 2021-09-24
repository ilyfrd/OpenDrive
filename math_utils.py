



from mathutils import Vector


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
