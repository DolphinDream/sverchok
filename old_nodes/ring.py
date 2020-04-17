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

from math import sin, cos, pi, radians

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper


def ring_verts(Separate, u, r1, r2, N1, N2, p):
    '''
        Separate : separate vertices into radial section lists
        r1  : major radius
        r2  : minor radius
        N1  : major sections - number of RADIAL sections
        N2  : minor sections - number of CIRCULAR sections
        p   : radial section phase
    '''
    list_verts = []

    # angle increments (cached outside of the loop for performance)
    da = 2 * pi / (N1*(u+1))

    for n1 in range(N1*(u+1)):
        theta = n1 * da + p     # radial section angle
        sin_theta = sin(theta)  # caching
        cos_theta = cos(theta)  # caching

        loop_verts = []
        s = 2 / (N2 - 1)  # caching
        for n2 in range(N2):
            r = r1 + (n2 * s - 1) * r2
            x = r * cos_theta
            y = r * sin_theta

            # append vertex to loop
            loop_verts.append([x, y, 0.0])

        if Separate:
            list_verts.append(loop_verts)
        else:
            list_verts.extend(loop_verts)

    return list_verts


def ring_edges(N1, N2, u):
    '''
        N1 : major sections - number of RADIAL sections
        N2 : minor sections - number of CIRCULAR sections
    '''
    list_edges = []

    # radial EDGES
    for n1 in range(N1):
        for n2 in range(N2 - 1):
            list_edges.append([N2 * n1*(u+1) + n2, N2 * n1*(u+1) + n2 + 1])

    # circular EDGES
    for n1 in range(N1*(u+1) - 1):
        for n2 in range(N2):
            list_edges.append([N2 * n1 + n2, N2 * (n1 + 1) + n2])
    for n2 in range(N2):
        list_edges.append([N2 * (N1*(u+1) - 1) + n2, n2])

    return list_edges


def ring_polygons(N1, N2, u):
    '''
        N1 : major sections - number of RADIAL sections
        N2 : minor sections - number of CIRCULAR sections
    '''
    list_polys = []
    for n1 in range(N1 - 1):
        for n2 in range(N2 - 1):
            list_polys.append([N2 * n1 + n2, N2 * (n1 + 1) + n2, N2 * (n1 + 1) + n2 + 1, N2 * n1 + n2 + 1])

    for n2 in range(N2 - 1):
        list_polys.append([N2 * (N1 - 1) + n2, n2, n2 + 1, N2 * (N1 - 1) + n2 + 1])

    return list_polys


