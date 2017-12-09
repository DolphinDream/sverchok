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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty

from math import sin, cos, pi, sqrt, radians
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

import numpy

m4d_color = (.2, .6, 1, 1)


def transform_verts(verts4D, m):
    # transform vectors from 4D to 5D
    V = [numpy.matrix([list(v) + [1]]) for v in verts4D]
    #
    W = [m * (v.T) for v in V]
    #
    K = [w.T.tolist()[0][:-1] for w in W]
    #
    #
    # print("C=", C)
    # print("T=", T)
    # print("R=", R)
    # print("S=", S)
    # print("L=", L)
    # print("K=", K)
    # print("V=", V)
    # print("W=", W)
    # print("m=", m)
    # return L
    # return K
    return K


class Sv4DTransformNode(bpy.types.Node, SverchCustomTreeNode):
    ''' 4D Transform '''
    bl_idname = 'Sv4DTransformNode'
    bl_label = '4D Transform'

    def sv_init(self, context):
        # self.width = 160
        self.inputs.new('VerticesSocket', "Verts")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Polys")

        self.inputs.new('StringsSocket', "Matrix").nodule_color = m4d_color

        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polys")

    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        # input values lists
        inputs = self.inputs
        input_v = inputs["Verts"].sv_get()
        input_e = inputs["Edges"].sv_get()
        input_p = inputs["Polys"].sv_get()

        input_m = inputs["Matrix"].sv_get()

        params = match_long_repeat([input_v, input_e, input_p, input_m])

        vertList = []
        edgeList = []
        polyList = []
        for v, e, p, m in zip(*params):
            verts = transform_verts(v, m)
            vertList.append(verts)
            edgeList.append(e)
            polyList.append(p)

        outputs['Verts'].sv_set(vertList)
        outputs['Edges'].sv_set(edgeList)
        outputs['Polys'].sv_set(polyList)


def register():
    bpy.utils.register_class(Sv4DTransformNode)


def unregister():
    bpy.utils.unregister_class(Sv4DTransformNode)
