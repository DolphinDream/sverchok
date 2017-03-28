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


def cache_category_node_list():
    '''
        Cache category-node list for color access.
    '''
    if _category_node_list:
        return

    node_category_list = make_node_cats()

    for category, nodes in node_category_list.items():
        for node in nodes:
            _category_node_list[node[0]] = category

    # print("category node list = ", _category_node_list)


def get_themes_path():
    '''
        Get the themes path. Create one first if it doesn't exist.
    '''
    dirPath = os.path.join(bpy.utils.user_resource(
        'DATAFILES', path='sverchok', create=True))
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
        # print("The themes are already loaded (SKIP)")
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

    print("Loaded theme collection: ", _theme_collection)


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
        Groups : "Node Colors", "Error Colors", "Heat Map Colors" etc
        Name : "Visualizer", "Text", "Generators" etc
    '''
    load_themes()  # loads the themes if not already loaded

    # print("theme collection: ", _theme_collection)

    theme = _theme_collection[_current_theme]
    return theme[group][name]


def get_node_color(nodeID):
    '''
        Return the theme color of a node given its node ID (category)
    '''
    nodeCategory = _category_node_list[nodeID]
    # print("NodeID: ", nodeID, " is in category:", nodeCategory)
    # print("theme collection: ", _theme_collection)

    theme = _theme_collection[_current_theme]

    if nodeCategory in theme["Node Colors"]:
        print("Category: ", nodeCategory, " found in the theme")
        return theme_color("Node Colors", nodeCategory)
    else:
        print("Category: ", nodeCategory, " NOT found in the theme")


class SvAddRemoveTheme(bpy.types.Operator):
    """
        Add current settings as new theme or remove currently selected theme.
        Note: it doesn't work on hardcoded themes: default, nippon_blossom
    """

    bl_idname = "node.sv_add_remove_theme"
    bl_label = "Add Remove Theme"
    # bl_options = {'REGISTER', 'UNDO'}

    behaviour = StringProperty(default='')

    def add_theme(self):
        # prefs = sv_preferences()

        print("add_theme in action")

        with sv_preferences() as prefs:
            print("Prefs color_viz:", prefs.color_viz)
            print("Prefs color_tex:", prefs.color_tex)

            themeName = "Dolphin Dream"

            theme = OrderedDict()
            nodeColors = OrderedDict()
            errorColors = OrderedDict()
            heatMapColors = OrderedDict()

            theme["Name"] = themeName

            nodeColors["Visualizers"] = prefs.color_viz[:]
            nodeColors["Text"] = prefs.color_tex[:]
            nodeColors["Scene"] = prefs.color_sce[:]
            nodeColors["Layout"] = prefs.color_lay[:]
            nodeColors["Generators"] = prefs.color_gen[:]
            nodeColors["Generators Extended"] = prefs.color_genx[:]

            errorColors["Exception Color"] = prefs.exception_color[:]
            errorColors["No Data"] = prefs.no_data_color[:]

            heatMapColors["Heat Map Cold"] = prefs.heat_map_cold[:]
            heatMapColors["Heat Map Hot"] = prefs.heat_map_cold[:]

            theme["Node Colors"] = nodeColors
            theme["Error Colors"] = errorColors
            theme["Heat Map Colors"] = heatMapColors

            print("theme: ", theme)

            save_theme(theme, "dolphin_dream.json")

    def remove_theme(self):
        print("remove_theme in action")

    def execute(self, context):
        if self.behaviour == 'add':
            self.add_theme()
        elif self.behaviour == 'remove':
            self.remove_theme()
        else:
            print("Warning: invalid add/remove theme behavior")

        return {'FINISHED'}


def register():
    save_default_themes()
    cache_category_node_list()
    bpy.utils.register_class(SvAddRemoveTheme)


def unregister():
    bpy.utils.unregister_class(SvAddRemoveTheme)

if __name__ == '__main__':
    register()
