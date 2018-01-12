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

centeringItems = [("F1", "F1", ""), ("C", "C", ""), ("F2", "F2", "")]
# directionItems = [("X", "X", ""), ("Y", "Y", ""), ("Z", "Z", "")]


class SvEllipseNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Ellipse '''
    bl_idname = 'SvEllipseNode'
    bl_label = 'Ellipse'
    bl_icon = 'OUTLINER_OB_EMPTY'

    centering = EnumProperty(
        name="Centering", items=centeringItems,
        description="Center the ellipse around F1, C or F2",
        default="C", update=updateNode)

    minor_radius = FloatProperty(
        name='Minor Radius', description='Minor radius of the ellipse',
        default=1.0, min=0.0, update=updateNode)

    major_radius = FloatProperty(
        name='Major Radius', description='Major radius of the ellipse',
        default=2.0, min=0.0, update=updateNode)

    num_verts = IntProperty(
        name='Num Verts', description='Number of vertices',
        default=24, min=3, update=updateNode)

    phase = FloatProperty(
        name='Phase', description='Ellipse phase',
        default=0.0, update=updateNode)

    spin = FloatProperty(
        name='Spin', description='Ellipse spin',
        default=0.0, update=updateNode)

    scale = FloatProperty(
        name='Scale', description='Ellipse scale',
        default=1.0, min=0.0, update=updateNode)

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('StringsSocket', "Rx", "Rx").prop_name = "major_radius"
        self.inputs.new('StringsSocket', "Ry", "Ry").prop_name = "minor_radius"
        self.inputs.new('StringsSocket', "N", "N").prop_name = "num_verts"
        self.inputs.new('StringsSocket', "Phase").prop_name = "phase"
        self.inputs.new('StringsSocket', "Spin").prop_name = "spin"
        self.inputs.new('StringsSocket', "Scale").prop_name = "scale"

        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polys", "Polys")

        self.outputs.new('VerticesSocket', "F1", "F1")
        self.outputs.new('VerticesSocket', "F2", "F2")

    def draw_buttons(self, context, layout):
        layout.prop(self, "centering", expand=True)

    def make_ellipse(self, Rx, Ry, N, phase, spin, scale):
        verts = []
        edges = []
        polys = []

        Rx = Rx * scale
        Ry = Ry * scale

        if Rx > Ry:
            dx = sqrt(Rx * Rx - Ry * Ry)
            dy = 0
        else:
            dx = 0
            dy = sqrt(Ry * Ry - Rx * Rx)

        if self.centering == "F1":
            cx = -dx
            cy = -dy
        elif self.centering == "F2":
            cx = +dx
            cy = +dy
        else:  # "C"
            cx = 0
            cy = 0

        sins = sin(spin)
        coss = cos(spin)

        f1x = -cx - dx
        f1y = -cy - dy
        f1xx = f1x * coss - f1y * sins
        f1yy = f1x * sins + f1y * coss
        f2x = -cx + dx
        f2y = -cy + dy
        f2xx = f2x * coss - f2y * sins
        f2yy = f2x * sins + f2y * coss

        F1 = [f1xx, f1yy, 0]
        F2 = [f2xx, f2yy, 0]

        for n in range(N):
            a = 2 * pi * n / N + phase
            x = -cx + Rx * cos(a)
            y = -cy + Ry * sin(a)
            z = 0
            xx = x * coss - y * sins
            yy = x * sins + y * coss
            verts.append([xx, yy, z])

        edges = list([i, (i + 1) % N] for i in range(N + 1))
        polys = list(range(N))

        return verts, edges, polys, F1, F2

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_Rx = inputs["Rx"].sv_get()[0]
        input_Ry = inputs["Ry"].sv_get()[0]
        input_N = inputs["N"].sv_get()[0]
        input_P = inputs["Phase"].sv_get()[0]
        input_S = inputs["Spin"].sv_get()[0]
        input_s = inputs["Scale"].sv_get()[0]

        # sanitize the input
        input_Rx = list(map(lambda x: max(0.0, x), input_Rx))
        input_Ry = list(map(lambda x: max(0.0, x), input_Ry))
        input_N = list(map(lambda x: max(3, int(x)), input_N))

        parameters = match_long_repeat([input_Rx, input_Ry, input_N, input_P, input_S, input_s])

        vertList = []
        edgeList = []
        polyList = []
        F1List = []
        F2List = []
        for Rx, Ry, N, phase, spin, scale in zip(*parameters):
            verts, edges, polys, F1, F2 = self.make_ellipse(Rx, Ry, N, phase, spin, scale)
            vertList.append(verts)
            edgeList.append(edges)
            polyList.append(polys)
            F1List.append(F1)
            F2List.append(F2)

        outputs["Verts"].sv_set(vertList)
        outputs["Edges"].sv_set(edgeList)
        outputs["Polys"].sv_set(polyList)

        outputs["F1"].sv_set([F1List])
        outputs["F2"].sv_set([F2List])


def register():
    bpy.utils.register_class(SvEllipseNode)


def unregister():
    bpy.utils.unregister_class(SvEllipseNode)
