# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bgl
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

# import mathutils
from mathutils import Vector, Matrix
import sverchok
from bpy.props import StringProperty, BoolProperty, FloatProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28

vertex_shader = '''
uniform mat4 viewProjectionMatrix;

in vec3 position;

void main()
{
  gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
}
'''

fragment_shader = '''
uniform vec4 color;
out vec4 outColor;

void main()
{
  outColor = color;
}
'''


geometry_shader = '''
layout(lines) in;
layout(triangle_strip, max_vertices=5) out;

uniform float lineWidth;

void main()
{
  vec3 start = gl_in[0].gl_Position.xyz;
  vec3 end = gl_in[1].gl_Position.xyz;

  vec3 line = normalize(end-start);
  vec3 lhs = cross(line, vec3(0.0, 0.0, 1.0));

  float line_width_scale = 0.1;
  float line_width = lineWidth * line_width_scale;
  vec3 dL = + lhs * 0.5 * line_width;
  vec3 dR = - lhs * 0.5 * line_width;

  gl_Position = gl_in[0].gl_Position + vec4(dL, 0);
  EmitVertex();

  gl_Position = gl_in[0].gl_Position + vec4(dR, 0);
  EmitVertex();

  gl_Position = gl_in[1].gl_Position + vec4(dL, 0);
  EmitVertex();

  gl_Position = gl_in[1].gl_Position + vec4(dR, 0);
  EmitVertex();

  gl_Position = gl_in[1].gl_Position + vec4(line_width * line, 0);
  EmitVertex();

  EndPrimitive();
}
'''

def screen_v3dMatrix(context, args):
    mdraw = MatrixDraw28()
    for matrix in args[0]:
        mdraw.draw_matrix(matrix)


def screen_v3dBGL(context, args):
    # region = context.region
    # region3d = context.space_data.region_3d

    shader = args[0]
    batch = args[1]
    line_color = list(args[2])
    line_width = args[3]

    matrix = bpy.context.region_data.perspective_matrix

    bgl.glLineWidth(5.0)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)

    shader.bind()
    shader.uniform_float("viewProjectionMatrix", matrix)
    shader.uniform_float("lineWidth", line_width)
    shader.uniform_float("color", line_color)

    batch.draw(shader)


class SvVDBasicLines(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: basic lines
    Tooltip: Basic GL line drawing

    not a very exciting node kids.
    """

    bl_idname = 'SvVDBasicLines'
    bl_label = 'Basic Line viewer'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_LINE_VIEWER'

    n_id: StringProperty(default='')
    activate: BoolProperty(name='Show', description='Activate', default=True, update=updateNode)

    edge_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1,
        default=(0.3, 0.3, 0.3, 1.0), name='edge color', size=4, update=updateNode)

    line_width: FloatProperty(
        name="Line Width",
        default=1.0, min=0.0, max=10.0,
        description="Line Width",
        update=updateNode)

    @property
    def fully_enabled(self):
        return "edges" in self.inputs

    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', 'verts')
        inew('SvStringsSocket', 'edges')
        inew('SvStringsSocket', 'Line Width').prop_name = "line_width"

    def draw_buttons(self, context, layout):
        layout.row().prop(self, "activate", text="ACTIVATE")
        r1 = layout.row(align=True)
        r1.label(icon="UV_EDGESEL")
        r1.prop(self, "edge_color", text='')


    def process(self):
        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            return

        n_id = node_id(self)
        callback_disable(n_id)

        verts_socket, edges_socket = self.inputs[:2]

        if verts_socket.is_linked and edges_socket.is_linked:

            propv = verts_socket.sv_get(deepcopy=False, default=[])
            prope = edges_socket.sv_get(deepcopy=False, default=[])

            coords = propv[0]
            indices = prope[0]

            shader = gpu.types.GPUShader(vertex_shader, fragment_shader, geocode=geometry_shader)
            # shader = gpu.types.GPUShader(vertex_shader, fragment_shader)

            batch = batch_for_shader(shader, 'LINES', {"position": coords}, indices=indices)

            line_color = self.edge_color[:]

            line_width = self.inputs["Line Width"].sv_get()[0][0]
            print("line_width=", line_width)

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3dBGL,
                'args': (shader, batch, line_color, line_width)
            }

            callback_enable(n_id, draw_data)
            return

    def sv_copy(self, node):
        self.n_id = ''

    def update(self):
        if not self.fully_enabled:
            return

        try:
            if not (self.inputs[0].other or self.inputs[1].other):
                callback_disable(node_id(self))
        except:
            print('vd basic lines update holdout', self.n_id)


def register():
    bpy.utils.register_class(SvVDBasicLines)


def unregister():
    bpy.utils.unregister_class(SvVDBasicLines)