class SvRingNode(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Ring
    Tooltip: Generate ring meshes
    """
    bl_idname = 'SvRingNode'
    bl_label = 'Ring'
    bl_icon = 'PROP_CON'

    replacement_nodes = [('SvRingNodeMK2', None, dict(rp="p"))]

    def update_mode(self, context):
        # switch radii input sockets (R,r) <=> (eR,iR)
        if self.mode == 'EXT_INT':
            self.inputs['R'].prop_name = "ring_er"
            self.inputs['r'].prop_name = "ring_ir"
        else:
            self.inputs['R'].prop_name = "ring_r1"
            self.inputs['r'].prop_name = "ring_r2"
        updateNode(self, context)

    # keep the equivalent radii pair in sync (eR,iR) => (R,r)
    def external_internal_radii_changed(self, context):
        if self.mode == "EXT_INT":
            self.ring_r1 = (self.ring_er + self.ring_ir) * 0.5
            self.ring_r2 = (self.ring_er - self.ring_ir) * 0.5
            updateNode(self, context)

    # keep the equivalent radii pair in sync (R,r) => (eR,iR)
    def major_minor_radii_changed(self, context):
        if self.mode == "MAJOR_MINOR":
            self.ring_er = self.ring_r1 + self.ring_r2
            self.ring_ir = self.ring_r1 - self.ring_r2
            updateNode(self, context)

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.ring_rP = self.ring_rP * au

    # Ring DIMENSIONS options
    mode: EnumProperty(
        name="Ring Dimensions",
        items=(("MAJOR_MINOR", "R : r",
                "Use the Major/Minor radii for ring dimensions."),
               ("EXT_INT", "eR : iR",
                "Use the Exterior/Interior radii for ring dimensions.")),
        update=update_mode)

    ring_r1: FloatProperty(
        name="Major Radius",
        description="Radius from the ring center to the middle of ring band",
        default=1.0, min=0.0,
        update=major_minor_radii_changed)

    ring_r2: FloatProperty(
        name="Minor Radius",
        description="Width of the ring band",
        default=.25, min=0.0,
        update=major_minor_radii_changed)

    ring_ir: FloatProperty(
        name="Interior Radius",
        description="Interior radius of the ring (closest to the ring center)",
        default=.75, min=0.0,
        update=external_internal_radii_changed)

    ring_er: FloatProperty(
        name="Exterior Radius",
        description="Exterior radius of the ring (farthest from the ring center)",
        default=1.25, min=0.0,
        update=external_internal_radii_changed)

    # Ring RESOLUTION options
    ring_n1: IntProperty(
        name="Radial Sections", description="Number of radial sections",
        default=32, min=3, soft_min=3,
        update=updateNode)

    ring_n2: IntProperty(
        name="Circular Sections", description="Number of circular sections",
        default=3, min=2, soft_min=2,
        update=updateNode)

    # Ring Phase Options
    ring_rP: FloatProperty(
        name="Phase", description="Phase of the radial sections (in degrees)",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    ring_u: IntProperty(
        name="Subdivide Circular", description="Number of subdivisions in the circular sections",
        default=0, min=0, soft_min=0,
        update=updateNode)

    # OTHER options
    Separate: BoolProperty(
        name='Separate', description='Separate UV coords',
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.width = 160
        self.inputs.new('SvStringsSocket', "R").prop_name = 'ring_r1'
        self.inputs.new('SvStringsSocket', "r").prop_name = 'ring_r2'
        self.inputs.new('SvStringsSocket', "n1").prop_name = 'ring_n1'
        self.inputs.new('SvStringsSocket', "n2").prop_name = 'ring_n2'
        self.inputs.new('SvStringsSocket', "rP").prop_name = 'ring_rP'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket',  "Edges")
        self.outputs.new('SvStringsSocket',  "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Separate", text="Separate")
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_angle_units_buttons(context, layout)
        layout.prop(self, 'ring_u')

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        # list of MAJOR or EXTERIOR radii
        input_r1 = self.inputs["R"].sv_get()[0]
        # list of MINOR or INTERIOR radii
        input_r2 = self.inputs["r"].sv_get()[0]
        # list of number of MAJOR sections : RADIAL
        input_n1 = self.inputs["n1"].sv_get()[0]
        # list of number of MINOR sections : CIRCULAR
        input_n2 = self.inputs["n2"].sv_get()[0]
        # list of RADIAL phases
        input_rp = self.inputs["rP"].sv_get()[0]

        # sanitize the input values
        input_r1 = list(map(lambda x: max(0, x), input_r1))
        input_r2 = list(map(lambda x: max(0, x), input_r2))
        input_n1 = list(map(lambda x: max(3, int(x)), input_n1))
        input_n2 = list(map(lambda x: max(2, int(x)), input_n2))

        # conversion factor from the current angle units to radians
        au = self.radians_conversion_factor()

        input_rp = list(map(lambda x: x * au, input_rp))

        # convert input radii values to MAJOR/MINOR, based on selected mode
        if self.mode == 'EXT_INT':
            # convert radii from EXTERIOR/INTERIOR to MAJOR/MINOR
            # (extend radii lists to a matching length before conversion)
            input_a, input_b = match_long_repeat([input_r1, input_r2])
            input_r1 = list(map(lambda a, b: (a + b) * 0.5, input_a, input_b))
            input_r2 = list(map(lambda a, b: (a - b) * 0.5, input_a, input_b))

        params = match_long_repeat([input_r1, input_r2, input_n1, input_n2, input_rp])

        V, E, P = self.outputs[:]
        for s, f in [(V, ring_verts), (E, ring_edges), (P, ring_polygons)]:
            if not s.is_linked:
                continue
            if s == V:
                s.sv_set([f(self.Separate, self.ring_u, *args) for args in zip(*params)])
            else:
                s.sv_set([f(n1, n2, self.ring_u) for _, _, n1, n2, _ in zip(*params)])


def register():
    bpy.utils.register_class(SvRingNode)


def unregister():
    bpy.utils.unregister_class(SvRingNode)
