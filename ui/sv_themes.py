# -*- coding: utf-8 -*-
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import StringProperty

from collections import OrderedDict

import re
import os
import json
import glob
from pprint import pprint

import sverchok
from sverchok.menu import make_node_cats
from sverchok.utils.context_managers import sv_preferences

_category_node_list = {}
_theme_collection = OrderedDict()
_current_theme = "default"
_theme_preset_list = []


def get_theme_preset_list():
    # print("get the theme preset list")
    return _theme_preset_list


def update_theme_preset_list():
    # load_themes()

    _theme_preset_list.clear()
    for name, theme in _theme_collection.items():
        themeName = theme["Name"]
        print("file name = ", name)
        print("theme name = ", themeName)
        themeItem = (name, themeName, themeName)
        _theme_preset_list.append(themeItem)


def cache_category_node_list():
    """ Cache the category-node list for color access. """
    if _category_node_list:
        return

    node_category_list = make_node_cats()

    for category, nodes in node_category_list.items():
        for node in nodes:
            _category_node_list[node[0]] = category

    # print("category node list = ", _category_node_list)


def get_node_category(nodeID):
    """ Get the note category for the given node ID """
    cache_category_node_list()  # make sure the category-node list is cached
    return _category_node_list[nodeID]  # @todo check if nodeID is in list


def get_themes_path():
    """ Get the themes path. Create one first if it doesn't exist """
    dirPath = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    themePath = os.path.join(dirPath, 'themes')

    # create theme path if it doesn't exist
    if not os.path.exists(themePath):
        os.mkdir(themePath)

    return themePath


def get_theme_files():
    """ Get the theme files for all the themes present at the themes path """
    themePath = get_themes_path()
    themeFilePattern = os.path.join(themePath, "*.json")
    themeFiles = glob.glob(themeFilePattern)

    return themeFiles


def load_theme(filePath):
    """ Load a theme from the given file path """
    print("loading theme: ", filePath)
    theme = {}
    with open(filePath, 'r') as infile:
        theme = json.load(infile, object_pairs_hook=OrderedDict)

    return theme


def load_themes(reload=False):
    """ Load all the themes from disk into a cache """
    # return if the themes are already loaded
    if _theme_collection and not reload:
        return

    print("Loading the themes...")

    themeFiles = get_theme_files()

    for f in themeFiles:
        # print("filepath: ", filePath)
        theme = load_theme(f)
        fileName = os.path.splitext(os.path.basename(f))[0]
        print("filename : ", fileName)
        _theme_collection[fileName] = theme

    for fileName, theme in _theme_collection.items():
        print("Theme : ", fileName, " is called: ", theme["Name"])

    print("Loaded theme collection: ", _theme_collection)


def save_theme(theme, fileName):
    """ Save the given theme to disk """
    print("save theme to:", fileName)

    themePath = get_themes_path()
    themeFile = os.path.join(themePath, fileName)
    print("filepath: ", themeFile)
    with open(themeFile, 'w') as outfile:
        json.dump(theme, outfile, indent=4, separators=(',', ':'))


