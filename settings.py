import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty, IntProperty, FloatProperty, StringProperty

from sverchok import data_structure
from sverchok.core import handlers
from sverchok.core import update_system
from sverchok.utils import sv_panels_tools
from sverchok.ui import color_def
from sverchok.ui.sv_icons import custom_icon

from sverchok.menu import make_node_cats
from collections import OrderedDict

import os
import json
import glob
from pprint import pprint

tab_items = [
    ("GENERAL", "General", "General settings", custom_icon("SV_PREFS_GENERAL"), 0),
    ("THEMES", "Themes", "Update nodes theme colors", custom_icon("SV_PREFS_THEMES"), 1),
    ("DEFAULTS", "Defaults", "Various node default values", custom_icon("SV_PREFS_DEVELOPER"), 2),
]

_theme_collection = OrderedDict()
_current_theme = "default"


def get_themes_path():
    '''
        Get the themes path. Create one first if it doesn't exist.
    '''
    dirPath = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    themePath = os.path.join(dirPath, 'themes')

    # create theme path if it doesn't exist
    if not os.path.exists(themePath):
        os.mkdir(themePath)

    return themePath


def get_theme_files():
    '''
        Get the theme files for all the themes present at the themes path
    '''
    themePath = get_themes_path()
    themeFilePattern = os.path.join(themePath, "*.json")
    themeFiles = glob.glob(themeFilePattern)

    return themeFiles


def get_theme_files_names():
    '''
        Get the theme file base names for all themes present at the theme path
    '''
    themeFiles = get_theme_files()
    themeFileNames = [os.path.basename(x) for x in glob.glob(themeFiles)]
    themeFileNames = [os.path.splitext(f)[0] for f in themeFileNames]

    return themeFileNames


def load_theme(filePath):
    '''
        Load a theme from the given file path
    '''
    print("loading theme: ", filePath)
    theme = {}
    with open(filePath, 'r') as infile:
        theme = json.load(infile, object_pairs_hook=OrderedDict)

    return theme


def load_themes():
    '''
        Load all the themes from disk into a cache
    '''
    if _theme_collection:  # return if themes already loaded
        print("The themes are already loaded (SKIP)")
        return

    print("Loading the themes...")

    themeFiles = get_theme_files()

    for f in themeFiles:
        # print("filepath: ", filePath)
        theme = load_theme(f)
        fileName = os.path.splitext(os.path.basename(f))[0]
        print("filename : ", fileName)
        # fileName = os.path.splitext(f)[0]
        _theme_collection[fileName] = theme

    for fileName, theme in _theme_collection.items():
        print("Theme : ", fileName, " is called: ", theme["Name"])

    print(_theme_collection)


def save_theme(theme, fileName):
    '''
        Save the given theme to disk
    '''
    print("save theme to:", fileName)

    themePath = get_themes_path()
    themeFile = os.path.join(themePath, fileName)
    print("filepath: ", themeFile)
    with open(themeFile, 'w') as outfile:
        json.dump(theme, outfile, indent=4, separators=(',', ':'))


def save_default_themes():
    '''
        Save the default themes to disk
    '''
    theme1 = {
        "Name": "Default",

        "Node Colors":
        {
            "Visualizer": [1.0, 0.3, 0.0],
            "Text": [0.5, 0.5, 1.0],
            "Scene": [0.0, 0.5, 0.2],
            "Layout": [0.674, 0.242, 0.363],
            "Generators": [0.0, 0.5, 0.5],
            "Generators Extended": [0.4, 0.7, 0.7]
        },

        "Error Colors":
        {
            "Exception": [0.8, 0.0, 0.0],
            "No Data": [1.0, 0.3, 0.0]
        },

        "Heat Map Colors":
        {
            "Heat Map Cold": [1.0, 1.0, 1.0],
            "Heat Map Hot": [0.8, 0.0, 0.0]
        },
    }

    theme2 = {
        "Name": "Nipon Blossom",

        "Node Colors":
        {
            "Visualizer": [0.628488, 0.931008, 1.000000],
            "Text": [1.000000, 0.899344, 0.974251],
            "Scene": [0.904933, 1.000000, 0.883421],
            "Layout": [0.602957, 0.674000, 0.564277],
            "Generators": [0.92, 0.92, 0.92],
            "Generators Extended": [0.95, 0.95, 0.95],
        },

        "Error Colors":
        {
            "Exception": [0.8, 0.0, 0.0],
            "No Data": [1.0, 0.3, 0.0],
        },

        "Heat Map Colors":
        {
            "Heat Map Cold": [1.0, 1.0, 1.0],
            "Heat Map Hot": [0.8, 0.0, 0.0],
        },
    }

    t1 = json.loads(json.dumps(theme1), object_pairs_hook=OrderedDict)
    t2 = json.loads(json.dumps(theme2), object_pairs_hook=OrderedDict)

    save_theme(t1, "default.json")
    save_theme(t2, "nipon_blossom.json")


