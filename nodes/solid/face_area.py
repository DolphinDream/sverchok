# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import map_recursive
from sverchok.utils.surface import SvSurface
from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface


class SvSolidFaceAreaNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Face Area Solid
    Tooltip: Calculate area of a Face of a Solid
    """
    bl_idname = 'SvSolidFaceAreaNode'
    bl_label = 'Solid Face Area'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_AREA'
    sv_category = "Solid Operators"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "SolidFace")
        self.outputs.new('SvStringsSocket', "Area")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        faces_in = self.inputs['SolidFace'].sv_get()

        def calc(face_surface):
            if not is_solid_face_surface(face_surface):
                face_surface = surface_to_freecad(face_surface, make_face=True)
            a = face_surface.face.Area
            return [a]

        area_out = map_recursive(calc, faces_in, data_types=(SvSurface,))

        self.outputs['Area'].sv_set(area_out)


def register():
    bpy.utils.register_class(SvSolidFaceAreaNode)

def unregister():
    bpy.utils.unregister_class(SvSolidFaceAreaNode)