def save_default_themes():
    """ Save the hardcoded default themes to disk """

    # DEFAULT theme
    themeName = "Default"

    theme = OrderedDict()
    nodeColors = OrderedDict()
    errorColors = OrderedDict()
    heatMapColors = OrderedDict()

    theme["Name"] = themeName

    nodeColors["Visualizer"] = [1.0, 0.3, 0.0]
    nodeColors["Text"] = [1.0, 0.3, 0.0]
    nodeColors["Scene"] = [0.0, 0.5, 0.2]
    nodeColors["Layout"] = [0.674, 0.242, 0.363]
    nodeColors["Generators"] = [0.0, 0.5, 0.5]
    nodeColors["Generators Extended"] = [0.4, 0.7, 0.7]

    errorColors["Exception"] = [0.8, 0.0, 0.0]
    errorColors["No Data"] = [1.0, 0.3, 0.0]

    heatMapColors["Heat Map Cold"] = [1.0, 1.0, 1.0]
    heatMapColors["Heat Map Hot"] = [0.8, 0.0, 0.0]

    theme["Node Colors"] = nodeColors
    theme["Error Colors"] = errorColors
    theme["Heat Map Colors"] = heatMapColors

    themeFileName = re.sub(r'[ ]', '_', themeName.lower()) + ".json"

    save_theme(theme, themeFileName)

    # NIPON-BLOSSOM theme
    themeName = "Nipon Blossom"

    theme = OrderedDict()
    nodeColors = OrderedDict()
    errorColors = OrderedDict()
    heatMapColors = OrderedDict()

    theme["Name"] = themeName

    nodeColors["Visualizer"] = [0.628488, 0.931008, 1.000000]
    nodeColors["Text"] = [1.000000, 0.899344, 0.974251]
    nodeColors["Scene"] = [0.904933, 1.000000, 0.883421]
    nodeColors["Layout"] = [0.602957, 0.674000, 0.564277]
    nodeColors["Generators"] = [0.92, 0.92, 0.92]
    nodeColors["Generators Extended"] = [0.95, 0.95, 0.95]

    errorColors["Exception"] = [0.8, 0.0, 0.0]
    errorColors["No Data"] = [1.0, 0.3, 0.0]

    heatMapColors["Heat Map Cold"] = [1.0, 1.0, 1.0]
    heatMapColors["Heat Map Hot"] = [0.8, 0.0, 0.0]

    theme["Node Colors"] = nodeColors
    theme["Error Colors"] = errorColors
    theme["Heat Map Colors"] = heatMapColors

    themeFileName = re.sub(r'[ ]', '_', themeName.lower()) + ".json"

    # print("save theme with filename: ", fileName)

    save_theme(theme, themeFileName)


def remove_theme(themeName):
    """ Remove theme from theme collection and disk """

    if themeName in ['default', 'nipon_blossom']:
        print("Cannot remove the default themes")
        return

    print("Removing the theme with name: ", themeName)
    if themeName in _theme_collection:
        print("Found theme <", themeName, "> to remove")
        del _theme_collection[themeName]
    else:
        print("NOT Found theme <", themeName, "> to remove")

    themePath = get_themes_path()
    themeFile = os.path.join(themePath, themeName + ".json")
    try:
        os.remove(themeFile)
    except OSError:
        print("failed to remove theme file: ", themeFile)
        pass


def get_current_theme():
    """ Get the currently selected theme """
    load_themes()  # make sure the themes are loaded
    print("getting the current theme for: ", _current_theme)
    return _theme_collection[_current_theme]  # @todo check if name exists


def select_current_theme(themeName):
    global _current_theme
    print("selecting current theme to:", themeName)
    _current_theme = themeName


def theme_color(group, category):
    """
    Return the color in the current theme for the given group & category
    Groups : "Node Colors", "Error Colors", "Heat Map Colors" etc
    Category : "Visualizer", "Text", "Generators" etc
    """
    theme = get_current_theme()
    return theme[group][category]


def get_node_color(nodeID):
    """ Return the theme color of a node given its node ID """
    theme = get_current_theme()
    print("Get node color for current theme name: ", theme["Name"])

    nodeCategory = get_node_category(nodeID)
    print("NodeID: ", nodeID, " is in category:", nodeCategory)

    nodeCategory = "Visualizer" if nodeCategory == "Viz" else nodeCategory

    if nodeCategory in theme["Node Colors"]:
        print("Category: ", nodeCategory, " found in the theme")
        return theme_color("Node Colors", nodeCategory)
    else:
        print("Category: ", nodeCategory, " NOT found in the theme")


def sverchok_trees():
    for ng in bpy.data.node_groups:
        if ng.bl_idname == "SverchCustomTreeType":
            yield ng


def apply_theme(ng=None):
    """ Apply theme colors """
    print("apply theme called")
    if not ng:
        for ng in sverchok_trees():
            apply_theme(ng)
    else:
        for n in filter(lambda n: hasattr(n, "set_color"), ng.nodes):
            n.set_color()


