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

from math import sin, cos, pi, radians, ceil

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat


def prepare_volume(bounds, resolution, padding):
    '''
        Calculate the voxelize/padded grid, volume origin, voxel dimension
    '''
    # print("bounds=", bounds)
    # print("resolution=", resolution)
    # print("padding=", padding)

    m_xmin, m_xmax, m_ymin, m_ymax, m_zmin, m_zmax = bounds
    m_res = float(resolution)
    m_padding = float(padding)

    # get the voxel dimensions of the padded voxelized volume (B3 = B2 + padding)
    m_xNum = int(ceil((m_xmax - m_xmin) / m_res)) + 2 * m_padding
    m_yNum = int(ceil((m_ymax - m_ymin) / m_res)) + 2 * m_padding
    m_zNum = int(ceil((m_zmax - m_zmin) / m_res)) + 2 * m_padding

    # print("xNum=", m_xNum)
    # print("yNum=", m_yNum)
    # print("zNum=", m_zNum)

    # get the final bounding box (B3) of the padded voxelized volume
    xpad = (m_res * m_xNum - (m_xmax - m_xmin)) / 2.0
    m_xmin -= xpad
    m_xmax += xpad
    ypad = (m_res * m_yNum - (m_ymax - m_ymin)) / 2.0
    m_ymin -= ypad
    m_ymax += ypad
    zpad = (m_res * m_zNum - (m_zmax - m_zmin)) / 2.0
    m_zmin -= zpad
    m_zmax += zpad

    # get the total Z-minimum of ALL surfaces (including the padding). This is
    # used during rendering as the FAR-plane to ensure no FAR plane clipping.
    # m_totalZmin = min(m_zmin, m_surfaces[1]->min[2])

    # set volumes parameters : origin, resolution and voxel dimensions
    m_volumeOrigin = [m_xmin + 0.5 * m_res, m_ymin + 0.5 * m_res, m_zmin + 0.5 * m_res]
    m_volumeResolution = [m_res, m_res, m_res]
    m_volumeVoxelDimensions = [m_xNum, m_yNum, m_zNum]

    paddedBounds = [m_xmin, m_xmax, m_ymin, m_ymax, m_zmin, m_zmax]
    paddedSize = [m_xmax - m_xmin, m_ymax - m_ymin, m_zmax - m_zmin]

    return m_volumeOrigin, m_volumeVoxelDimensions, paddedBounds, paddedSize


class SvMiniVoxelizerNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Mini Voxelizer '''
    bl_idname = 'SvMiniVoxelizerNode'
    bl_label = 'Mini Voxelizer'
    # bl_icon = 'PROP_CON'

    focus_range = IntProperty(
        name="Focus Range", description="Number of voxels around the focus point",
        default=3, min=1, max=10, update=updateNode)

    padding = IntProperty(
        name="Padding", description="Number of padding voxels on each side",
        default=4, min=2, update=updateNode)

    resolution = FloatProperty(
        name="Resolution", description="Voxel resolution",
        default=0.25, min=0.0, update=updateNode)

    def sv_init(self, context):
        self.width = 170
        self.inputs.new('VerticesSocket', "V")
        self.inputs.new('VerticesSocket', "F")
        self.inputs.new('StringsSocket', "FR").prop_name= "focus_range"
        self.inputs.new('StringsSocket', "R").prop_name = "resolution"
        self.inputs.new('StringsSocket', "P").prop_name = "padding"

        self.outputs.new('VerticesSocket', "Min")
        self.outputs.new('VerticesSocket', "Max")
        self.outputs.new('VerticesSocket', "Mean")
        self.outputs.new('VerticesSocket', "Size")

        self.outputs.new('VerticesSocket', "VO")  # volume origin
        self.outputs.new('StringsSocket', "VD")  # voxel dimensions
        self.outputs.new('VerticesSocket', "PB")  # padded bounds
        self.outputs.new('VerticesSocket', "PS")  # padded size

        # self.outputs.new('StringsSocket', "MinX")
        # self.outputs.new('StringsSocket', "MaxX")
        # self.outputs.new('StringsSocket', "MinY")
        # self.outputs.new('StringsSocket', "MaxY")
        # self.outputs.new('StringsSocket', "MinZ")
        # self.outputs.new('StringsSocket', "MaxZ")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        verts = self.inputs["V"].sv_get()[0]  # vertices
        focus = self.inputs["F"].sv_get()[0]  # focus
        focus_range = self.inputs["FR"].sv_get()[0][0]  # focus range
        resolution = self.inputs["R"].sv_get()[0][0]  # resolution
        padding = self.inputs["P"].sv_get()[0][0]  # padding

        A = 1e5
        minX, maxX, minY, maxY, minZ, maxZ = [A, -A, A, -A, A, -A]
        for v in verts:
            minX = min(minX, v[0])
            maxX = max(maxX, v[0])
            minY = min(minY, v[1])
            maxY = max(maxY, v[1])
            minZ = min(minZ, v[2])
            maxZ = max(maxZ, v[2])

        bounds = [minX, maxX, minY, maxY, minZ, maxZ]

        # get volume origin, voxel dimension and padded bounds
        vO, vD, pB, pS = prepare_volume(bounds, resolution, padding)

        meanX = 0.5 * (minX + maxX)
        meanY = 0.5 * (minY + maxY)
        meanZ = 0.5 * (minZ + maxZ)

        sizeX = maxX - minX
        sizeY = maxY - minY
        sizeZ = maxZ - minZ

        # self.outputs["MinX"].sv_set([[minX]])
        # self.outputs["MaxX"].sv_set([[maxX]])

        # self.outputs["MinY"].sv_set([[minY]])
        # self.outputs["MaxY"].sv_set([[maxY]])

        # self.outputs["MinZ"].sv_set([[minZ]])
        # self.outputs["MaxZ"].sv_set([[maxZ]])

        self.outputs["Min"].sv_set([[minX, minY, minZ]])
        self.outputs["Max"].sv_set([[maxX, maxY, maxZ]])
        self.outputs["Mean"].sv_set([[(meanX, meanY, meanZ)]])
        self.outputs["Size"].sv_set([[(sizeX, sizeY, sizeZ)]])

        self.outputs["VO"].sv_set([[tuple(vO)]])
        self.outputs["VD"].sv_set([vD])
        self.outputs["PB"].sv_set([[tuple(pB)]])
        self.outputs["PS"].sv_set([[tuple(pS)]])


def register():
    bpy.utils.register_class(SvMiniVoxelizerNode)


def unregister():
    bpy.utils.unregister_class(SvMiniVoxelizerNode)
