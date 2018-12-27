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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from mathutils import Quaternion


def project(vert4D, d):
    """
    Project a 4D vector onto 3D space given the projection distance.
    """
    cx, cy, cz = [0.0, 0.0, 0.0]  # center (projection origin)
    x, y, z, w = vert4D
    # w, x, y, z = vert4D
    # return [x + (cx - x) * d / w, y + (cy - y) * d / w, z + (cz - z) * d / w]
    s = d / (d + w)
    xx = x * s
    yy = y * s
    zz = z * s
    return [xx, yy, zz]
    # return [x + (cx - x) * w / d, y + (cy - y) * w / d, z + (cz - z) * w / d]


def project_verts(verts4D, d):
    """
    Project the 4D verts onto 3D space given the projection distance.
    """
    verts3D = [project(verts4D[i], d) for i in range(len(verts4D))]
    return verts3D


class Sv4DProjectNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 4D Projection
    Tooltips: Project from 4D to 3D
    """
    bl_idname = 'Sv4DProjectNode'
    bl_label = '4D Project'

    distance = FloatProperty(
        name="Distance", description="Projection Distance",
        default=2.0, min=0.0,
        update=updateNode)

    def sv_init(self, context):
        # self.width = 160
        self.inputs.new('SvQuaternionSocket', "Quaternions")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Polys")

        self.inputs.new('StringsSocket', "D").prop_name = 'distance'

        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polys")

    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        # input values lists
        inputs = self.inputs

        if inputs["Quaternions"].is_linked:
            input_v = inputs["Quaternions"].sv_get()
        else:
            return

        if inputs["Edges"].is_linked:
            input_e = inputs["Edges"].sv_get()
        else:
            input_e = [[]]

        if inputs["Polys"].is_linked:
            input_p = inputs["Polys"].sv_get()
        else:
            input_p = [[]]

        input_d = inputs["D"].sv_get()[0]

        params = match_long_repeat([input_v, input_e, input_p, input_d])

        vertList = []
        edgeList = []
        polyList = []
        for v, e, p, d in zip(*params):
            verts = project_verts(v, d)
            vertList.append(verts)
            edgeList.append(e)
            polyList.append(p)

        if outputs["Verts"].is_linked:
            outputs["Verts"].sv_set(vertList)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edgeList)
        if outputs["Polys"].is_linked:
            outputs["Polys"].sv_set(polyList)


def register():
    bpy.utils.register_class(Sv4DProjectNode)


def unregister():
    bpy.utils.unregister_class(Sv4DProjectNode)
