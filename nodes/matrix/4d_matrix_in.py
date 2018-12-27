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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

import numpy
from itertools import combinations

m4d_color = (.2, .6, 1, 1)

angleTypes = [
    ("RAD", "Rad", "", 0),   # expects input as radian values
    ("DEG", "Deg", "", 1),   # expects input as degree values
    ("NORM", "Norm", "", 2)]  # expects input as 0-1 values


def get_T_matrix(t):
    """
    Return the 5D Translation matrix given the 4D translation vector.
    """
    T = numpy.matrix(numpy.identity(5))
    for i in range(4):
        T[i, 4] = t[i]
    return T


def get_S_matrix(s):
    """
    Return the 5D Scale matrix given the 4D scale vector.
    """
    S = numpy.matrix(numpy.identity(5))
    for i in range(4):
        S[i, i] = s[i]
    return S


def get_R_matrix(a1=0, a2=0, a3=0, a4=0, a5=0, a6=0):
    """
    Return the 5D Rotation matrix given the 6 rotation angles.
    """
    angles = [a1, a2, a3, a4, a5, a6]
    R = numpy.matrix(numpy.identity(5))
    for (i, j), a in zip(combinations(range(4), 2), angles):
        rot = numpy.mat(numpy.identity(5))
        rot[i, i] = cos(a)
        rot[j, j] = cos(a)
        rot[i, j] = -sin(a)
        rot[j, i] = sin(a)
        R = R * rot
    return R

def get_composite_matrix(a1, a2, a3, a4, a5, a6, s, t):
    """
    Return the 4D(5D) composite matrix T * R * S given the rotation angles
    the 4D translation and the 4D scale.
    """
    T = get_T_matrix(t)
    R = get_R_matrix(a1, a2, a3, a4, a5, a6)
    S = get_S_matrix(s)
    m = T * R * S
    return m


class Sv4DMatrixInNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 4D Matrix In
    Tooltip: Generate a 4D (5D) matrix to transform 4D points
    """
    bl_idname = 'Sv4DMatrixInNode'
    bl_label = '4D Matrix In'

    def update_angle(self, context):
        if self.syncing:
            return
        updateNode(self, context)

    def update_mode(self, context):
        """
        Update angle values when switching mode to keep the same radian values
        """
        if self.lastAngleType == self.angleType:
            return

        if self.lastAngleType == "RAD":
            if self.angleType == "DEG":
                aU = 180 / pi
            elif self.angleType == "NORM":
                aU = 1 / (2 * pi)

        elif self.lastAngleType == "DEG":
            if self.angleType == "RAD":
                aU = pi / 180
            elif self.angleType == "NORM":
                aU = 1 / 360

        elif self.lastAngleType == "NORM":
            if self.angleType == "RAD":
                aU = 2 * pi
            elif self.angleType == "DEG":
                aU = 360
        self.lastAngleType = self.angleType

        self.syncing = True
        self.angle_a1 *= aU
        self.angle_a2 *= aU
        self.angle_a3 *= aU
        self.angle_a4 *= aU
        self.angle_a5 *= aU
        self.angle_a6 *= aU
        self.syncing = False

        updateNode(self, context)

    angleType = EnumProperty(
        name="Angle Type", description="Angle units",
        default="NORM", items=angleTypes, update=update_mode)

    lastAngleType = EnumProperty(
        name="Last Angle Type", description="Last angle units",
        default="NORM", items=angleTypes)

    angle_a1 = FloatProperty(
        name="XY", description="Angle 1",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a2 = FloatProperty(
        name="XZ", description="Angle 2",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a3 = FloatProperty(
        name="XW", description="Angle 3",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a4 = FloatProperty(
        name="YZ", description="Angle 4",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a5 = FloatProperty(
        name="YW", description="Angle 5",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a6 = FloatProperty(
        name="ZW", description="Angle 6",
        default=0.0, min=0.0,
        update=update_angle)

    scale = FloatVectorProperty(
        size=4,
        name="Scale", description="Scale in 4D space",
        default=(1, 1, 1, 1),
        subtype="QUATERNION",
        update=updateNode)

    translate = FloatVectorProperty(
        size=4,
        name="Translate", description="Translate in 4D space",
        default=(0, 0, 0, 0),
        subtype="QUATERNION",
        update=updateNode)

    syncing = BoolProperty(
        name='Syncing', description='Syncing flag', default=False)

    def sv_init(self, context):
        # self.width = 160
        self.inputs.new('StringsSocket', "A1").prop_name = 'angle_a1'
        self.inputs.new('StringsSocket', "A2").prop_name = 'angle_a2'
        self.inputs.new('StringsSocket', "A3").prop_name = 'angle_a3'
        self.inputs.new('StringsSocket', "A4").prop_name = 'angle_a4'
        self.inputs.new('StringsSocket', "A5").prop_name = 'angle_a5'
        self.inputs.new('StringsSocket', "A6").prop_name = 'angle_a6'
        self.inputs.new('SvQuaternionSocket', "Scale").prop_name = 'scale'
        self.inputs.new('SvQuaternionSocket', "Translate").prop_name = 'translate'

        self.outputs.new('StringsSocket', "Matrix").nodule_color = m4d_color

    def draw_buttons(self, context, layout):
        layout.prop(self, 'angleType', expand=True)


    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        # input values lists
        inputs = self.inputs
        input_a1 = inputs["A1"].sv_get()[0]
        input_a2 = inputs["A2"].sv_get()[0]
        input_a3 = inputs["A3"].sv_get()[0]
        input_a4 = inputs["A4"].sv_get()[0]
        input_a5 = inputs["A5"].sv_get()[0]
        input_a6 = inputs["A6"].sv_get()[0]

        input_s = inputs["Scale"].sv_get()[0]
        input_t = inputs["Translate"].sv_get()[0]

        # convert everything to radians
        if self.angleType == "DEG":
            aU = pi / 180
        elif self.angleType == "RAD":
            aU = 1
        else:
            aU = 2 * pi

        params = match_long_repeat([input_a1, input_a2, input_a3,
                                    input_a4, input_a5, input_a6,
                                    input_s, input_t])

        matrixList = []
        for a1, a2, a3, a4, a5, a6, s, t in zip(*params):
            a1 *= aU
            a2 *= aU
            a3 *= aU
            a4 *= aU
            a5 *= aU
            a6 *= aU
            m = get_composite_matrix(a1, a2, a3, a4, a5, a6, s, t)
            M = m.tolist()
            matrixList.append(M)

        outputs['Matrix'].sv_set(matrixList)


def register():
    bpy.utils.register_class(Sv4DMatrixInNode)


def unregister():
    bpy.utils.unregister_class(Sv4DMatrixInNode)

'''
    # list(map("".join, combinations(list("XYZW"), 2)))
    # list(map("".join, combinations(list("0123"), 2)))
'''

