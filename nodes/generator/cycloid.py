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
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (match_long_repeat, updateNode)

from math import sin, cos, pi, sqrt
import time

centeringItems = [("P1", "P1", ""), ("P2", "P2", "")]


class SvCycloidNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Cycloid '''
    bl_idname = 'SvCycloidNode'
    bl_label = 'Cycloid'
    bl_icon = 'OUTLINER_OB_EMPTY'

    centering = EnumProperty(
        name="Centering", items=centeringItems,
        description="Center the path around P1 or P2",
        default="P1", update=updateNode)

    radius1 = FloatProperty(
        name='Radius1', description='Radius1',
        default=10.0, min=0.0, update=updateNode)

    radius2 = FloatProperty(
        name='Radius2', description='Radius2',
        default=2.0, min=0.0, update=updateNode)

    period1 = FloatProperty(
        name='Period1', description='Period1',
        default=11.0, min=0.0, update=updateNode)

    period2 = FloatProperty(
        name='Period2', description='Period2',
        default=1.0, min=0.0, update=updateNode)

    offset1 = FloatProperty(
        name='Offset1', description='Offset1',
        default=0.0, min=0.0, max=1.0, update=updateNode)

    offset2 = FloatProperty(
        name='Offset2', description='Offset2',
        default=0.0, min=0.0, max=1.0, update=updateNode)

    time = FloatProperty(
        name='Time', description='Time',
        default=11.0, min=0.0, update=updateNode)

    num_verts = IntProperty(
        name='Num Verts', description='Number of vertices',
        default=200, min=3, update=updateNode)

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('StringsSocket', "R1", "R1").prop_name = "radius1"
        self.inputs.new('StringsSocket', "R2", "R2").prop_name = "radius2"
        self.inputs.new('StringsSocket', "T1", "T1").prop_name = "period1"
        self.inputs.new('StringsSocket', "T2", "T2").prop_name = "period2"
        self.inputs.new('StringsSocket', "O1", "O1").prop_name = "offset1"
        self.inputs.new('StringsSocket', "O2", "O2").prop_name = "offset2"
        self.inputs.new('StringsSocket', "T", "T").prop_name = "time"
        self.inputs.new('StringsSocket', "N", "N").prop_name = "num_verts"

        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        layout.prop(self, "centering", expand=True)

    def make_cycloid(self, R1, R2, T1, T2, O1, O2, T, N):
        verts = []
        edges = []

        if self.centering == "P2":  # swap values
            R1, R2 = R2, R1
            T1, T2 = T2, T1
            O1, O2 = O2, O1

        dT = T / N
        dA1 = 2 * pi / T1
        dA2 = 2 * pi / T2
        o1 = T1 * O1
        o2 = T2 * O2
        for n in range(N):
            t = n * dT
            a1 = (t + o1) * dA1
            a2 = (t + o2) * dA2
            x = R2 * cos(a2) - R1 * cos(a1)
            y = R2 * sin(a2) - R1 * sin(a1)
            z = 0
            verts.append([x, y, z])

        # edges = list([i, (i + 1) % N] for i in range(N + 1))
        edges = list([i, i + 1] for i in range(N))

        return verts, edges

    def process(self):
        t0 = time.time()

        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_R1 = inputs["R1"].sv_get()[0]
        input_R2 = inputs["R2"].sv_get()[0]
        input_T1 = inputs["T1"].sv_get()[0]
        input_T2 = inputs["T2"].sv_get()[0]
        input_O1 = inputs["O1"].sv_get()[0]
        input_O2 = inputs["O2"].sv_get()[0]
        input_T = inputs["T"].sv_get()[0]
        input_N = inputs["N"].sv_get()[0]

        t1 = time.time()

        # sanitize the inputs
        input_R1 = list(map(lambda x: max(0.0, x), input_R1))
        input_R2 = list(map(lambda x: max(0.0, x), input_R2))
        input_T1 = list(map(lambda x: max(0.0, x), input_T1))
        input_T2 = list(map(lambda x: max(0.0, x), input_T2))
        input_O1 = list(map(lambda x: max(0.0, min(1.0, x)), input_O1))
        input_O2 = list(map(lambda x: max(0.0, min(1.0, x)), input_O2))
        input_T = list(map(lambda x: max(0.0, x), input_T))
        input_N = list(map(lambda x: max(3, int(x)), input_N))

        t2 = time.time()

        parameters = match_long_repeat([input_R1, input_R2, input_T1, input_T2, input_O1, input_O2, input_T, input_N])

        t3 = time.time()

        vertList = []
        edgeList = []
        for R1, R2, T1, T2, O1, O2, T, N in zip(*parameters):
            verts, edges = self.make_cycloid(R1, R2, T1, T2, O1, O2, T, N)
            vertList.append(verts)
            edgeList.append(edges)

        t4 = time.time()

        outputs["Verts"].sv_set(vertList)
        outputs["Edges"].sv_set(edgeList)

        t5 = time.time()

        print("Time Statistics:")
        print("dT1 = ", t2 - t1)
        print("dT2 = ", t3 - t2)
        print("dT3 = ", t4 - t3)
        print("dT4 = ", t5 - t4)
        print("dT = ", t5 - t0)


def register():
    bpy.utils.register_class(SvCycloidNode)


def unregister():
    bpy.utils.unregister_class(SvCycloidNode)
