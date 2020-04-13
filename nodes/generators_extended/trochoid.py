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
from sverchok.data_structure import (match_long_repeat, updateNode, get_edge_list, get_edge_loop)

from math import sin, cos, pi, sqrt

from sverchok.utils.profile import profile

epsilon = 1e-5  # used to avoid division by zero

typeItems = [("HYPO", "Hypo", ""), ("LINE", "Line", ""), ("EPI", "Epi", "")]

# name : [ preset index, type, r1, r2, distance, phase1, phase2, turns, resolution ]
trochoidPresets = {
    " ":                    (0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0),
    # GENERIC LINE, EPI and HYPO TYPES
    "CYCLOID":              (10, "LINE", 1.0, 1.0, 1.0, 0.0, 0.0, 3.0, 200),
    "CURTATE CYCLOID":      (11, "LINE", 1.0, 1.0, 0.5, 0.0, 0.0, 3.0, 200),
    "PROLATE CYCLOID":      (12, "LINE", 1.0, 1.0, 2.0, 0.0, 0.0, 3.0, 200),
    "EPI-CYCLOID":          (13, "EPI", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "CURTATE EPI-CYCLOID":  (14, "EPI", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200),
    "PROLATE EPI-CYCLOID":  (15, "EPI", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200),
    "HYPO CYCLOID":         (16, "HYPO", 7.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "CURTATE HYPO-CYCLOID": (17, "HYPO", 7.0, 1.0, 0.5, 0.0, 0.0, 1.0, 200),
    "PROLATE HYPO-CYCLOID": (18, "HYPO", 7.0, 1.0, 2.0, 0.0, 0.0, 1.0, 200),
    # EPIs
    "CARDIOID":             (20, "EPI", 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "NEPHROID":             (21, "EPI", 2.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "RANUNCULOID":          (22, "EPI", 5.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    # HYPOs
    "DELTOID":              (30, "HYPO", 3.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "ASTROID":              (31, "HYPO", 4.0, 1.0, 1.0, 0.0, 0.0, 1.0, 200),
    "ROSETTE":              (32, "HYPO", 6.0, 1.0, 5.0, 0.0, 0.0, 1.0, 300),
    # other somewhat interesting EPIs
    "E 6-1-5":              (40, "EPI", 6.0, 1.0, 5.0, 0.0, 0.0, 1.0, 300),
    "E 6-3-1":              (41, "EPI", 6.0, 3.0, 1.0, 0.0, 0.0, 1.0, 200),
    "E 10-1-9":             (42, "EPI", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500),
    "E 12-7-11":            (43, "EPI", 12.0, 7.0, 11.0, 0.0, 0.0, 7.0, 500),
    "E 7-2-2":              (44, "EPI", 7.0, 2.0, 2.0, 0.0, 0.0, 2.0, 300),
    # other somewhat interesting HYPOs
    "H 6-1-4":              (50, "HYPO", 6.0, 1.0, 4.0, 0.0, 0.0, 1.0, 500),
    "H 10-1-9":             (51, "HYPO", 10.0, 1.0, 9.0, 0.0, 0.0, 1.0, 500),
    "H 13-6-12":            (52, "HYPO", 13.0, 6.0, 12.0, 0.0, 0.0, 6.0, 200),
    "H 1-5-2":              (53, "HYPO", 1.0, 5.0, 2.0, 0.0, 0.0, 5.0, 200),
    "H 6-10-5":             (54, "HYPO", 6.0, 10.0, 5.0, 0.0, 0.0, 10.0, 100),
}


class SvTrochoidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Curve, Line, Cycloid
    Tooltip: Generate a trochoid curve (cycloids & epi / hypo trochoids)
    """
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

        tT, r1, r2, d, p1, p2, T, N = trochoidPresets[self.presets][1:]
        self.tType = tT
        self.radius1 = r1
        self.radius2 = r2
        self.distance = d
        self.phase1 = p1
        self.phase2 = p2
        self.turns = T
        self.resolution = N
        self.scale = 1.0
        self.normalize_size = 1.0
        self.normalize = True
        self.swap = False

        self.updating = False
        updateNode(self, context)

    presets = EnumProperty(
        name="Presets", items=preset_items, update=update_presets)

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

    distance = FloatProperty(
        name='Distance',
        description='Distance from the drawing point to the center of the moving circle',
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

    shift = FloatProperty(
        name='Shift', description='Shift the starting point along the curve',
        default=0.0, min=0.0, max=1.0, update=update_trochoid)

    resolution = IntProperty(
        name='Resolution',
        description='Number of vertices in one full turn around the static circle',
        default=200, min=3, update=update_trochoid)

    scale = FloatProperty(
        name='Scale', description='Scale of the main parameters: radii and distance',
        default=1.0, min=0.0, update=update_trochoid)

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
        self.width = 170
        self.inputs.new('StringsSocket', "R1").prop_name = "radius1"
        self.inputs.new('StringsSocket', "R2",).prop_name = "radius2"
        self.inputs.new('StringsSocket', "D").prop_name = "distance"
        self.inputs.new('StringsSocket', "T").prop_name = "turns"
        self.inputs.new('StringsSocket', "N").prop_name = "resolution"
        self.inputs.new('StringsSocket', "P1").prop_name = "phase1"
        self.inputs.new('StringsSocket', "P2").prop_name = "phase2"
        self.inputs.new('StringsSocket', "F").prop_name = "shift"
        self.inputs.new('StringsSocket', "S").prop_name = "scale"

        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "Edges")

        self.presets = "ROSETTE"

    def draw_buttons(self, context, layout):
        layout.prop(self, 'presets', text="")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "tType", expand=True)
        row = col.row(align=True)
        row.prop(self, "normalize", text="Norm", toggle=True)
        row.prop(self, "swap", toggle=True)

    def update_sockets(self):
        if self.normalize:
            socket = self.inputs[-1]
            socket.replace_socket("StringsSocket", "S").prop_name = "normalize_size"
        else:  # AC
            socket = self.inputs[-1]
            socket.replace_socket("StringsSocket", "S").prop_name = "scale"

    def make_trochoid(self, R1, R2, D, P1, P2, T, N, F, S):
        """
        R1 : radius1    = radius of the static circle
        R2 : radius2    = radius of the moving circle
        D  : distance   = drawing point distance to the center of the moving circle
        P1 : phase1     = starting angle for the static circle
        P2 : phase2     = starting angle for the moving circle
        T  : turns      = number of turns around the static circle
        N  : resolution = number of vertices in one full turn around the static circle
        F  : shift      = shift the starting point along the curve (percentage)
        S  : scale      = scale the main parameters (radii & distance)
        """
        verts = []
        edges = []

        a, b, p1, p2 = [R2, R1, P2, P1] if self.swap else [R1, R2, P1, P2]

        if self.normalize:  # normalize ? => set scale to fit the normalize size
            if self.tType == "EPI":
                S = S / (abs(a + b) + D + epsilon)
            elif self.tType == "HYPO":
                S = S / (abs(a - b) + D + epsilon)
            else:  # LINE
                S = S / (2 * pi * a + D + epsilon)

        a = a * S
        b = max(b * S, epsilon)  # safeguard to avoid division by zero
        d = D * S

        if self.tType == "EPI":
            R = a + b  # outer radius
            Rb = R / b  # outer "gear ratio"
            fx = lambda t: R * cos(t + p1) - d * cos(Rb * t + p2)
            fy = lambda t: R * sin(t + p1) - d * sin(Rb * t + p2)
        elif self.tType == "HYPO":
            r = a - b  # inner radius
            rb = r / b  # inner "gear ratio"
            fx = lambda t: r * cos(t + p1) + d * cos(rb * t + p2)
            fy = lambda t: r * sin(t + p1) - d * sin(rb * t + p2)
        else:  # LINE
            fx = lambda t: b * t - d * sin(t + p1)
            fy = lambda t: b - d * cos(t + p1)

        v = lambda t: [fx(t), fy(t), 0]

        N = max(3, int(T * N))  # total number of points in all turns
        dT = 2 * pi * T / N
        shift = 2 * pi * F * T

        verts = [v(shift + n * dT) for n in range(N + 1)]

        # close the curve if the first & last points overlap (remove duplicate)
        vF, vL = [verts[0], verts[N]]
        dx, dy, dz = [vL[0] - vF[0], vL[1] - vF[1], vL[2] - vF[2]]
        d = sqrt(dx * dx + dy * dy + dz * dz)

        if d < epsilon:
            del verts[-1]
            edges = get_edge_loop(N)
        else:
            edges = get_edge_list(N)

        return verts, edges

    @profile
    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_R1 = inputs["R1"].sv_get()[0]  # radius R1
        input_R2 = inputs["R2"].sv_get()[0]  # radius R2
        input_D = inputs["D"].sv_get()[0]    # distance
        input_P1 = inputs["P1"].sv_get()[0]  # phase P1
        input_P2 = inputs["P2"].sv_get()[0]  # phase P2
        input_T = inputs["T"].sv_get()[0]    # turns
        input_N = inputs["N"].sv_get()[0]    # resolution
        input_S = inputs["S"].sv_get()[0]    # scale
        input_F = inputs["F"].sv_get()[0]    # shift

        # sanitize the inputs
        input_R1 = list(map(lambda x: max(0.0, x), input_R1))
        input_R2 = list(map(lambda x: max(0.0, x), input_R2))
        input_D = list(map(lambda x: max(0.0, x), input_D))
        input_T = list(map(lambda x: max(0.0, x), input_T))
        input_N = list(map(lambda x: max(3, int(x)), input_N))
        input_S = list(map(lambda x: max(0.0, x), input_S))
        # input_F = list(map(lambda x: max(0.0, min(1.0, x)), input_F))

        parameters = match_long_repeat([input_R1, input_R2, input_D,
                                        input_P1, input_P2, input_T,
                                        input_N, input_F, input_S])

        vertList = []
        edgeList = []
        for R1, R2, D, P1, P2, T, N, F, S in zip(*parameters):
            verts, edges = self.make_trochoid(R1, R2, D, P1, P2, T, N, F, S)
            vertList.append(verts)
            edgeList.append(edges)

        if outputs["Verts"].is_linked:
            outputs["Verts"].sv_set(vertList)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edgeList)


def register():
    bpy.utils.register_class(SvTrochoidNode)


def unregister():
    bpy.utils.unregister_class(SvTrochoidNode)
