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

from mathutils import Matrix
from functools import reduce

from sverchok.node_tree import SverchCustomTreeNode, MatrixSocket, StringsSocket
from sverchok.data_structure import (updateNode, match_long_repeat,
                                     Matrix_listing, Matrix_generate)
from pprint import pprint

sortDirection = [
    ("X", "x", "Sort by X location", 0),
    ("Y", "y", "Sort by Y location", 1),
    ("Z", "z", "Sort by Z location", 2),
]

id_mat = Matrix_listing([Matrix.Identity(4)])


class SvMatrixSortNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Sort matrices '''
    bl_idname = 'SvMatrixSortNode'
    bl_label = 'Matrix Sort'
    bl_icon = 'OUTLINER_OB_EMPTY'

    direction = EnumProperty(
        name="Operation",
        description="Sort matrices by this location",
        items=sortDirection, default="Z", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('MatrixSocket', "iMatrix", "iMatrix")
        self.outputs.new('MatrixSocket', "oMatrix", "oMatrix")

    def draw_buttons(self, context, layout):
        layout.prop(self, "direction", text="")

    def process(self):
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs
        input_matrix = inputs['iMatrix'].sv_get(default=id_mat)

        vv = {"X": (0, 3), "Y": (1, 3), "Z": (2, 3)}

        i, j = vv[self.direction]

        sortedMatrices = sorted(input_matrix, key=lambda m: m[i][j])

        outputs["oMatrix"].sv_set(sortedMatrices)


def register():
    bpy.utils.register_class(SvMatrixSortNode)


def unregister():
    bpy.utils.unregister_class(SvMatrixSortNode)
