import bpy

from .utils import draw_utils
from .utils import math_utils
from .utils import cubic_curve_fitting_utils
from .utils import export_import_utils

from . import map_scene_data


class RemoveRoad(bpy.types.Operator):
    bl_idname = 'dsc.remove_road'
    bl_label = 'xxx'
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        ''''''

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        context.workspace.status_text_set("xxx")
        bpy.context.window.cursor_modal_set('CROSSHAIR')

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            hit, raycast_point, raycast_object = math_utils.raycast_mouse_to_object(context, event, 'lane')
            if hit:
                name_sections = raycast_object.name.split('_')
                last_index = len(name_sections) - 1
                road_id = int(name_sections[last_index - 2])

                road_data = map_scene_data.get_road_data(road_id)
                lane_to_object_map = road_data['lane_to_object_map']
                for key, value in lane_to_object_map.items():
                    bpy.data.objects.remove(value, do_unlink=True) # 删除车道在场景中的实物object

                road_reference_line_object = road_data['road_reference_line_object']
                bpy.data.objects.remove(road_reference_line_object, do_unlink=True) # 删除道路参考线在场景中的实物object

                road_object = road_data['road_object']
                bpy.data.objects.remove(road_object, do_unlink=True) # 删除道路object，道路object只作为一个容器存在，没有mesh。
                
                map_scene_data.remove_road_data(road_id)

            return {'RUNNING_MODAL'}

        elif event.type in {'ESC'}:
            self.clean_up(context)

            return {'FINISHED'}
            
        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type in {'MIDDLEMOUSE'}:
            if event.alt:
                bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        draw_utils.set_context(context)

        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        context.workspace.status_text_set(None)

        bpy.context.window.cursor_modal_restore()

        if bpy.context.active_object:
            if bpy.context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
 

