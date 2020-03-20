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

projection_type_items = [
    ("PLANAR",  "Planar",  "Project onto a plane", 0),
    ("SPHERICAL", "Spherical", "Project onto a sphere", 1),
    ("CYLINDRICAL", "Cylindrical", "Project onto a cylinder", 2)]

idMat = [[tuple(v) for v in Matrix()]]  # identity matrix

EPSILON = 1e-10


def projection_cylindrical(verts3D, m, d):
    """
    Project 3D verts onto a cylindrical surface

    verts3D : 3D verts to project
    m : matrix orienting the cylindrical projection screen
    d : distance between projector (cylinder origin) and the cylinder surface (cylinder radius)
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection cylinder origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection cylinder axis (Z)

    vert_list = []
    focus_list = []
    for vert in verts3D:
        x, y, z = vert
        # vertex vector relative to the center of the cylinder (OV = V - O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the OV vector projected PARALLEL to the cylinder axis
        vn = dx * nx + dy * ny + dz * nz
        # vector OV projected PERPENDICULAR to the cylinder axis
        xn = dx - vn * nx
        yn = dy - vn * ny
        zn = dz - vn * nz
        # magnitude of the perpendicular projection
        r = sqrt(xn * xn + yn * yn + zn * zn) + EPSILON
        # factor to scale the OV vector to touch the cylinder
        s = d / r
        # extended vector touching the cylinder
        xx = ox + dx * s
        yy = oy + dy * s
        zz = oz + dz * s

        vert_list.append([xx, yy, zz])

    focus_list = [[ox, oy, oz]]

    return vert_list, focus_list


def projection_spherical(verts3D, m, d):
    """
    Project 3D verts onto a spherical surface

    verts3D : 3D verts to project
    m : matrix orienting the sphere (no effect)
    d : distance between projector (sphere origin) and the sphere surface (sphere radius)
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection sphere origin

    vert_list = []
    focus_list = []
    for vert in verts3D:
        x, y, z = vert
        # vertex vector relative to the sphere origin (OV = V - O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the OV vector
        r = sqrt(dx * dx + dy * dy + dz * dz) + EPSILON
        # factor to scale the OV vector to touch the sphere
        s = d / r
        # extended vector touching the sphere
        xx = ox + dx * s
        yy = oy + dy * s
        zz = oz + dz * s

        vert_list.append([xx, yy, zz])

    focus_list = [[ox, oy, oz]]

    return vert_list, focus_list


def projection_planar(verts3D, m, d):
    """
    Project 3D verts onto a planar surface

    verts3D : 3D verts to project
    m : matrix orienting the plane (plane normal is along Z)
    d : distance between the projector point and the plane surface

    # Projection point (focus) location is given by m * D:
    #  Xx Yx Zx Tx        0     Tx - d * Zx
    #  Xy Yy Zy Ty   *    0  =  Ty - d * Zy
    #  Xz Yz Zz Tz      - d     Tz - d * Zz
    #  0  0  0  1         1     1
    """
    tx, ty, tz = [m[0][3], m[1][3], m[2][3]]  # projection screen location
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection screen normal

    ox, oy, oz = [tx - d * nx, ty - d * ny, tz - d * nz] # projection point

    vert_list = []
    focus_list = []
    for vert in verts3D:
        x, y, z = vert
        # vertex vector relative to the projection point (OV = V - O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the OV vector projected PARALLEL to the plane normal
        l = (dx * nx + dy * ny + dz * nz) + EPSILON
        # factor to scale the OV vector to touch the plane
        s = d / l
        # extended vector touching the plane
        xx = ox + dx * s
        yy = oy + dy * s
        zz = oz + dz * s

        vert_list.append([xx, yy, zz])

    focus_list = [[ox, oy, oz]]

    return vert_list, focus_list


class Sv3DProjectNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Projection, Perspective
    Tooltips: Projection from 3D space to 2D space
    """
    bl_idname = 'Sv3DProjectNode'
    bl_label = '3D Projector'

    projection_type: EnumProperty(
        name="Projection Type", items=projection_type_items, default="PLANAR", update=updateNode)

    distance: FloatProperty(
        name="Distance", description="Projection Distance",
        default=2.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Verts")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Polys")
        # projection screen location and orientation
        self.inputs.new('SvMatrixSocket', "Matrix")
        # distance from the projection point to the projection screen
        self.inputs.new('SvStringsSocket', "D").prop_name = 'distance'

        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polys")
        self.outputs.new('SvVerticesSocket', "Focus")

    def draw_buttons(self, context, layout):
        layout.prop(self, "projection_type", text="")

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

        input_e = inputs["Edges"].sv_get(default=[[]])
        input_p = inputs["Polys"].sv_get(default=[[]])
        input_m = inputs["Matrix"].sv_get(default=idMat)
        input_d = inputs["D"].sv_get()[0]

        params = match_long_repeat([input_v, input_e, input_p, input_m, input_d])

        if self.projection_type == "PLANAR":
            projector = projection_planar
        elif self.projection_type == "CYLINDRICAL":
            projector = projection_cylindrical
        elif self.projection_type == "SPHERICAL":
            projector = projection_spherical

        vert_list = []
        edge_list = []
        poly_list = []
        focus_list = []
        for v, e, p, m, d in zip(*params):
            verts, focus = projector(v, m, d)
            vert_list.append(verts)
            edge_list.append(e)
            poly_list.append(p)
            focus_list.append(focus)

        if outputs["Verts"].is_linked:
            outputs["Verts"].sv_set(vert_list)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edge_list)
        if outputs["Polys"].is_linked:
            outputs["Polys"].sv_set(poly_list)
        if outputs["Focus"].is_linked:
            outputs["Focus"].sv_set(focus_list)


def register():
    bpy.utils.register_class(Sv3DProjectNode)


def unregister():
    bpy.utils.unregister_class(Sv3DProjectNode)