def update_colors():
    with sv_preferences() as prefs:
        prefs.color_viz = theme_color("Node Colors", "Visualizer")
        prefs.color_tex = theme_color("Node Colors", "Text")
        prefs.color_sce = theme_color("Node Colors", "Scene")
        prefs.color_lay = theme_color("Node Colors", "Layout")
        prefs.color_gen = theme_color("Node Colors", "Generators")
        prefs.color_genx = theme_color("Node Colors", "Generators Extended")

        prefs.exception_color = theme_color("Error Colors", "Exception")
        prefs.no_data_color = theme_color("Error Colors", "No Data")

        prefs.heat_map_cold = theme_color("Heat Map Colors", "Heat Map Cold")
        prefs.heat_map_hot = theme_color("Heat Map Colors", "Heat Map Hot")


class SvApplyTheme(bpy.types.Operator):

    """
    Apply Sverchok theme
    """
    bl_idname = "node.sverchok_apply_theme2"
    bl_label = "Sverchok Apply theme"
    bl_options = {'REGISTER', 'UNDO'}

    tree_name = StringProperty()

    def execute(self, context):
        global _current_theme
        with sv_preferences() as prefs:
            _current_theme = prefs.current_theme

        print("applying sverchok theme: ", _current_theme)
        if self.tree_name:
            ng = bpy.data.node_groups.get(self.tree_name)
            if ng:
                apply_theme(ng)
            else:
                return {'CANCELLED'}
        else:
            apply_theme()
        return {'FINISHED'}


class SvAddRemoveTheme(bpy.types.Operator):

    """
    Add current settings as new theme or remove currently selected theme.
    Note: it doesn't work on hardcoded themes: default, nippon_blossom
    """
    bl_idname = "node.sv_add_remove_theme"
    bl_label = "Add Remove Theme"

    behaviour = StringProperty(default='')

    def add_theme(self, themeName):
        print("add_theme in action")

        with sv_preferences() as prefs:

            theme = OrderedDict()
            nodeColors = OrderedDict()
            errorColors = OrderedDict()
            heatMapColors = OrderedDict()

            theme["Name"] = themeName

            nodeColors["Visualizer"] = prefs.color_viz[:]
            nodeColors["Text"] = prefs.color_tex[:]
            nodeColors["Scene"] = prefs.color_sce[:]
            nodeColors["Layout"] = prefs.color_lay[:]
            nodeColors["Generators"] = prefs.color_gen[:]
            nodeColors["Generators Extended"] = prefs.color_genx[:]

            errorColors["Exception"] = prefs.exception_color[:]
            errorColors["No Data"] = prefs.no_data_color[:]

            heatMapColors["Heat Map Cold"] = prefs.heat_map_cold[:]
            heatMapColors["Heat Map Hot"] = prefs.heat_map_hot[:]

            theme["Node Colors"] = nodeColors
            theme["Error Colors"] = errorColors
            theme["Heat Map Colors"] = heatMapColors

            print("theme: ", theme)

            themeFileBase = re.sub(r'[ ]', '_', themeName.lower())

            themeFileName = themeFileBase + ".json"
            save_theme(theme, themeFileName)

    def remove_theme(self, themeName):
        print("remove_theme in action")
        themeFileBase = re.sub(r'[ ]', '_', themeName.lower())
        remove_theme(themeFileBase)

    def update_theme_list(self):
        print("update_theme_list in action")
        load_themes(True)  # force reload themes
        update_theme_list()

    def execute(self, context):
        themeName = "Dolphin Dream"
        if self.behaviour == 'add':
            self.add_theme(themeName)
            self.update_theme_list()
            with sv_preferences() as prefs:
                themeFileBase = re.sub(r'[ ]', '_', themeName.lower())
                prefs.current_theme = themeFileBase

        elif self.behaviour == 'remove':
            self.remove_theme(themeName)
            self.update_theme_list()
            with sv_preferences() as prefs:
                prefs.current_theme = "default"
        else:
            print("Warning: invalid add/remove theme behavior")

        return {'FINISHED'}


def register():
    save_default_themes()
    bpy.utils.register_class(SvAddRemoveTheme)
    bpy.utils.register_class(SvApplyTheme)


def unregister():
    bpy.utils.unregister_class(SvAddRemoveTheme)
    bpy.utils.unregister_class(SvApplyTheme)

if __name__ == '__main__':
    register()