def theme_color(group, name):
    '''
        Return the color int the current theme for the given group & name
    '''
    load_themes()  # loads the themes if not already loaded

    theme = _theme_collection[_current_theme]
    return theme[group][name]


class SvAddThemePreset(bpy.types.Operator):

    """ Add theme preset """
    bl_idname = "node.sv_add_theme_preset"
    bl_label = "Save Theme Preset"

    themeName = StringProperty()

    def execute(self, context):
        print('Adding Theme Preset')
        _current_theme = self.themeName
        for name in ["Visualizer", "Text", "Scene", "Layout", "Scene", "Generators", "Generators Extended"]:
            color = theme_color("Node Colors", name)
            print("Color for: ", name, " is : ", color)

        return {'FINISHED'}


class SvRemoveThemePreset(bpy.types.Operator):

    """ Remove theme preset """
    bl_idname = "node.sv_remove_theme_preset"
    bl_label = "Remove Theme Preset"

    def execute(self, context):
        print('Removing Theme Preset')
        return {'FINISHED'}


# class SvAddRemoveTheme(bpy.types.Operator):
#     """
#         add current settings as new theme or remove currently selected theme
#         (doesn't work on hardcoded themes: default, nippon_blossom)
#     """

#     bl_idname = "node.sv_add_remove_theme"
#     bl_label = "Add Remove Theme"
#     # bl_options = {'REGISTER', 'UNDO'}

#     behaviour = bpy.props.StringProperty(default='')

#     def execute(self, context):
#         n = context.node

#         if self.behaviour == 'store current theme':
#             print("A")
#         elif self.behaviour == 'remove current theme':
#             print("B")

#         return {'FINISHED'}


