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
modeItems = [("AB", "a b", ""), ("AE", "a e", ""), ("AC", "a c", "")]


class SvEllipseNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Ellipse '''
    bl_idname = 'SvEllipseNode'
    bl_label = 'Ellipse'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def update_mode(self, context):
        self.updating = True

        if self.mode == "AB":
            if self.lastMode == "AE":
                a = self.major_radius
                e = self.eccentricity
                self.minor_radius = a * sqrt(1 - e * e)
            elif self.lastMode == "AC":
                a = self.major_radius
                c = self.focal_length
                self.minor_radius = sqrt(a * a - c * c)
            else:
                print("no mode change")

        elif self.mode == "AE":
            if self.lastMode == "AB":
                a = self.major_radius
                b = self.minor_radius
                self.eccentricity = sqrt(1 - (b * b) / (a * a))
            if self.lastMode == "AC":
                a = self.major_radius
                c = self.focal_length
                self.eccentricity = c / a
            else:
                print("no mode change")

        elif self.mode == "AC":
            if self.lastMode == "AB":
                a = self.major_radius
                b = self.minor_radius
                self.focal_length = sqrt(a * a - b * b)
            if self.lastMode == "AE":
                a = self.major_radius
                e = self.eccentricity
                self.focal_length = a * e
            else:
                print("no mode change")

        self.updating = False

        self.lastMode = self.mode

        self.update_sockets()
        updateNode(self, context)

    def update_ellipse(self, context):
        if self.updating:
            return

        updateNode(self, context)

    centering = EnumProperty(
        name="Centering", items=centeringItems,
        description="Center the ellipse around F1, C or F2",
        default="C", update=updateNode)

    mode = EnumProperty(
        name="Mode", items=modeItems,
        description="Ellipse definition mode",
        default="AB", update=update_mode)

    lastMode = EnumProperty(
        name="Mode", items=modeItems,
        description="Ellipse definition last mode",
        default="AB")

    major_radius = FloatProperty(
        name='Major Radius', description='Ellipse major radius',
        default=1.0, min=0.0, update=update_ellipse)

    minor_radius = FloatProperty(
        name='Minor Radius', description='Ellipse minor radius',
        default=0.8, min=0.0, update=update_ellipse)

    eccentricity = FloatProperty(
        name='Eccentricity', description='Ellipse eccentricity',
        default=0.6, min=0.0, max=1.0, update=update_ellipse)

    focal_length = FloatProperty(
        name='Focal Length', description='Ellipse focal length',
        default=0.6, min=0.0, update=update_ellipse)

    num_verts = IntProperty(
        name='Num Verts', description='Number of vertices',
        default=36, min=3, update=updateNode)

    phase = FloatProperty(
        name='Phase', description='Phase ellipse points around its center by this radians amount',
        default=0.0, update=updateNode)

    spin = FloatProperty(
        name='Spin', description='Spin ellipse points around selected centering point by this radians amount',
        default=0.0, update=updateNode)

    scale = FloatProperty(
        name='Scale', description='Scale ellipse radii by this amount',
        default=1.0, min=0.0, update=updateNode)

    updating = BoolProperty(default=False)  # used for disabling update callback

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('StringsSocket', "Major Radius").prop_name = "major_radius"
        self.inputs.new('StringsSocket', "Minor Radius").prop_name = "minor_radius"
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
        layout.prop(self, "mode", expand=True)
        layout.prop(self, "centering", expand=True)

    def update_sockets(self):
        if self.mode == "AB":
            socket2 = self.inputs[1]
            socket2.replace_socket("StringsSocket", "Minor Radius").prop_name = "minor_radius"
        elif self.mode == "AE":
            socket2 = self.inputs[1]
            socket2.replace_socket("StringsSocket", "Eccentricity").prop_name = "eccentricity"
        else:  # AC
            socket2 = self.inputs[1]
            socket2.replace_socket("StringsSocket", "Focal Length").prop_name = "focal_length"

    def make_ellipse(self, a, b, N, phase, spin, scale):
        verts = []
        edges = []
        polys = []

        a = a * scale
        b = b * scale

        if a > b:
            dx = sqrt(a * a - b * b)
            dy = 0
        else:
            dx = 0
            dy = sqrt(b * b - a * a)

        if self.centering == "F1":
            cx = -dx
            cy = -dy
        elif self.centering == "F2":
            cx = +dx
            cy = +dy
        else:  # "C"
            cx = 0
            cy = 0

        sins = sin(spin) # cached for performance
        coss = cos(spin) # cached for performance

        f1x = -cx - dx
        f1y = -cy - dy
        f2x = -cx + dx
        f2y = -cy + dy
        f1xx = f1x * coss - f1y * sins
        f1yy = f1x * sins + f1y * coss
        f2xx = f2x * coss - f2y * sins
        f2yy = f2x * sins + f2y * coss

        F1 = [f1xx, f1yy, 0]
        F2 = [f2xx, f2yy, 0]

        for n in range(N):
            theta = 2 * pi * n / N + phase
            x = -cx + a * cos(theta)
            y = -cy + b * sin(theta)
            z = 0
            xx = x * coss - y * sins
            yy = x * sins + y * coss
            verts.append((xx, yy, z))

        edges = list((i, (i + 1) % N) for i in range(N + 1))
        polys = [list(range(N))]

        return verts, edges, polys, F1, F2

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_v1 = inputs[0].sv_get()[0]
        input_v2 = inputs[1].sv_get()[0]
        input_N = inputs["N"].sv_get()[0]
        input_P = inputs["Phase"].sv_get()[0]
        input_S = inputs["Spin"].sv_get()[0]
        input_s = inputs["Scale"].sv_get()[0]

        # convert input parameters to major/minor axis
        if self.mode == "AB":
            input_vv1 = input_v1  # a
            input_vv2 = input_v2  # b
        elif self.mode == "AE":
            input_vv1 = input_v1  # a
            input_va, input_ve = match_long_repeat([input_v1, input_v2])
            input_vv2 = list(map(lambda a, e: a * sqrt(1 - e * e), input_va, input_ve))  # b = a * sqrt(1 - e*e)
        else:  # "AC"
            input_vv1 = input_v1  # a
            input_va, input_vb = match_long_repeat([input_v1, input_v2])
            input_vv2 = list(map(lambda a, b: sqrt(a * a - b * b), input_va, input_vb))  # c = sqrt(a*a - b*b)

        # sanitize the input
        input_vv1 = list(map(lambda x: max(0.0, x), input_vv1))
        input_vv2 = list(map(lambda x: max(0.0, x), input_vv2))
        input_N = list(map(lambda x: max(3, int(x)), input_N))

        parameters = match_long_repeat([input_vv1, input_vv2, input_N, input_P, input_S, input_s])

        vertList = []
        edgeList = []
        polyList = []
        F1List = []
        F2List = []
        for a, b, N, phase, spin, scale in zip(*parameters):
            verts, edges, polys, F1, F2 = self.make_ellipse(a, b, N, phase, spin, scale)
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
