# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import bpy.utils.previews

import os

from . export import DSC_OT_export
from . draw_road import DrawRoad
from . segment_road import SegmentRoad
from . adjust_lane_numbers import AdjustLaneNumbers
from . adjust_lane_boundary import AdjustLaneBoundary
from . draw_lane_boundary import DrawLaneBoundary

from . draw_junction import DrawJunction

from . check_lane_width_curve_fit import CheckLaneWidthCurveFit
from . adjust_curve_fit_sections import AdjustCurveFitSections
from . draw_segmenting_line_for_curve_fitting import DrawSegmentingLineForCurveFitting
from . save_map_scene import SaveMapScene
from . open_map_scene import OpenMapScene
from . export_open_drive_map import ExportOpenDriveMap
from . remove_road import RemoveRoad

from .utils import export_import_utils

from . import map_scene_data




bl_info = {
    'name' : 'Open Drive',
    'author' : 'yangtian',
    'description' : 'Create OpenDRIVE and OpenSCENARIO based driving scenarios.',
    'blender' : (2, 93, 0),
    'version' : (0, 6, 0),
    'location' : 'View3D > Sidebar > Open Drive',
    'warning' : '',
    'doc_url': '',
    'tracker_url': 'https://github.com/johschmitz/blender-driving-scenario-creator/issues',
    'link': 'https://github.com/johschmitz/blender-driving-scenario-creator',
    'support': 'COMMUNITY',
    'category' : 'Add Mesh'
}

# Global variables
custom_icons = None

class DSC_PT_panel_create(bpy.types.Panel):
    bl_idname = 'DSC_PT_panel_create'
    bl_label = 'Open Drive'
    bl_category = 'Open Drive'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'

    def draw(self, context):
        global custom_icons

        layout = self.layout

        outerBox = layout.box()
        outerBox.label(text='高精度地图制作工具集')

        innerBox = outerBox.box()
        innerBox.label(text='绘制')
        row = innerBox.row(align=True)
        row.operator('dsc.draw_road', text='绘制道路', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.remove_road', text='删除道路', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.segment_road', text='道路分段', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.adjust_lane_numbers', text='调整车道数量', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.adjust_lane_boundary', text='调整车道边界', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.draw_lane_boundary', text='显示/隐藏车道边界线', icon_value=custom_icons['road_straight'].icon_id)

        # innerBox = outerBox.box()
        # innerBox.label(text='Junction')
        # row = innerBox.row(align=True)
        # row.operator('dsc.draw_junction', text='Draw Junction', icon_value=custom_icons['road_straight'].icon_id)
        # row = innerBox.row(align=True)
        # row.operator('dsc.edit_junction', text='Edit Junction', icon_value=custom_icons['road_straight'].icon_id)

        innerBox = outerBox.box()
        innerBox.label(text='检查')
        row = innerBox.row(align=True)
        row.operator('dsc.check_lane_width_curve_fit', text='车道宽度三次曲线拟合检查', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.adjust_curve_fit_sections', text='调整车道宽度元素数量', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.draw_segmenting_line_for_curve_fitting', text='显示/隐藏三次曲线拟合分段线', icon_value=custom_icons['road_straight'].icon_id)

        innerBox = outerBox.box()
        innerBox.label(text='导入/导出')
        row = innerBox.row(align=True)
        row.operator('dsc.open_map_scene', text='打开地图场景', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.save_map_scene', text='保存地图场景', icon_value=custom_icons['road_straight'].icon_id)
        row = innerBox.row(align=True)
        row.operator('dsc.export_open_drive_map', text='导出高精度地图', icon_value=custom_icons['road_straight'].icon_id)

        # box = layout.box()
        # box.label(text='Export (Track, Scenario, Mesh)')
        # row = box.row(align=True)
        # row.operator('dsc.export_driving_scenario', icon='EXPORT')

def menu_func_export(self, context):
    self.layout.operator('dsc.export_driving_scenario', text='Driving Scenario (.xosc, .xodr, .fbx/.gltf/.osgb)')

classes = (
    DSC_OT_export,
    DSC_PT_panel_create,
    DrawRoad,
    SegmentRoad,
    AdjustLaneNumbers,
    AdjustLaneBoundary,
    DrawLaneBoundary,
    DrawJunction,
    CheckLaneWidthCurveFit,
    AdjustCurveFitSections,
    DrawSegmentingLineForCurveFitting,
    SaveMapScene,
    OpenMapScene,
    ExportOpenDriveMap,
    RemoveRoad
)

def register():
    global custom_icons
    # Load custom icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    custom_icons.load('road_straight', os.path.join(icons_dir, 'road_straight.png'), 'IMAGE')
    custom_icons.load('road_arc', os.path.join(icons_dir, 'road_arc.png'), 'IMAGE')
    custom_icons.load('road_spiral', os.path.join(icons_dir, 'road_spiral.png'), 'IMAGE')
    custom_icons.load('road_parametric_polynomial', os.path.join(icons_dir, 'road_parametric_polynomial.png'), 'IMAGE')
    custom_icons.load('junction', os.path.join(icons_dir, 'junction.png'), 'IMAGE')
    custom_icons.load('trajectory_nurbs', os.path.join(icons_dir, 'trajectory_nurbs.png'), 'IMAGE')
    custom_icons.load('trajectory_polyline', os.path.join(icons_dir, 'trajectory_polyline.png'), 'IMAGE')

    # Register all addon classes
    for c in classes:
        bpy.utils.register_class(c)
    # Register export menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    # Register property groups

def unregister():
    global custom_icons
    # Unregister export menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    #  Unregister all addon classes
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    # Get rid of custom icons
    bpy.utils.previews.remove(custom_icons)


if __name__ == '__main__':
    register()


