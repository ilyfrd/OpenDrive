import bpy
import bmesh
from mathutils import Vector, Matrix

from math import pi

from . import helpers


class DrawJunction(bpy.types.Operator):
    bl_idname = 'dsc.draw_junction'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    mesh = None


    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

