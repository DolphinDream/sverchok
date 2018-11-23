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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat
from sverchok.utils.sv_operator_mixins import SvGenericCallbackWithParams
from math import sqrt

modeItems = [
    ("AB",  "AB",  "Point A to Point B", 0),
    ("OD",  "OD",  "Origin O in direction D", 1)]

directions = {"X": [1, 0, 0], "Y": [0, 1, 0], "Z": [0, 0, 1]}


def get_vector_interpolator(nx, ny, nz, v1, v2):
    ''' Get the optimal vector interpolator to speed up the line generation '''
    interpolator = [
        lambda l: (v1[0], v1[1], v1[2]),                            # 0: n=(0,0,0)
        lambda l: (v1[0], v1[1], v1[2] + l * nz),                   # 1: n=(0,0,1)
        lambda l: (v1[0], v1[1] + l * ny, v1[2]),                   # 2: n=(0,1,0)
        lambda l: (v1[0], v1[1] + l * ny, v1[2] + l * nz),          # 3: n=(0,1,1)
        lambda l: (v1[0] + l * nx, v1[1], v1[2]),                   # 4: n=(1,0,0)
        lambda l: (v1[0] + l * nx, v1[1], v1[2] + l * nz),          # 5: n=(1,0,1)
        lambda l: (v1[0] + l * nx, v1[1] + l * ny, v1[2]),          # 6: n=(1,1,0)
        lambda l: (v1[0] + l * nx, v1[1] + l * ny, v1[2] + l * nz)  # 7: n=(1,1,1)
    ]

    index = (nx != 0) << 2 | (ny != 0) << 1 | (nz != 0)
    return interpolator[index]


def make_line(flags, steps, size, v1, v2):
    center, normalize, mode = flags

    # get the scaled direction (based on mode, size & normalize)
    if mode == "AB":
        nx, ny, nz = [v2[0] - v1[0],  v2[1] - v1[1], v2[2] - v1[2]]
    elif mode == "OD":
        nx, ny, nz = v2

    nn = sqrt(nx * nx + ny * ny + nz * nz)

    stepsLength = sum(steps)  # length of the non-normalized steps

    if normalize:
        scale = 1 if nn == 0 else (1 / nn / stepsLength * size)  # scale to given size
    else:  # not normalized
        if mode == "AB":
            scale = 1 / stepsLength  # scale to AB vector size
        elif mode == "OD":
            scale = 1 if nn == 0 else (1 / nn)  # scale to steps size

    nx, ny, nz = [nx * scale, ny * scale, nz * scale]

    vec = get_vector_interpolator(nx, ny, nz, v1, v2)

    verts = []
    add_vert = verts.append
    l = -stepsLength / 2 if center else 0
    for s in [0.0] + steps:
        l = l + s
        add_vert(vec(l))
    edges = [[i, i + 1] for i in range(len(steps))]

    return verts, edges


class SvLineNodeMK4(bpy.types.Node, SverchCustomTreeNode):
    ''' Line '''
    bl_idname = 'SvLineNodeMK4'
    bl_label = 'Line'
    bl_icon = 'GRIP'

    def set_direction(self, operator):
        self.direction = operator.direction
        self.mode = "OD"
        return {'FINISHED'}

    def update_normalize(self, context):
        self.inputs["Size"].hide_safe = not self.normalize

    def update_direction(self, context):
        self.point_V1 = [0, 0, 0]
        self.point_V2 = directions[self.direction]

    direction = StringProperty(
        name="Direction", default="X", update=update_direction)

    mode = EnumProperty(
        name="Mode", items=modeItems,
        default="OD", update=updateNode)

    num = IntProperty(
        name='Num Verts', description='Number of Vertices',
        default=2, min=2, update=updateNode)

    step = FloatProperty(
        name='Step', description='Step length',
        default=1.0, update=updateNode)

    center = BoolProperty(
        name='Center', description='Center the line',
        default=False, update=updateNode)

    normalize = BoolProperty(
        name='Normalize', description='Normalize line to size',
        default=False, update=update_normalize)

    size = FloatProperty(
        name='Size', description='Size of line',
        default=10.0, update=updateNode)

    point_V1 = FloatVectorProperty(
        name='V1', description='Point V1 (starting point)',
        size=3, default=(0, 0, 0), update=updateNode)

    point_V2 = FloatVectorProperty(
        name='V2', description='Point V2 (ending point or direction)',
        size=3, default=(1, 0, 0), update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Num").prop_name = 'num'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step'
        size_socket = self.inputs.new('StringsSocket', "Size")
        size_socket.prop_name = 'size'
        size_socket.hide_safe = True
        self.inputs.new('VerticesSocket', "V1").prop_name = "point_V1"
        self.inputs.new('VerticesSocket', "V2").prop_name = "point_V2"
        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        col = layout.column(align=False)

        if not self.inputs["V2"].is_linked:
            row = col.row(align=True)
            for direction in "XYZ":
                op = row.operator("node.set_line_direction", text=direction)
                op.direction = direction

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "mode", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", toggle=True)
        row.prop(self, "normalize", toggle=True)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs
        input_num = inputs["Num"].sv_get()
        input_step = inputs["Step"].sv_get()
        input_size = inputs["Size"].sv_get()[0]
        input_V1 = inputs["V1"].sv_get()[0]
        input_V2 = inputs["V2"].sv_get()[0]

        params = match_long_repeat([input_num, input_step])

        stepList = []
        for n, s in zip(*params):
            for num in n:
                num = max(2, num)
                s = s[:(num - 1)]  # shorten step list if needed
                fullList(s, num - 1)  # extend step list if needed
                stepList.append(s)

        flags = [self.center, self.normalize, self.mode]

        params2 = match_long_repeat([stepList, input_size, input_V1, input_V2])

        vertList, edgeList = [], []
        for steps, size, v1, v2 in zip(*params2):
            verts, edges = make_line(flags, steps, size, v1, v2)
            vertList.append(verts)
            edgeList.append(edges)

        if self.outputs['Verts'].is_linked:
            self.outputs['Verts'].sv_set(vertList)

        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(edgeList)


class SvSetLineDirection(bpy.types.Operator, SvGenericCallbackWithParams):
    bl_label = "Set line direction"
    bl_idname = "node.set_line_direction"   # dont use sv.
    bl_description = "Set the direction of the line along X, Y or Z"

    direction = StringProperty(default="X")
    fn_name = StringProperty(default="set_direction")


def register():
    bpy.utils.register_class(SvSetLineDirection)
    bpy.utils.register_class(SvLineNodeMK4)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK4)
    bpy.utils.unregister_class(SvSetLineDirection)
