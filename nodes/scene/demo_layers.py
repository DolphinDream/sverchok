# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

layerNames = [ "Alpha", "Beta", "Gamma", "Delta" ]

def pre_updateNode(self, context):
    ''' must rebuild for each update'''
    print("pre updateNode")
    self.collection_name.clear()
    for node in self.id_data.nodes:
        if node.bl_idname == 'ViewerNode2':
            self.collection_name.add().name = node.name

    # updateNode(self, context)

class SvVDMK2LayerOperatorCallback(bpy.types.Operator):
    """delegate changes to node"""
    bl_idname = "nodes.sv_vdmk2_layer_cb"
    bl_label = "Sv Ops Layer vd"

    fn_name = bpy.props.StringProperty()
    nt_name = bpy.props.StringProperty()
    node_name = bpy.props.StringProperty()
    lg_name = bpy.props.StringProperty() # layer group name

    def execute(self, context):
        n = context.node
        getattr(n, self.fn_name)(self.lg_name)
        return {"FINISHED"}

class SvVDMK2Layer(bpy.types.PropertyGroup):

    collection_name = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    vd_node_name = bpy.props.StringProperty(update=pre_updateNode)
    # vd_enum_nodes = bpy.props.EnumProperty()
    vd_node_viewstate = bpy.props.BoolProperty()

class SvVDMK2LayerGroup(bpy.types.PropertyGroup):

    name = bpy.props.StringProperty()
    collection_name = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    vd_layers = bpy.props.CollectionProperty(name="Viewer Draw Layers", type=SvVDMK2Layer)
    visible = bpy.props.BoolProperty(name="Visible", default=True)

class SvVDMK2LayerNode(bpy.types.Node, SverchCustomTreeNode):
    ''' VDMK layer teste '''
    bl_idname = 'SvVDMK2LayerNode'
    bl_label = 'VDMK Layers'
    bl_icon = 'CAMERA_STEREO'

    # vd_layers = bpy.props.CollectionProperty(name="Viewer Draw Layers", type=SvVDMK2Layer)
    vd_layer_groups = bpy.props.CollectionProperty(name="Viewer Draw Layer Groups", type=SvVDMK2LayerGroup)

    def sv_init(self, context):
        self.width = 300

    def draw_buttons(self, context, layout):

        cb = SvVDMK2LayerOperatorCallback.bl_idname
        tree = self.id_data

        for layerGroup in self.vd_layer_groups:
            print("Layer group:", layerGroup.name)
            # print("Layer group:", layerGroup.collection_name)
            row = layout.row(align=True)
            split = row.split(0.9)
            split.label(layerGroup.name)
            # split.prop(layerGroup, "visible", toggle=True, icon="VISIBLE_IPO_ON", text="")
            onButton = split.operator(cb, text='', icon='VISIBLE_IPO_ON')
            onButton.fn_name = "ops_show_hide_layer_group"
            onButton.lg_name = layerGroup.name

            box = layout.box()

            for viewer in layerGroup.vd_layers:
                row = box.row(align=True)
                part1 = row.split(0.6)
                part1.prop_search(viewer, "vd_node_name", viewer, 'collection_name', icon='OBJECT_DATA', text='')

                viewer_node = tree.nodes.get(viewer.vd_node_name)
                if viewer_node:
                    part2 = part1.split(align=True)
                    part2.prop(viewer_node, "activate", toggle=True, icon='VISIBLE_IPO_ON', text='')
                    part2.prop(viewer_node, "shading", toggle=True, icon='LAMP_SPOT', text='')
                    part2.prop(viewer_node, "vertex_colors", text='')
                    part2.prop(viewer_node, "edge_colors", text='')
                    part2.prop(viewer_node, "face_colors", text='')

            addButton = box.row().operator(cb, text='', icon='PLUS')
            addButton.fn_name = "ops_add_new_layer"
            addButton.lg_name = layerGroup.name

        layout.row().operator(cb, text='', icon='PLUS').fn_name = "ops_add_new_layer_group"

    def process(self):
        ...

    def ops_add_new_layer(self, layer_group_name):
        print("add new layer to group: ", layer_group_name)
        print("number of layer groups: ", len(self.vd_layer_groups))
        for layerGroup in self.vd_layer_groups:
            if layerGroup.name == layer_group_name:
                m = layerGroup.vd_layers.add()
                m.vd_node_name = ''
        # m = self.vd_layer_groups.vd_layers.add()
        # m.vd_node_name = ''

    def ops_add_new_layer_group(self, layer_group_name):
        print("add new layer group")
        m = self.vd_layer_groups.add()
        m.name = layerNames[len(self.vd_layer_groups)-1]
        m.vd_node_name = ''

    def ops_show_hide_layer_group(self, layer_group_name):
        print("show/hide layer group: ", layer_group_name)
        for layerGroup in self.vd_layer_groups:
            if layerGroup.name == layer_group_name:
                layerGroup.visible = not layerGroup.visible
                for layer in layerGroup.vd_layers:
                    print("toggle layer visibility")
                    tree = self.id_data
                    viewer_node = tree.nodes.get(layer.vd_node_name)
                    viewer_node.activate = layerGroup.visible

    def ops_activate_helper(self, mode):
        print("call activate helper")
        for viewer in self.vd_layers:
            viewer_node = tree.nodes.get(viewer.vd_node_name)
            if viewer_node:
                viewer_node.activate = mode

    def ops_hide_layers(self):
        print("hide layer")
        self.ops_activate_helper(False)



classes = SvVDMK2LayerOperatorCallback, SvVDMK2Layer, SvVDMK2LayerGroup, SvVDMK2LayerNode

def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]

def unregister():
    _ = [bpy.utils.register_class(cls) for cls in reverse(classes)]


if __name__ == '__main__':
    try:
        register()
    except Exception as err:
        unregister()
        register()

    nodes = bpy.data.node_groups['NodeTree'].nodes
    newnode = nodes.new('SvVDMK2LayerNode')
    # layer_1 = newnode.vd_layers.add()
    # layer_1.vd_node_name = "Viewer Draw"
    # layer_1.vd_node_viewstate = nodes[layer_1.vd_node_name].activate
    # layer_2 = newnode.vd_layers.add()
    # layer_2.vd_node_name = "Viewer Draw.001"
    # layer_2.vd_node_viewstate = nodes[layer_2.vd_node_name].activate
    # layer_3 = newnode.vd_layers.add()
    # layer_3.vd_node_name = "Viewer Draw.002"
    # layer_3.vd_node_viewstate = nodes[layer_3.vd_node_name].activate