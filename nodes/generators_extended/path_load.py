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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from math import sin, cos, pi, sqrt, radians
from random import random
import time
import mmap

from mathutils import Quaternion

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

def load_path(filepath):
    ## the QMAT file format is :
    #
    # numEntries
    # x y z  x y z w
    # x y z  x y z w
    # ...
    # homeDir = "/home/marius/Downloads/"
    homeDir = "/Users/atokirina/Downloads/"
    filepath = homeDir + filepath
    print("loading path: ", filepath)

    with open(filepath, 'rb') as file:
        # check http://bugs.python.org/issue8046 to have mmap context
        # manager fixed in python
        data = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        #yield data
        #data.close()

        verts, quats = [], []

        # read the number of locations
        nl = int(data.readline().rstrip())
        # read the vertex coordinates for all vertices
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

        print("QMAT file has %d entries" % (nl))

        return verts, quats


class SvPathLoadNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Load Path from file in vector (3) + quaternion (4) format '''
    bl_idname = 'SvPathLoadNode'
    bl_label = 'Load Path'
    # sv_icon = 'SV_SPLIT_EDGES'

    def sv_init(self, context):

        self.outputs.new('SvVerticesSocket',  "Vertices")
        self.outputs.new('SvQuaternionSocket',  "Quaternions")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mirror')

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        file_name = "path_size4_barrel_j2xr_distal.qmat"
        vertex_list, quaternion_list = load_path(file_name)

        self.outputs['Vertices'].sv_set([vertex_list])
        self.outputs['Quaternions'].sv_set(quaternion_list)


def register():
    bpy.utils.register_class(SvPathLoadNode)


def unregister():
    bpy.utils.unregister_class(SvPathLoadNode)
