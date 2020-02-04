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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, StringProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

from math import sin, cos, pi, sqrt, radians
from random import random
import time
import mmap
import os

from mathutils import Quaternion

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

from pprint import pprint

recent_paths_list = set()
recent_paths_dict = dict()

def load_path(filepath):
    # the QMAT file format is :
    #
    # numEntries
    # x y z  x y z w
    # x y z  x y z w
    # ...

    # homeDir = "/home/marius/Downloads/"
    # homeDir = "/Users/atokirina/Downloads/"
    # filepath = homeDir + filepath
    print("loading path: ", filepath)

    verts, quats = [], []

    with open(filepath, 'rb') as file:
        data = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)

        # read the number of entries (locations + quaternions)
        nl = int(data.readline().rstrip())
        # read the location + quaternion for all entries
        for i in range(nl):
            line = data.readline().rstrip()
            l = list(map(float, line.split()))
            v = l[:3]
            q = l[3:]
            q = Quaternion([q[3], q[0], q[1], q[2]])

            verts.append(v)
            quats.append(q)

            # print("l=", l)
            # print("v=", v)
            # print("q=", q)

        data.close()

        print("QMAT file has %d entries" % (nl))

    return verts, quats


class SvPathLoadNode(bpy.types.Node, SverchCustomTreeNode):
    '''Path Loader'''
    bl_idname = 'SvPathLoadNode'
    bl_label = 'Load Path'
    bl_description = 'Load Path from file in vector (3) + quaternion (4) format'

    def set_path(self, filepath):
        filename = os.path.basename(filepath)
        print("setting filepath/filename: ", filepath, filename)
        # recent_paths_list.add(filepath)
        recent_paths_dict[filename]=filepath
        self.file_path = filepath

    def update_path(self, context):
        print("Updating path: ", self.file_path)
        # recent_paths_list.add(self.file_path)
        # load_path(self.file_path)
        updateNode(self, context)

    def update_path_selection(self, context):
        print("Selected path: ", self.selected_path)
        self.file_path = recent_paths_dict[self.selected_path]
        updateNode(self, context)

    def recent_path_items(self, context):
        # recentItems = [(k, k.title(), "", i) for i, k in enumerate(recent_paths_list)]
        recentItems = [(k, k, v, i) for i, (k,v) in enumerate(recent_paths_dict.items())]
        # pprint(recentItems)
        return recentItems

    file_path: StringProperty(
        name="Path File",
        description="Path file name",
        default="", update=update_path)

    selected_path: EnumProperty(
        name="Selected Paths",
        items=recent_path_items,
        update=update_path_selection)

    def sv_init(self, context):
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvQuaternionSocket', "Quaternions")
        self.outputs.new('SvStringsSocket', "Index")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "selected_path", text="")
        row = layout.row()
        # row.prop(self, "file_path")
        col = row.column()
        load_op = col.operator("node.sv_somenode_file_importer", text="Load")
        load_op.idname = self.name
        load_op.idtree = self.id_data.name

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        vertex_list, quaternion_list = load_path(self.file_path)

        # if self.inputs["Quaternions"].is_linked:
        #     input_Q = inputs["Quaternions"].sv_get()
        #     quaternion_list = [Quaternion(q) for q in input_Q]

        index = 0
        for i, (k,v) in enumerate(recent_paths_dict.items()):
            if self.selected_path == k:
                index = i
                break

        self.outputs['Vertices'].sv_set([vertex_list])
        self.outputs['Quaternions'].sv_set(quaternion_list)
        self.outputs['Index'].sv_set([[index]])


class SvSomeNodeFileImporterOp(bpy.types.Operator, ImportHelper):

    bl_idname = "node.sv_somenode_file_importer"
    bl_label = "File Importer"

    filename_ext = ".qmat"
    files = CollectionProperty(type=bpy.types.PropertyGroup)

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024, default="", subtype='FILE_PATH')

    idname: StringProperty(
        name='idname', description='name of parent node', default='')

    idtree: StringProperty(
        name='idtree', description='name of parent tree', default='')

    def get_node(self):
        node_group = bpy.data.node_groups[self.idtree]
        node = node_group.nodes[self.idname]
        return node

    def execute(self, context):
        dirname = os.path.dirname(self.filepath)
        filepaths = [os.path.join(dirname, f.name) for f in self.files]
        print("selected files: ", filepaths)

        n = self.get_node()
        for p in filepaths:
            print("setting path: ", p)
            n.set_path(p)
        # print('executing self.filepath', self.filepath)
        # n.set_path(self.filepath)
        # t = bpy.data.texts.load(self.filepath)
        # n.file_path = t.filepath
        # n.set_path(t.filepath, t.name)
        print("selected file path: ", n.file_path)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(SvPathLoadNode)
    bpy.utils.register_class(SvSomeNodeFileImporterOp)


def unregister():
    bpy.utils.unregister_class(SvSomeNodeFileImporterOp)
    bpy.utils.unregister_class(SvPathLoadNode)
