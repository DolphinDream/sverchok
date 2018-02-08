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

typeItems = [("HYPO", "Hypo", ""), ("LINE", "Line", ""), ("EPI", "Epi", "")]


class SvTrochoidNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Trochoid '''
    bl_idname = 'SvTrochoidNode'
    bl_label = 'Trochoid'
    bl_icon = 'OUTLINER_OB_EMPTY'

    tType = EnumProperty(
        name="Type", items=typeItems,
        description="Type of trochoid: Hypo, Line & Epi",
        default="EPI", update=updateNode)

    radius1 = FloatProperty(
        name='Radius1', description='Radius1',
        default=6.0, min=0.0, update=updateNode)

    radius2 = FloatProperty(
        name='Radius2', description='Radius2',
        default=1.0, min=0.0, update=updateNode)

    height = FloatProperty(
        name='Height', description='Height',
        default=5.0, min=0.0, update=updateNode)

    offset1 = FloatProperty(
        name='Offset1', description='Offset1',
        default=0.0, min=0.0, max=1.0, update=updateNode)

    offset2 = FloatProperty(
        name='Offset2', description='Offset2',
        default=0.0, min=0.0, max=1.0, update=updateNode)

    time = FloatProperty(
        name='Time', description='Time',
        default=1.0, min=0.0, update=updateNode)

    closed = BoolProperty(
        name='Closed', description='Closed',
        default=False, update=updateNode)

    swap = BoolProperty(
        name='Swap', description='Swap',
        default=False, update=updateNode)

    num_verts = IntProperty(
        name='Num Verts', description='Number of vertices',
        default=200, min=3, update=updateNode)

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('StringsSocket', "R1", "R1").prop_name = "radius1"
        self.inputs.new('StringsSocket', "R2",  "R2").prop_name = "radius2"
        self.inputs.new('StringsSocket', "H", "H").prop_name = "height"
        self.inputs.new('StringsSocket', "O1", "O1").prop_name = "offset1"
        self.inputs.new('StringsSocket', "O2", "O2").prop_name = "offset2"
        self.inputs.new('StringsSocket', "T", "T").prop_name = "time"
        self.inputs.new('StringsSocket', "N", "N").prop_name = "num_verts"

        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "tType", expand=True)
        row = col.row(align=True)
        row.prop(self, "closed", toggle=True)
        row.prop(self, "swap", toggle=True)

    def make_trochoid(self, R1, R2, H, O1, O2, T, N):
        verts = []
        edges = []

        a, b = [R2, R1] if self.swap else [R1, R2]

        # cache here for performance
        o1 = 2 * pi * O1
        o2 = 2 * pi * O2
        R = a + b  # outer radius
        r = a - b  # inner radius
        Rb = R / b  # outer "gear ratio"
        rb = r / b  # inner "gear ratio"

        if self.tType == "EPI":
            fx = lambda t: R * cos(t + o1) - H * cos(Rb * t + o2)
            fy = lambda t: R * sin(t + o1) - H * sin(Rb * t + o2)
        elif self.tType == "HYPO":
            fx = lambda t: r * cos(t + o1) + H * cos(rb * t + o2)
            fy = lambda t: r * sin(t + o1) - H * sin(rb * t + o2)
        else:  # LINE
            fx = lambda t: a * t - H * sin(t)
            fy = lambda t: a - H * cos(t)

        dT = 2 * pi * T / N

        for n in range(N):
            t = n * dT
            verts.append([fx(t), fy(t), 0])

        edges = list([i, i + 1] for i in range(N - 1))

        if self.closed:
            edges.append([N - 1, 0])

        return verts, edges

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_R1 = inputs["R1"].sv_get()[0]
        input_R2 = inputs["R2"].sv_get()[0]
        input_H = inputs["H"].sv_get()[0]
        input_O1 = inputs["O1"].sv_get()[0]
        input_O2 = inputs["O2"].sv_get()[0]
        input_T = inputs["T"].sv_get()[0]
        input_N = inputs["N"].sv_get()[0]

        # sanitize the inputs
        input_R1 = list(map(lambda x: max(0.0, x), input_R1))
        input_R2 = list(map(lambda x: max(0.0, x), input_R2))
        input_H = list(map(lambda x: max(0.0, x), input_H))
        input_O1 = list(map(lambda x: max(0.0, min(1.0, x)), input_O1))
        input_O2 = list(map(lambda x: max(0.0, min(1.0, x)), input_O2))
        input_T = list(map(lambda x: max(0.0, x), input_T))
        input_N = list(map(lambda x: max(3, int(x)), input_N))

        parameters = match_long_repeat([input_R1, input_R2, input_H, input_O1, input_O2, input_T, input_N])

        vertList = []
        edgeList = []
        for R1, R2, H, O1, O2, T, N in zip(*parameters):
            verts, edges = self.make_trochoid(R1, R2, H, O1, O2, T, N)
            vertList.append(verts)
            edgeList.append(edges)

        outputs["Verts"].sv_set(vertList)
        outputs["Edges"].sv_set(edgeList)


def register():
    bpy.utils.register_class(SvTrochoidNode)


def unregister():
    bpy.utils.unregister_class(SvTrochoidNode)
