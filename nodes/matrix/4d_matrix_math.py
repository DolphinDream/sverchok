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

import numpy
from functools import reduce

from sverchok.node_tree import SverchCustomTreeNode, MatrixSocket, StringsSocket
from sverchok.data_structure import (updateNode, match_long_repeat)

operationItems = [
    ("MULTIPLY", "Multiply", "Multiply two or more matrices", 0),
    ("INVERT", "Invert", "Invert matrix", 1),
    ("FILTER", "Filter", "Filter matrix components", 2),
    ("BASIS", "Basis", "Extract Basis vectors", 3)
]

prePostItems = [
    ("PRE", "Pre", "Calculate A op B", 0),
    ("POST", "Post", "Calculate B op A", 1)
]

m4d_color = (.2, .6, 1, 1)
id_mat = numpy.mat(numpy.identity(5)).tolist()
ABC = tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')


def decompose_4d_matrix(m):
    '''
        Decompose a 4D(5D) homogeneous matrix into its T, R, S components
    '''
    T = numpy.matrix(numpy.identity(5))
    for i in range(4):
        T[i, 4] = m[i, 4]

    S = numpy.matrix(numpy.identity(5))
    for i in range(4):
        S[i, i] = numpy.linalg.norm(m[:-1,i])

    R = numpy.matrix(numpy.identity(5))
    for i in range(4):
        for j in range(4):
            R[i, j] = m[i, j] / S[i, i]

    return T, R, S


class Sv4DMatrixMathNode(bpy.types.Node, SverchCustomTreeNode):
    ''' 4D Math operation on matrices '''
    bl_idname = 'Sv4DMatrixMathNode'
    bl_label = '4D Matrix Math'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def update_operation(self, context):
        self.label = "4D Matrix " + self.operation.title()
        self.update_sockets()
        updateNode(self, context)

    prePost = EnumProperty(
        name='Pre Post',
        description='Order of operations PRE = A op B vs POST = B op A)',
        items=prePostItems, default="PRE", update=updateNode)

    operation = EnumProperty(
        name="Operation",
        description="Operation to apply on the given matrices",
        items=operationItems, default="MULTIPLY", update=update_operation)

    filter_t = BoolProperty(
        name="Filter Translation",
        description="Filter out the translation component of the matrix",
        default=False, update=updateNode)

    filter_r = BoolProperty(
        name="Filter Rotation",
        description="Filter out the rotation component of the matrix",
        default=False, update=updateNode)

    filter_s = BoolProperty(
        name="Filter Scale",
        description="Filter out the scale component of the matrix",
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "A", "A").nodule_color = m4d_color
        self.inputs.new('StringsSocket', "B", "B").nodule_color = m4d_color

        self.outputs.new('StringsSocket', "C", "C").nodule_color = m4d_color

        self.outputs.new('VerticesSocket', "X", "X")
        self.outputs.new('VerticesSocket', "Y", "Y")
        self.outputs.new('VerticesSocket', "Z", "Z")
        self.outputs.new('VerticesSocket', "W", "W")

        self.operation = "MULTIPLY"

    def update_sockets(self):
        # update inputs
        inputs = self.inputs
        if self.operation in {"MULTIPLY"}:  # multiple input operations
            if len(inputs) < 2:  # at least two matrix inputs are available
                if not "B" in inputs:
                    inputs.new("StringsSocket", "B").nodule_color = m4d_color
        else:  # single input operations (remove all inputs except the first one)
            ss = [s for s in inputs]
            for s in ss:
                if s != inputs["A"]:
                    inputs.remove(s)

        # update outputs
        outputs = self.outputs
        if self.operation == "BASIS":
            for name in list("XYZW"):
                if name not in outputs:
                    outputs.new("VerticesSocket", name)
        else:  # remove basis output sockets for all other operations
            for name in list("XYZW"):
                if name in outputs:
                    outputs.remove(outputs[name])

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")
        if self.operation == "MULTIPLY":
            layout.prop(self, "prePost", expand=True)
        elif self.operation == "FILTER":
            row = layout.row(align=True)
            row.prop(self, "filter_t", toggle=True, text="T")
            row.prop(self, "filter_r", toggle=True, text="R")
            row.prop(self, "filter_s", toggle=True, text="S")

    def operation_filter(self, a):
        T, R, S = decompose_4d_matrix(a)

        if self.filter_t:
            T = numpy.mat((numpy.identity(5)))

        if self.filter_r:
            R = numpy.mat((numpy.identity(5)))

        if self.filter_s:
            S = numpy.mat((numpy.identity(5)))

        m = T * R * S

        return m

    def operation_basis(self, a):
        T, R, S = decompose_4d_matrix(a)

        Rx = (R[0, 0], R[1, 0], R[2, 0], R[3, 0])
        Ry = (R[0, 1], R[1, 1], R[2, 1], R[3, 1])
        Rz = (R[0, 2], R[1, 2], R[2, 2], R[3, 2])
        Rw = (R[0, 3], R[1, 3], R[2, 3], R[3, 3])

        return Rx, Ry, Rz, Rw

    def get_operation(self):
        if self.operation == "MULTIPLY":
            return lambda l: reduce((lambda a, b: a * b), l)
        elif self.operation == "FILTER":
            return self.operation_filter
        elif self.operation == "INVERT":
            return lambda a: a.I
        elif self.operation == "BASIS":
            return self.operation_basis

    def update(self):
        # sigle input operation ? => no need to update sockets
        if self.operation not in {"MULTIPLY"}:
            return

        # multiple input operation ? => add an empty last socket
        inputs = self.inputs
        if inputs[-1].links:
            name = ABC[len(inputs)]  # pick the next letter A to Z
            inputs.new("StringsSocket", name).nodule_color = m4d_color
        else:  # last input disconnected ? => remove all but last unconnected extra inputs
            while len(inputs) > 2 and not inputs[-2].links:
                inputs.remove(inputs[-1])

    def process(self):
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        I = []  # collect the inputs from the connected sockets
        for s in filter(lambda s: s.is_linked, self.inputs):
            I.append([numpy.mat(m) for m in s.sv_get(default=id_mat)])

        operation = self.get_operation()

        if self.operation in {"MULTIPLY"}:  # multiple input operations
            if self.prePost == "PRE":  # A op B : keep input order
                parameters = match_long_repeat(I)
            else:  # B op A : reverse input order
                parameters = match_long_repeat(I[::-1])

            matrixList = [operation(params) for params in zip(*parameters)]

            matrices = [m.tolist() for m in matrixList]
            outputs['C'].sv_set(matrices)

        else:  # single input operations
            parameters = I[0]
            print("parameters=", parameters)

            if self.operation == "BASIS":
                xList = []
                yList = []
                zList = []
                wList = []
                for a in parameters:
                    Rx, Ry, Rz, Rw = operation(a)
                    xList.append(Rx)
                    yList.append(Ry)
                    zList.append(Rz)
                    wList.append(Rw)
                outputs['X'].sv_set(xList)
                outputs['Y'].sv_set(yList)
                outputs['Z'].sv_set(zList)
                outputs['W'].sv_set(wList)

                matrices = [m.tolist() for m in parameters]
                outputs['C'].sv_set(matrices)

            else:  # INVERSE / FILTER
                matrixList = [operation(a) for a in parameters]

                matrices = [m.tolist() for m in matrixList]
                outputs['C'].sv_set(matrices)


def register():
    bpy.utils.register_class(Sv4DMatrixMathNode)


def unregister():
    bpy.utils.unregister_class(Sv4DMatrixMathNode)
