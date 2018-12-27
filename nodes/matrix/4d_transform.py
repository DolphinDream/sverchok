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

from pprint import pprint

m4d_color = (.2, .6, 1, 1)

idMat4D = [numpy.matrix(numpy.identity(5))]


def transform_verts(verts4D, m):
    # convert vectors from 4D to 5D
    # print("verts4D=", verts4D)
    print("m=", m)
    m = numpy.matrix(m)
    V = [numpy.matrix([list(v) + [1]]) for v in verts4D]
    # transform 4D(5D) vector by 4D(5D) matrix
    W = [m * (v.T) for v in V]
    # convert vectors from 5D to 4D
    K = [w.T.tolist()[0][:-1] for w in W]

    #
    # print("C=", C)
    # print("T=", T)
    # print("R=", R)
    # print("S=", S)
    # print("L=", L)
    # print("m=", m)
    # print("V=", V)
    # print("W=", W)
    # print("K=", K)
    # return L
    # return K
    return K


class Sv4DTransformNode(bpy.types.Node, SverchCustomTreeNode):
    ''' 4D Transform '''
    bl_idname = 'Sv4DTransformNode'
    bl_label = '4D Transform'

    def sv_init(self, context):
        # self.width = 160
        self.inputs.new('SvQuaternionSocket', "Quaternion")
        # self.inputs.new('StringsSocket', "Edges")
        # self.inputs.new('StringsSocket', "Polys")

        self.inputs.new('StringsSocket', "4D Matrix").nodule_color = m4d_color

        self.outputs.new('SvQuaternionSocket', "Quaternion")
        # self.outputs.new('StringsSocket', "Edges")
        # self.outputs.new('StringsSocket', "Polys")

    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        # input values lists
        inputs = self.inputs

        # no 4D verts ? => nothing to transform
        if not inputs["Quaternion"].is_linked:
            return

        input_v = inputs["Quaternion"].sv_get()
        # input_v = [list(v) for v in input_v] # convert quaternions to lists
        # print("v=", input_v)
        # input_e = inputs["Edges"].sv_get()
        # print("e=", input_e)
        # input_p = inputs["Polys"].sv_get()[0]
        # print("p=", input_p)
        input_m = inputs["4D Matrix"].sv_get(default=idMat4D)
        # input_m = [numpy.matrix(m) for m in input_m]
        # print("m=", input_m)

        params = match_long_repeat([input_v, input_m])
        # params = match_long_repeat([input_v, input_e, input_p, input_m])

        # print("input_m=")
        # pprint(input_m)

        # print("mm=")
        # pprint(mm)
        # print("idMat = ")
        # pprint(idMat4D)
        # print(type(idMat4D))

        vertList = []
        # edgeList = []
        # polyList = []
        # for v, e, p, m in zip(*params):
        for v, m in zip(*params):
            # print("matrix = ", m)
            # verts = transform_verts(v, numpy.matrix(m))
            verts = transform_verts(v, m)
            vertList.append(verts)
            # edgeList.append(e)
            # polyList.append(p)

        if outputs['Quaternion'].is_linked:
            outputs['Quaternion'].sv_set(vertList)
        # if outputs['Edges'].is_linked:
        #     outputs['Edges'].sv_set(edgeList)
        # if outputs['Polys'].is_linked:
        #     outputs['Polys'].sv_set(polyList)


def register():
    bpy.utils.register_class(Sv4DTransformNode)


def unregister():
    bpy.utils.unregister_class(Sv4DTransformNode)
