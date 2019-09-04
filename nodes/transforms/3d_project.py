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
from mathutils import Matrix
from math import sqrt

from sverchok.utils.profile import profile

projection_screen_items = [
    ("PLANAR",  "Planar",  "Project onto a plane", 0),
    ("CYLINDRICAL", "Cylindrical", "Project onto a cylinder", 1),
    ("SPHERICAL", "Spherical", "Project onto a sphere", 2)]


projection_type_items = [
    ("PERSPECTIVE",  "Perspective",  "Perspective projection", 0),
    ("ORTHOGRAPHIC", "Orthographic", "Orthographic projection", 1)]

idMat = [[tuple(v) for v in Matrix()]]  # identity matrix

EPSILON = 1e-10


def projection_planar(verts3D, m, d, perspective):
    """
    Project the 3D verts onto a plane.
     verts3D : vertices to project (perspective or ortographic)
           m : transformation matrix of the projection plane (location & rotation)
           d : distance between the projection point (focus) and the projection plane
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection plane origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection plane normal

    # d = d if perspective else 1e10

    vertList = []
    for vert in verts3D:
        x, y, z = vert
        # vector relative to the plane origin (V-O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the vector projected parallel to the plane normal
        an = dx * nx + dy * ny + dz * nz
        # factor to scale the vector to touch the plane
        s = d / (d + an)
        # extended vector touching the plane
        px = ox + s * (dx - an * nx)
        py = oy + s * (dy - an * ny)
        pz = oz + s * (dz - an * nz)

        vertList.append([px, py, pz])

    # Focus location m * D:
    #  Xx Yx Zx Tx        0     Tx - d * Zx
    #  Xy Yy Zy Ty   *    0  =  Ty - d * Zy
    #  Xz Yz Zz Tz      - d     Tz - d * Zz
    #  0  0  0  1         1     1
    focus = [[ox - d * nx, oy - d * ny, oz - d * nz]]

    return vertList, focus


def projection_cylindrical(verts3D, m, d, perspective):
    """
    Project the 3D verts onto a cylinder.
     verts3D : vertices to project (perspective)
           m : transformation matrix of the projection cylinder (location & rotation)
           d : distance between the projection point (focus) and the projection cylinder (cylinder radius)

    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection cylinder origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection cylinder axis

    vertList = []
    for vert in verts3D:
        x, y, z = vert
        # vector relative to the cylinder origin (V-O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the vector projected parallel to the cylinder normal
        vn = dx * nx + dy * ny + dz * nz
        # vector projected perpendicular to the cylinder normal
        xn = dx - vn * nx
        yn = dy - vn * ny
        zn = dz - vn * nz
        # magnitude of the perpendicular projection
        r = sqrt(xn * xn + yn * yn + zn * zn) + EPSILON
        # factor to scale the vector to touch the cylinder
        s = d / r
        # extended vector touching the cylinder
        xx = ox + dx * s
        yy = oy + dy * s
        zz = oz + dz * s

        vertList.append([xx, yy, zz])

    focus = [[ox, oy, oz]]

    return vertList, focus


def projection_spherical(verts3D, m, d, perspective):
    """
    Project the 3D verts onto a sphere.
     verts3D : vertices to project (perspective)
           m : transformation matrix of the projection sphere (location & rotation)
           d : distance between the projection point (focus and the projection sphere (sphere radius)
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection sphere origin

    vertList = []
    for vert in verts3D:
        x, y, z = vert
        # vector relative to the sphere origin (V-O)
        dx = x - ox
        dy = y - oy
        dz = z - oz

        r = sqrt(dx*dx + dy*dy + dz*dz) + EPSILON

        xx = ox + dx * d/r
        yy = oy + dy * d/r
        zz = oz + dz * d/r

        vertList.append([xx, yy, zz])

    focus = [[ox, oy, oz]]

    return vertList, focus


class Sv3DProjectNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 3D Projection, Perspective, Orthographic
    Tooltips: Projection from 3D space to 2D space
    """
    bl_idname = 'Sv3DProjectNode'
    bl_label = '3D Projection'

    projection_screen = EnumProperty(
        name="Screen", items=projection_screen_items, default="PLANAR", update=updateNode)

    projection_type = EnumProperty(
        name="Type", items=projection_type_items, default="PERSPECTIVE", update=updateNode)

    distance = FloatProperty(
        name="Distance", description="Projection Distance", default=2.0, update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('VerticesSocket', "Verts")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Polys")
        # projection screen location and orientation
        self.inputs.new('MatrixSocket', "Matrix")
        # distance from the projection point to the projection screen
        self.inputs.new('StringsSocket', "D").prop_name = 'distance'

        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polys")
        self.outputs.new('VerticesSocket', "Focus")

    def draw_buttons(self, context, layout):
        layout.prop(self, "projection_screen", text="")

        if self.projection_screen == "PLANAR":
            layout.prop(self, "projection_type", expand=True)

    @profile
    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs

        if inputs["Verts"].is_linked:
            input_v = inputs["Verts"].sv_get()
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

        input_m = inputs["Matrix"].sv_get(default=idMat)

        input_d = inputs["D"].sv_get()[0]

        params = match_long_repeat([input_v, input_e, input_p, input_m, input_d])

        if self.projection_screen == "PLANAR":
            projector = projection_planar
        elif self.projection_screen == "CYLINDRICAL":
            projector = projection_cylindrical
        elif self.projection_screen == "SPHERICAL":
            projector = projection_spherical

        perspective = self.projection_type == "PERSPECTIVE"

        vertList = []
        edgeList = []
        polyList = []
        focusList = []
        for v, e, p, m, d in zip(*params):
            verts, focus = projector(v, m, d, perspective)
            vertList.append(verts)
            edgeList.append(e)
            polyList.append(p)
            focusList.append(focus)

        if outputs["Verts"].is_linked:
            outputs["Verts"].sv_set(vertList)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edgeList)
        if outputs["Polys"].is_linked:
            outputs["Polys"].sv_set(polyList)
        if outputs["Focus"].is_linked:
            outputs["Focus"].sv_set(focusList)


def register():
    bpy.utils.register_class(Sv3DProjectNode)


def unregister():
    bpy.utils.unregister_class(Sv3DProjectNode)
