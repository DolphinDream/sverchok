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

from math import sin, cos, pi, sqrt, radians
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
import itertools


def intersect(edge, plane):
    '''
        Computes and returns the edge-plane intersection (if any)
    '''
    L0, L1 = edge
    P0, n = plane

    w = P0 - L0
    m = L1 - L0

    if m * n == 0:  # edge is parallel to the plane => no intersection
        L = []
    else:  # edge is not parallel => intersection may exist
        t = (w * n) / (m * n)  # t=0 -> L=L0, t=1 -> L=L1
        if t >= 0 and t <= 1:  # intersection inside of the edge
            L = L0 + t * m
        else:  # intersection outside of the edge
            L = []
    return L


def poly_plane_intersection(verts, poly, plane):
    vertsList = []
    edgesList = []

    ne = len(poly)
    edges = [[poly[i], poly[(i + 1) % ne]] for i in range(ne)]
    # print(poly)
    # print(edges)
    vlist = []
    ip = 0
    for i1, i2 in edges:
        v1 = Vector(verts[i1])
        v2 = Vector(verts[i2])
        edge = [v1, v2]
        # print(edge)
        iv = intersect(edge, plane)

        if iv:
            ip = ip + 1
            # print("vert #", ip, " iv = ", iv)
            vert = [i for i in iv]
            vertsList.append(vert)
            vlist.append(len(vertsList) - 1)

        if len(vlist) == 2:
            edgesList.append([vlist[0], vlist[1]])

    print("vertsList=", vertsList)
    print("edgesList=", edgesList)

    return vertsList, edgesList


class SvPlaneIntersectNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Plane Intersection '''
    bl_idname = 'SvPlaneIntersectNode'
    bl_label = 'Plane Intersection'

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('VerticesSocket', "Vertices")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Polys")

        self.inputs.new('VerticesSocket', "P0")
        self.inputs.new('VerticesSocket', "n")

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

        input_verts = inputs["Vertices"].sv_get()
        input_edges = inputs["Edges"].sv_get()
        input_polys = inputs["Polys"].sv_get()

        input_p0s = inputs["P0"].sv_get()
        input_ns = inputs["n"].sv_get()

        params = match_long_repeat([input_verts, input_edges, input_polys, input_p0s, input_ns])
        # print("ivs =", input_verts)
        # print("ies =", input_edges)
        # print("ips =", input_polys)
        # print("ip0s =", input_p0s)
        # print("ins =", input_ns)

        vertsList = []
        edgesList = []
        polysList = []
        for verts, edges, polys, p0s, ns in zip(*params):
            # print("vs=", vs)
            # print("es=", es)
            # print("ps=", ps)
            # print("p0s=", p0s)
            # print("ns=", ns)

            P0 = Vector(p0s[0])
            n = Vector(ns[0])
            plane = [P0, n]

            vl = []
            el = []
            i = 0
            for poly in polys:
                i = i +1
                print("Poly %d of %d" % (i, len(polys)))
                vs, es = poly_plane_intersection(verts, poly, plane)
                vl.extend(vs)
                el.extend(es)

            vertsList.append(vl)
            edgesList.append(el)

        outputs['Verts'].sv_set(vertsList)
        outputs['Edges'].sv_set(edgesList)
        outputs['Polys'].sv_set(polysList)


def register():
    bpy.utils.register_class(SvPlaneIntersectNode)


def unregister():
    bpy.utils.unregister_class(SvPlaneIntersectNode)
