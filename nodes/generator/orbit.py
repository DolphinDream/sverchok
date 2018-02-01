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

from math import sin, cos, pi, sqrt, tan, atan


class SvOrbitNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Orbit '''
    bl_idname = 'SvOrbitNode'
    bl_label = 'Orbit'
    bl_icon = 'OUTLINER_OB_EMPTY'

    major_radius = FloatProperty(
        name='Major Radius', description='Major radius of the orbit',
        default=1.0, min=0.0, update=updateNode)

    eccentricity = FloatProperty(
        name='Eccentricity', description='Orbit eccentricity',
        default=0.6, min=0.0, max=1.0, update=updateNode)

    time = FloatProperty(
        name='Time', description='Time',
        default=0.5, min=0.0, max=1.0, update=updateNode)

    def get_eccentric_anomaly2(self, e, t):
        M = 2.0 * pi * t  # 0->2*pi
        E = M + e * sin(M) + e * e * sin(M) * cos(M) + 0.5 * e**3 * sin(M) * (3 * cos(M)**2 - 1)

        return M, E

    def get_eccentric_anomaly(self, e, t):
        M = 2.0 * pi * t  # 0->2*pi
        # if M < pi:
        #     E = M - e / 2
        # else:
        #     E = M + e / 2

        if e < 0.8:
            E = M
        else:
            if M < pi:
                E = pi
            else:
                E = M - e / 2

        dE = 1
        while dE > 1e-8:
            # dE = (M + e * sin(E) - E) / (1.0 - e * cos(E))
            # dE = (M + e * sin(E) - E) / (1.0 - e * cos(E) + 0.5 * dE * e * sin(E))
            # dE = (M + e * sin(E) - E) / (1.0 - e * cos(E) + 0.5 * (e*sin(E) - 1/3 *e * cos(E) * dE) * dE)
            # E = E + dE
            dE = (E - e * sin(E) - M) / (1.0 - e * cos(E))
            dE = (E - e * sin(E) - M) / (1.0 - e * cos(E) - 0.5 * dE * e * sin(E))
            dE = (E - e * sin(E) - M) / (1.0 - e * cos(E) - 0.5 * (e*sin(E) - 1/3*e*cos(E) * dE) * dE)
            E = E - dE

        # print("E=", E)
        # print("M=", M)
        # print("t=", t)

        return M, E

    def get_orbit(self, a, e, t):

        M, E = self.get_eccentric_anomaly(e, t)

        t = E / (2.0 * pi)
        r = a * (1.0 - e * cos(E))
        h = 2.0 * atan(sqrt((1 + e) / (1 - e)) * tan(E / 2))

        return t, r, h, M, E

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('StringsSocket', "a", "a").prop_name = "major_radius"
        self.inputs.new('StringsSocket', "e", "e").prop_name = "eccentricity"
        self.inputs.new('StringsSocket', "t", "t").prop_name = "time"

        self.outputs.new('StringsSocket', "Time", "Time")
        self.outputs.new('StringsSocket', "Radius", "Radius")
        self.outputs.new('StringsSocket', "Theta", "Theta")
        self.outputs.new('StringsSocket', "M", "M")
        self.outputs.new('StringsSocket', "E", "E")

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_a = inputs["a"].sv_get()[0]
        input_e = inputs["e"].sv_get()[0]
        input_t = inputs["t"].sv_get()[0]
        # sanitize the input
        input_a = list(map(lambda x: max(0.0, x), input_a))
        input_e = list(map(lambda x: max(0.0, min(1.0, x)), input_e))
        input_t = list(map(lambda x: max(0.0, min(1.0, x)), input_t))

        # print("input_t = ", input_t)
        parameters = match_long_repeat([input_a, input_e, input_t])

        tList = []
        rList = []
        hList = []
        mList = []
        eList = []
        for a, e, t in zip(*parameters):
            # print("params=", parameters)
            t, r, h, M, E = self.get_orbit(a, e, t)
            tList.append(t)
            rList.append(r)
            hList.append(h)
            mList.append(M)
            eList.append(E)

        outputs["Time"].sv_set([tList])
        outputs["Radius"].sv_set([rList])
        outputs["Theta"].sv_set([hList])
        outputs["M"].sv_set([mList])
        outputs["E"].sv_set([eList])


def register():
    bpy.utils.register_class(SvOrbitNode)


def unregister():
    bpy.utils.unregister_class(SvOrbitNode)
