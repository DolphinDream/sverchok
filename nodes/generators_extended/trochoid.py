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

epsilon = 1e-5  # used to avoid division by zero

typeItems = [("HYPO", "Hypo", ""), ("LINE", "Line", ""), ("EPI", "Epi", "")]

# name : [ preset index, type, r1, r2, height, phase1, phase2, turns, resolution, scale ]
trochoidPresets = {
    " ":                    (0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 1.0),
    # SAMPLE of ALL TYPES
    "CYCLOID":              (10, "LINE", 1.0, 1.0, 1.0, 0.0, 0.0, 3.0, 200, 0.1),
    "CURTATE CYCLOID":      (11, "LINE", 1.0, 1.0, 0.5, 0.0, 0.0, 3.0, 200, 0.1),
    "PROLATE CYCLOID":      (12, "LINE", 1.0, 1.0, 2.0, 0.0, 0.0, 3.0, 200, 0.1),
    "EPI-CYCLOID":          (13, "EPI", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.11),
    "CURTATE EPI-CYCLOID":  (14, "EPI", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200, 0.12),
    "PROLATE EPI-CYCLOID":  (15, "EPI", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200, 0.1),
    "HYPO CYCLOID":         (16, "HYPO", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.15),
    "CURTATE HYPO-CYCLOID": (17, "HYPO", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200, 0.15),
    "PROLATE HYPO-CYCLOID": (18, "HYPO", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200, 0.12),
    # EPIs
    "CARDIOID":             (20, "EPI", 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.4),
    "NEPHROID":             (21, "EPI", 2.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.25),
    "RANUNCULOID":          (22, "EPI", 5.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200, 0.15),
    # HYPOs
    "DELTOID":              (30, "HYPO", 3.0, 1.0, 1.0, 0.0, 0.0, 1.0, 300, 0.4),
    "ASTROID":              (31, "HYPO", 4.0, 1.0, 1.0, 0.0, 0.0, 1.0, 300, 0.25),
    "ROSETTE":              (32, "HYPO", 6.0, 1.0, 5.0, 0.0, 0.0, 1.0, 300, 0.11),
    # other somewhat interesting EPIs
    "E 6-1-5":              (100, "EPI", 6.0, 1.0, 5.0, 0.0, 0.0, 1.0, 300, 0.08),
    "E 6-3-1":              (101, "EPI", 6.0, 3.0, 1.0, 0.0, 0.0, 1.0, 200, 0.1),
    "E 10-1-9":             (102, "EPI", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500, 0.05),
    "E 12-7-11":            (103, "EPI", 12.0, 7.0, 11.0, 0.0, 0.0, 7.0, 500, 0.03),
    "E 7-2-2":              (104, "EPI", 7.0, 2.0, 2.0, 0.0, 0.0, 2.0, 300, 0.09),
    # other somewhat interesting HYPOs
    "H 6-1-4":              (200, "HYPO", 6.0, 1.0, 4.0, 0.0, 0.0, 1.0, 500, 0.11),
    "H 10-1-9":             (201, "HYPO", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500, 0.06),
    "H 13-6-12":            (202, "HYPO", 13.0, 6.0, 12.0, 0.0, 0.0, 6.0, 200, 0.05),
    "H 1-5-2":              (203, "HYPO", 1.0, 5.0, 2.0, 0.0, 0.0, 5.0, 200, 0.16),
    "H 6-10-5":             (204, "HYPO", 6.0, 10.0, 5.0, 0.0, 0.0, 10.0, 100, 0.11),
}


class SvTrochoidNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Trochoid '''
    bl_idname = 'SvTrochoidNode'
    bl_label = 'Trochoid'
    sv_icon = 'SV_TROCHOID'

    def update_normalize(self, context):
        self.update_sockets()
        updateNode(self, context)

    def update_trochoid(self, context):
        if self.updating:
            return

        self.presets = " "
        updateNode(self, context)

    def preset_items(self, context):
        return [(k, k.title(), "", "", s[0]) for k, s in sorted(trochoidPresets.items(), key=lambda k: k[1][0])]

    def update_presets(self, context):
        if self.presets == " ":
            return

        self.updating = True

        tT, r1, r2, h, p1, p2, T, N, S = trochoidPresets[self.presets][1:]
        self.tType = tT
        self.radius1 = r1
        self.radius2 = r2
        self.height = h
        self.phase1 = p1
        self.phase2 = p2
        self.turns = T
        self.resolution = N
        self.scale = 1.0
        self.normalize_size = 1.0
        self.normalize = True
        self.swap = False
        self.close = False if self.tType == "LINE" else True

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
        default=4.0, min=0.0, update=update_trochoid)

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

    close = BoolProperty(
        name='Close', description='Close the line',
        default=False, update=update_trochoid)

    swap = BoolProperty(
        name='Swap', description='Swap radii and phases: R1<->R2 and P1<->P2',
        default=False, update=update_trochoid)

    normalize = BoolProperty(
        name='Normalize', description='Scale the curve to fit within normalized size',
        default=False, update=update_normalize)

    normalize_size = FloatProperty(
        name='Size', description='Normalized size of the curve',
        default=1.0, min=0.0, update=updateNode)

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

        self.presets = "ROSETTE"

    def draw_buttons(self, context, layout):
        layout.prop(self, 'presets')
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "tType", expand=True)
        row = col.row(align=True)
        row.prop(self, "normalize", text="Norm", toggle=True)
        row.prop(self, "swap", toggle=True)
        row.prop(self, "close", toggle=True)

    def update_sockets(self):
        if self.normalize:
            socket = self.inputs[-1]
            socket.replace_socket("StringsSocket", "S").prop_name = "normalize_size"
        else:  # AC
            socket = self.inputs[-1]
            socket.replace_socket("StringsSocket", "S").prop_name = "scale"

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

        a, b, p1, p2 = [R2, R1, P2, P1] if self.swap else [R1, R2, P1, P2]

        if self.normalize:  # normalize ? => set scale to fit the normalize size
            if self.tType == "EPI":
                S = 1 / (abs(a + b) + H + epsilon) * S
            elif self.tType == "HYPO":
                S = 1 / (abs(a - b) + H + epsilon) * S
            else:  # LINE
                S = 1 / (2 * pi * a + H + epsilon) * S

        a = a * S
        b = max(b * S, epsilon) # safeguard to avoid division by zero
        h = H * S

        if self.tType == "EPI":
            R = a + b  # outer radius
            Rb = R / b  # outer "gear ratio"
            fx = lambda t: R * cos(t + p1) - h * cos(Rb * t + p2)
            fy = lambda t: R * sin(t + p1) - h * sin(Rb * t + p2)
        elif self.tType == "HYPO":
            r = a - b  # inner radius
            rb = r / b  # inner "gear ratio"
            fx = lambda t: r * cos(t + p1) + h * cos(rb * t + p2)
            fy = lambda t: r * sin(t + p1) - h * sin(rb * t + p2)
        else:  # LINE
            fx = lambda t: b * t - h * sin(t + p1)
            fy = lambda t: b - h * cos(t + p1)

        v = lambda t: [fx(t), fy(t), 0]

        # N = max(3, int(T * N))  # total number of points in all turns
        N = max(3, int((a+b)/b*T * N))  # total number of points in all turns
        dT = 2 * pi * T / N

        verts = [v(n * dT) for n in range(N + 1)]
        edges = [[i, i + 1] for i in range(N)]

        if self.close:
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

        parameters = match_long_repeat([input_R1, input_R2, input_H,
                                        input_P1, input_P2, input_T,
                                        input_N, input_S])

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
