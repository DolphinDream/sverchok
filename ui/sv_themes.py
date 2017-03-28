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
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty, IntProperty, FloatProperty, StringProperty

from collections import OrderedDict

import os
import json
import glob
from pprint import pprint

from sverchok.menu import make_node_cats


_category_node_list = {}
_theme_collection = OrderedDict()
_current_theme = "default"


def cache_category_node_list():
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
    '''
    load_themes()  # loads the themes if not already loaded

    print("theme collection: ", _theme_collection)

    theme = _theme_collection[_current_theme]
    return theme[group][name]


def get_node_color(nodeID):
    nodeCategory = _category_node_list[nodeID]
    print("NodeID: ", nodeID, " is in category:", nodeCategory)

    print("theme collection: ", _theme_collection)

    theme = _theme_collection[_current_theme]

    if nodeCategory in theme["Node Colors"]:
        print("Category: ", nodeCategory, " found in the theme")
        return theme_color("Node Colors", nodeCategory)
    else:
        print("Category: ", nodeCategory, " NOT found in the theme")
        # return


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


def register():
    save_default_themes()
    cache_category_node_list()
    bpy.utils.register_class(SvAddThemePreset)
    bpy.utils.register_class(SvRemoveThemePreset)


def unregister():
    bpy.utils.unregister_class(SvAddThemePreset)
    bpy.utils.unregister_class(SvRemoveThemePreset)

if __name__ == '__main__':
    register()
