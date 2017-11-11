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

from math import sin, cos, pi, sqrt, radians
from random import random
import time

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

DEBUG=False

def digital_root(a=1, level=1):
    digits = str(a)
    if level == 1:
        print("DigitalRoot(", digits, ") = ")

    if len(digits) == 1:
        print(" = ", a)
        print()
        result = a
    else:
        digitAdd = digits.replace("", " + ")[3: -3]
        digitSum = sum(int(digit) for digit in digits)
        print(" = ", digitAdd, " = ", digitSum)
        result = digital_root(digitSum, level+1)

    return result


class SvDigitalRootNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Digital Root '''
    bl_idname = 'SvDigitalRootNode'
    bl_label = 'Digital Root'
    sv_icon = 'SV_DIGITAL_ROOT'

    number = IntProperty(
        name="Number",
        default=9, min=1, soft_min=1,
        description="Input Number",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Number").prop_name = 'number'

        self.outputs.new('StringsSocket',  "Digital Root")

    # def draw_buttons(self, context, layout):

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_N = self.inputs["Number"].sv_get()[0]  # list of numbers

        # sanitize the input values
        input_N = list(map(lambda n: max(1, int(n)), input_N))
        # print(input_N)

        # parameters=match_long_repeat([input_N])

        if self.outputs['Digital Root'].is_linked:
            rootList=[]
            # for n in zip(*parameters):
            for n in input_N:
                # print(n)
                root=digital_root(n)
                rootList.append(root)
            self.outputs['Digital Root'].sv_set(rootList)


def register():
    bpy.utils.register_class(SvDigitalRootNode)


def unregister():
    bpy.utils.unregister_class(SvDigitalRootNode)

if __name__ == '__main__':
    register()
