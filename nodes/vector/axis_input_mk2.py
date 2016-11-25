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
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, SvSetSocketAnyType


class SvAxisInputNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Generator for X, Y or Z axis. '''

    bl_idname = 'SvAxisInputNodeMK2'
    bl_label = 'Vector X | Y | Z MK2'    # shall default to Z Axis in svint.
    bl_icon = 'MANIPUL'

    axis_x = bpy.props.BoolProperty(update=updateNode, name='X')
    axis_y = bpy.props.BoolProperty(update=updateNode, name='Y')
    axis_z = bpy.props.BoolProperty(update=updateNode, name='Z')

    def my_custom_draw(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'axis_x', toggle=True)
        row.prop(self, 'axis_y', toggle=True)
        row.prop(self, 'axis_z', toggle=True)

    def sv_init(self, context):
        self.width = 100
        a = self.outputs.new('VerticesSocket', "Vector")
        a.custom_draw = 'my_custom_draw'


    def get_axis(self):
        return int(self.axis_x), int(self.axis_y), int(self.axis_z)

    def draw_label(self):
        return str('{0}, {1}, {2}'.format(*self.get_axis()))

    def process(self):
        vec_out = self.outputs[0]
        if vec_out.is_linked:
            vec_out.sv_set([[list(self.get_axis())]])


def register():
    bpy.utils.register_class(SvAxisInputNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvAxisInputNodeMK2)
