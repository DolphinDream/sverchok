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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

def read_sur(filepath):
    ## the SUR file format is :
    # numVertices
    # x y z
    # x y z
    # ...
    # numTriangles
    # id1 id2 id3
    # id1 id2 id3
    # ...

    with open(filepath, 'rb') as file:
        # check http://bugs.python.org/issue8046 to have mmap context
        # manager fixed in python
        data = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        #yield data
        #data.close()

        verts, quaternion = [], []

        # read the number of vertices
        nv = int(data.readline().rstrip())
        # read the vertex coordinates for all vertices
        for i in range(nv):
            line = data.readline().rstrip()
            v = list(map(float, line.split()))
            verts.append(v)

        # read the number of faces
        nf = int(data.readline().rstrip())
        # read the face's vertex indices for all faces
        for i in range(nf):
            line = data.readline().rstrip()
            t = list(map(int, line.split()))
            faces.append(t)

        print("SUR file has %d verts and %d faces" %(nv, nf))

        return verts, faces, norms



def load_path(file_path):
    # open file
    # read content (vertex + quaternion)
    # convert vertex + quaternion => matrix
    return [[0,0,0], [1,1,1,1]]

    # return matrices (location + rotation)
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

        vertex_list, quaternion_list = load_path()

        self.outputs['Vertices'].sv_set([vertex_list])
        self.outputs['Quaternions'].sv_set([quaternion_list])


def register():
    bpy.utils.register_class(SvPathLoadNode)


def unregister():
    bpy.utils.unregister_class(SvPathLoadNode)
