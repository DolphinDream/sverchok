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

from math import sin, cos, pi

typeItems = [("HYPO", "Hypo", ""), ("LINE", "Line", ""), ("EPI", "Epi", "")]

# name : [ preset index, type, r1, r2, height, phase1, phase2, turns, resolution, scale ]
trochoidPresets = {
    # some common shapes
    " ":               (0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 1.0),
    # LINE
    "CYCLOID":         (10, "LINE", 1.0, 1.0, 1.0, 0.0, 0.0, 2.0, 200, 0.1),
    "CYCLOID C":       (11, "LINE", 1.0, 1.0, 0.5, 0.0, 0.0, 2.0, 200, 0.1),
    "CYCLOID P":       (12, "LINE", 1.0, 1.0, 2.0, 0.0, 0.0, 2.0, 200, 0.1),
    "EPI CYCLOID":     (13, "EPI", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.5),
    "EPI CYCLOID C":   (14, "EPI", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200, 0.5),
    "EPI CYCLOID P":   (15, "EPI", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200, 0.5),
    "HYPO CYCLOID":    (16, "HYPO", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.5),
    "HYPO CYCLOID C":  (17, "HYPO", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200, 0.5),
    "HYPO CYCLOID P":  (18, "HYPO", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200, 0.5),
    # EPI
    "CARDIOID":        (20, "EPI", 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 1.0),
    "NEPHROID":        (21, "EPI", 2.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 1.0),
    "RANUNCULOID":     (22, "EPI", 5.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.5),
    # HYPO
    "DELTOID":         (30, "HYPO", 3.0, 1.0, 1.0, 0.0, 0.0, 1.0, 300, 1.0),
    "ASTROID":         (31, "HYPO", 4.0, 1.0, 1.0, 0.0, 0.0, 1.0, 300, 0.5),
    # other somewhat interesting EPIs
    "E 6-1-5":         (100, "EPI", 6.0, 1.0, 5.0, 0.0, 0.0, 1.0, 300, 0.2),
    "E 6-3-1":         (101, "EPI", 6.0, 3.0, 1.0, 0.0, 0.0, 1.0, 200, 0.2),
    "E 10-1-9":        (102, "EPI", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500, 0.1),
    "E 12-7-11":       (103, "EPI", 12.0, 7.0, 11.0, 0.0, 0.0, 7.0, 500, 0.1),
    "E 7-2-2":         (104, "EPI", 7.0, 2.0, 2.0, 0.0, 0.0, 2.0, 300, 0.2),
    # other somewhat interesting HYPOs
    "H 6-1-4":         (200, "HYPO", 6.0, 1.0, 4.0, 0.0, 0.0, 1.0, 500, 0.2),
    "H 10-1-9":        (201, "HYPO", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500, 0.1),
    "H 13-6-12":       (202, "HYPO", 13.0, 6.0, 12.0, 0.0, 0.0, 6.0, 200, 0.1),
    "H 1-5-2":         (203, "HYPO", 1.0, 5.0, 2.0, 0.0, 0.0, 5.0, 200, 0.3),
    "H 6-10-5":        (204, "HYPO", 6.0, 10.0, 5.0, 0.0, 0.0, 10.0, 100, 0.3),
}


class SvTrochoidNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Trochoid '''
    bl_idname = 'SvTrochoidNode'
    bl_label = 'Trochoid'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def update_trochoid(self, context):
        if self.updating:
            return

        self.presets = " "
        updateNode(self, context)

    def preset_items(self, context):
        return [(k, k.title(), "", "", s[0]) for k, s in sorted(trochoidPresets.items(), key=lambda k: k[1][0])]

    def update_presets(self, context):
        self.updating = True

        if self.presets == " ":
            self.updating = False
            return

        _, tt, r1, r2, h, p1, p2, T, N, S = trochoidPresets[self.presets]
        self.tType = tt
        self.radius1 = r1
        self.radius2 = r2
        self.height = h
        self.phase1 = p1
        self.phase2 = p2
        self.turns = T
        self.resolution = N
        self.scale = S
        self.swap = False
        self.closed = False if self.tType == "LINE" else True

        self.updating = False
        updateNode(self, context)

    presets = EnumProperty(
        name="Presets", items=preset_items,
        update=update_presets)

    tType = EnumProperty(
        name="Type", items=typeItems,
        description="Type of the trochoid: HYPO, LINE & EPI",
        default="EPI", update=update_trochoid)

    radius1 = FloatProperty(
        name='Radius1', description='Radius of the static circle',
        default=6.0, min=0.0, update=update_trochoid)

    radius2 = FloatProperty(
        name='Radius2', description='Radius of the moving circle',
        default=1.0, min=0.0, update=update_trochoid)

    height = FloatProperty(
        name='Height',
        description='Distance from drawing point to the center of the moving circle',
        default=5.0, min=0.0, update=update_trochoid)

    phase1 = FloatProperty(
        name='Phase1', description='Starting angle for the static circle (radians)',
        default=0.0, update=update_trochoid)

    phase2 = FloatProperty(
        name='Phase2', description='Starting angle for the moving circle (radians)',
        default=0.0, update=update_trochoid)

    turns = FloatProperty(
        name='Turns', description='Number of turns around the static circle',
        default=1.0, min=0.0, update=update_trochoid)

    resolution = IntProperty(
        name='Resolution',
        description='Number of vertices in one full turn around the static circle',
        default=200, min=3, update=update_trochoid)

    scale = FloatProperty(
        name='Scale', description='Scale of the main parameters: radii and height',
        default=1.0, min=0.0, update=update_trochoid)

    closed = BoolProperty(
        name='Closed', description='Close the line',
        default=False, update=update_trochoid)

    swap = BoolProperty(
        name='Swap', description='Swap radii and phases: R1<->R2 and P1<->P2',
        default=False, update=update_trochoid)

    normalize = BoolProperty(
        name='Normalize', description='Scale the curve to fit within normalized size',
        default=False, update=updateNode)

    normalize_size = FloatProperty(
        name='Normalized size', description='Normalized size of the curve',
        default=2.0, min=0.0, update=update_trochoid)

    updating = BoolProperty(default=False)  # used for disabling update callback

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('StringsSocket', "R1", "R1").prop_name = "radius1"
        self.inputs.new('StringsSocket', "R2",  "R2").prop_name = "radius2"
        self.inputs.new('StringsSocket', "H", "H").prop_name = "height"
        self.inputs.new('StringsSocket', "P1", "P1").prop_name = "phase1"
        self.inputs.new('StringsSocket', "P2", "P2").prop_name = "phase2"
        self.inputs.new('StringsSocket', "T", "T").prop_name = "turns"
        self.inputs.new('StringsSocket', "N", "N").prop_name = "resolution"
        self.inputs.new('StringsSocket', "S", "S").prop_name = "scale"

        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'presets')
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "tType", expand=True)
        row = col.row(align=True)
        row.prop(self, "closed", toggle=True)
        row.prop(self, "swap", toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'normalize')
        layout.prop(self, 'normalize_size')

    def make_trochoid(self, R1, R2, H, P1, P2, T, N, S):
        '''
            R1 : radius of the static circle
            R2 : radius of the moving circle
            H  : distance from the point to the center of the moving circle
            P1 : starting angle for the static circle (phase1)
            P2 : starting angle for the moving circle (phase2)
            T  : number of turns around the static circle
            N  : number of vertices in one full turn around the static circle (turn resolution)
            S  : scale the main parameters (radii & height)
        '''
        verts = []
        edges = []

        a, b = [R2, R1] if self.swap else [R1, R2]

        if self.normalize:
            if self.tType == "EPI":
                S = 1/(abs(a+b)+H) * self.normalize_size
            elif self.tType == "HYPO":
                S = 1/(abs(a-b)+H) * self.normalize_size
            else:
                S = 1/(2*pi*a+H) * self.normalize_size

        a = a * S
        b = b * S
        h = H * S

        if self.tType == "EPI":
            R = a + b  # outer radius
            Rb = R / b  # outer "gear ratio"
            fx = lambda t: R * cos(t + P1) - h * cos(Rb * t + P2)
            fy = lambda t: R * sin(t + P1) - h * sin(Rb * t + P2)
        elif self.tType == "HYPO":
            r = a - b  # inner radius
            rb = r / b  # inner "gear ratio"
            fx = lambda t: r * cos(t + P1) + h * cos(rb * t + P2)
            fy = lambda t: r * sin(t + P1) - h * sin(rb * t + P2)
        else:  # LINE
            fx = lambda t: b * t - h * sin(t + P1)
            fy = lambda t: b - h * cos(t + P1)

        N = max(3, int(T * N))  # total number of points in all turns
        dT = 2 * pi * T / N

        for n in range(N + 1):
            t = n * dT
            verts.append([fx(t), fy(t), 0])

        edges = list([i, i + 1] for i in range(N))

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
        input_P1 = inputs["P1"].sv_get()[0]
        input_P2 = inputs["P2"].sv_get()[0]
        input_T = inputs["T"].sv_get()[0]
        input_N = inputs["N"].sv_get()[0]
        input_S = inputs["S"].sv_get()[0]

        # sanitize the inputs
        input_R1 = list(map(lambda x: max(0.0, x), input_R1))
        input_R2 = list(map(lambda x: max(0.0, x), input_R2))
        input_H = list(map(lambda x: max(0.0, x), input_H))
        input_T = list(map(lambda x: max(0.0, x), input_T))
        input_N = list(map(lambda x: max(3, int(x)), input_N))
        input_S = list(map(lambda x: max(0.0, x), input_S))

        parameters = match_long_repeat([input_R1, input_R2, input_H, input_P1, input_P2, input_T, input_N, input_S])

        vertList = []
        edgeList = []
        for R1, R2, H, P1, P2, T, N, S in zip(*parameters):
            verts, edges = self.make_trochoid(R1, R2, H, P1, P2, T, N, S)
            vertList.append(verts)
            edgeList.append(edges)

        outputs["Verts"].sv_set(vertList)
        outputs["Edges"].sv_set(edgeList)


def register():
    bpy.utils.register_class(SvTrochoidNode)


def unregister():
    bpy.utils.unregister_class(SvTrochoidNode)