class SverchokPreferences(AddonPreferences):

    bl_idname = __package__

    def select_theme(self, context):
        # color_def.color_callback(self, context)
        # self.load_theme_values(self.sv_theme)
        get_theme_files_names()
        print("selecting theme: update colors")

    def update_debug_mode(self, context):
        data_structure.DEBUG_MODE = self.show_debug

    def update_heat_map(self, context):
        data_structure.heat_map_state(self.heat_map)

    def set_frame_change(self, context):
        handlers.set_frame_change(self.frame_change_mode)

    def update_theme(self, context):
        color_def.rebuild_color_cache()
        if self.auto_apply_theme:
            color_def.apply_theme()

    def update_defaults(self, context):
        print("Update Defaults")
        self.load_theme_values()

    #  debugish...
    show_debug = BoolProperty(
        name="Print update timings",
        description="Print update timings in console",
        default=False, subtype='NONE',
        update=update_debug_mode)

    no_data_color = FloatVectorProperty(
        name="No data", description='When a node can not get data',
        size=3, min=0.0, max=1.0,
        default=(1, 0.3, 0), subtype='COLOR',
        update=update_system.update_error_colors)

    exception_color = FloatVectorProperty(
        name="Error", description='When node has an exception',
        size=3, min=0.0, max=1.0,
        default=(0.8, 0.0, 0), subtype='COLOR',
        update=update_system.update_error_colors)

    #  heat map settings
    heat_map = BoolProperty(
        name="Heat map",
        description="Color nodes according to time",
        default=False, subtype='NONE',
        update=update_heat_map)

    heat_map_hot = FloatVectorProperty(
        name="Heat map hot", description='',
        size=3, min=0.0, max=1.0,
        default=(.8, 0, 0), subtype='COLOR')

    heat_map_cold = FloatVectorProperty(
        name="Heat map cold", description='',
        size=3, min=0.0, max=1.0,
        default=(1, 1, 1), subtype='COLOR')

    #  theme settings
    sv_theme = EnumProperty(
        items=color_def.themes,
        name="Theme preset",
        description="Select a theme preset",
        update=select_theme,
        default="default_theme")

    auto_apply_theme = BoolProperty(
        name="Apply theme", description="Apply theme automatically",
        default=False)

    apply_theme_on_open = BoolProperty(
        name="Apply theme", description="Apply theme automatically on open",
        default=False)

    color_viz = FloatVectorProperty(
        name="Visualization", description='',
        size=3, min=0.0, max=1.0,
        default=(1, 0.3, 0), subtype='COLOR',
        update=update_theme)

    # colors = {}

    # for f in range(10):Er
    #     colors[f] = FloatVectorProperty(
    #         name="Color", description='Next Color',
    #         size=3, min=0.0, max=1.0,
    #         default=(0.5, 0.5, 0.5), subtype='COLOR',
    #         update=update_theme)
    #     # print(f)

    color_tex = FloatVectorProperty(
        name="Text", description='',
        size=3, min=0.0, max=1.0,
        default=(0.5, 0.5, 1), subtype='COLOR',
        update=update_theme)

    color_sce = FloatVectorProperty(
        name="Scene", description='',
        size=3, min=0.0, max=1.0,
        default=(0, 0.5, 0.2), subtype='COLOR',
        update=update_theme)

    color_lay = FloatVectorProperty(
        name="Layout", description='',
        size=3, min=0.0, max=1.0,
        default=(0.674, 0.242, 0.363), subtype='COLOR',
        update=update_theme)

    color_gen = FloatVectorProperty(
        name="Generator", description='',
        size=3, min=0.0, max=1.0,
        default=(0, 0.5, 0.5), subtype='COLOR',
        update=update_theme)

    color_genx = FloatVectorProperty(
        name="Generator X", description='',
        size=3, min=0.0, max=1.0,
        default=(0.4, 0.7, 0.7), subtype='COLOR',
        update=update_theme)

    #  frame change
    frame_change_modes = [
        ("PRE", "Pre", "Update Sverchok before frame change", 0),
        ("POST", "Post", "Update Sverchok after frame change", 1),
        ("NONE", "None", "Sverchok doesn't update on frame change", 2)
    ]

    frame_change_mode = EnumProperty(
        items=frame_change_modes,
        name="Frame change",
        description="Select frame change handler",
        default="POST",
        update=set_frame_change)

    #  ctrl+space settings

    show_icons = BoolProperty(
        name="Show icons in ctrl+space menu",
        default=False,
        description="Use icons in ctrl+space menu")

    enable_icon_manager = BoolProperty(
        name="Enable Icon Manager",
        default=False,
        description="Enable SV icon manager node")

    over_sized_buttons = BoolProperty(
        name="Big buttons",
        default=False,
        description="Very big buttons")

    enable_live_objin = BoolProperty(
        description="Objects in edit mode will be updated in object-in Node")

    tabs = EnumProperty(
        name="Sections", description="Setting Sections",
        default="GENERAL", items=tab_items)

    # node default values
    color_verts = FloatVectorProperty(
        name="Verts", description='Vertex Color',
        size=3, min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0), subtype='COLOR',
        update=update_defaults)

    color_edges = FloatVectorProperty(
        name="Edges", description='Edge Color',
        size=3, min=0.0, max=1.0,
        default=(0.5, 0.75, 0.9), subtype='COLOR',
        update=update_defaults)

    color_polys = FloatVectorProperty(
        name="Polys", description='Poly Color',
        size=3, min=0.0, max=1.0,
        default=(0.0, 0.5, 0.9), subtype='COLOR',
        update=update_defaults)

    vert_size = FloatProperty(
        name="Vert size", description="Vertex size",
        min=0.0, max=10.0, default=3.2)

    edge_width = FloatProperty(
        name="Edge width", description="Edge width",
        min=1.0, max=10.0, default=2.0)

    enable_center = BoolProperty(
        name="Centering ON", description="Set centering to ON in various nodes",
        default=False)

    def split_columns(self, panel, ratios):
        '''
            Splits the given panel into columns based on the given ratios
            e.g ratios = [1, 2, 1] or [.2, .3, .2] etc
            Note: The sum of all ratio numbers don't need to be normalized
        '''
        col2 = panel
        cols = []
        for n in range(len(ratios)):
            n1 = ratios[n]  # size of the current column
            n2 = sum(ratios[n + 1:])  # size of all remaining columns
            p = n1 / (n1 + n2)  # percentage split of current vs remaming columns
            split = col2.split(percentage=p, align=True)
            col1 = split.column()
            col2 = split.column()
            cols.append(col1)
        return cols

    def draw_general_tab_ui(self, tab):
        # print("Draw the GENERAL tab UI")
        cols = self.split_columns(tab, [1, 1, 1])

        col = cols[0]

        col.label(text="Debug:")
        box = col.box()
        box.prop(self, "show_debug")
        box.prop(self, "enable_live_objin", text='Enable Live Object-In')
        box.prop(self, "heat_map", text="Heat Map")

        col = cols[1]

        col.label(text="Frame change handler:")
        box = col.box()
        row = box.row()
        row.prop(self, "frame_change_mode", expand=True)

        col = cols[2]
        col.label(text="Enable:")
        box = col.box()
        box.prop(self, "enable_center")

    def draw_theme_tab_ui(self, tab):
        # print("Draw the THEME tab UI")
        colA, colB = self.split_columns(tab, [1, 2])

        colA.label(text="")
        colA.label(text="Theme update settings:")
        box = colA.box()
        box.prop(self, 'auto_apply_theme', text="Auto apply theme changes")
        box.prop(self, 'apply_theme_on_open', text="Apply theme when opening file")
        box.separator()
        box.operator('node.sverchok_apply_theme', text="Apply theme to layouts")

        colA.label(text="UI settings:")
        box = colA.box()
        box.prop(self, "show_icons")
        box.prop(self, "over_sized_buttons")
        box.prop(self, "enable_icon_manager")

        row = colB.row(align=True)
        row.prop(self, 'sv_theme')
        row.operator("node.sv_add_theme_preset", text="", icon='ZOOMIN').themeName = self.sv_theme
        row.operator("node.sv_remove_theme_preset", text="", icon='ZOOMOUT')

        colB1, colB2 = self.split_columns(colB, [1, 1])

        colB1.label("Nodes Colors:")
        box = colB1.box()
        for name in ['color_viz', 'color_tex', 'color_sce', 'color_lay', 'color_gen', 'color_genx']:
            row = box.row()
            row.prop(self, name)

        colB2.label("Error Colors:")
        box = colB2.box()
        for name in ['exception_color', 'no_data_color']:
            row = box.row()
            row.prop(self, name)

        colB2.label("Heat Map Colors:")
        box = colB2.box()
        box.active = self.heat_map
        for name in ['heat_map_hot', 'heat_map_cold']:
            row = box.row()
            row.prop(self, name)

        # print("there are ", len(self.colors), " custom colors")
        # colB2.label("Other Colors:")
        # box = colB2.box()
        # for color in self.colors.values():
        #     print("color = ", color)
        #     # name = color.name
        #     row = box.row()
        #     row.prop(self, "colors[1]")
        #     # row.prop(self, name)

    def draw_defaults_tab_ui(self, tab):
        # print("Draw the DEFAULTS tab UI")
        cols = self.split_columns(tab, [1, 1, 1, 1])

        col = cols[0]
        col.label(text="Viewer Colors:")
        box = col.box()
        for name in ['color_verts', 'color_edges', 'color_polys']:
            row = box.row()
            row.prop(self, name)

        col = cols[1]
        col.label(text="Viewer Sizes:")
        box = col.box()
        for name in ['vert_size', 'edge_width']:
            row = box.row()
            row.prop(self, name)

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "tabs", expand=True)
        row.scale_y = 1.5
        row = col.row(align=True)

        if self.tabs == "THEMES":
            self.draw_theme_tab_ui(row)

        elif self.tabs == "GENERAL":
            self.draw_general_tab_ui(row)

        elif self.tabs == "DEFAULTS":
            self.draw_defaults_tab_ui(row)

        col = layout.column(align=True)
        col.label(text="Links:")
        row1 = col.row(align=True)
        row1.scale_y = 2.0
        row1.operator('wm.url_open', text='Sverchok home page').url = 'http://nikitron.cc.ua/blend_scripts.html'
        row1.operator('wm.url_open', text='Documentation').url = 'http://nikitron.cc.ua/sverch/html/main.html'

        if context.scene.sv_new_version:
            row1.operator('node.sverchok_update_addon', text='Upgrade Sverchok addon')
        else:
            row1.operator('node.sverchok_check_for_upgrades_wsha', text='Check for new version')


def register():
    save_default_themes()

    bpy.utils.register_class(SverchokPreferences)
    bpy.utils.register_class(SvAddThemePreset)
    bpy.utils.register_class(SvRemoveThemePreset)


def unregister():
    bpy.utils.unregister_class(SverchokPreferences)
    bpy.utils.unregister_class(SvAddThemePreset)
    bpy.utils.unregister_class(SvRemoveThemePreset)

if __name__ == '__main__':
    register()
