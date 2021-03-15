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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, StringProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

import mmap
import os

from mathutils import Quaternion, Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

from pprint import pprint

loaded_filepaths_dict = dict()

DEBUG = False

def read_matrix(data, rows, columns, array_size, convertTo4x4):
    matrix_list = []
    if rows == 3 and columns == 4: # 3x4 matrices
        for n in range(array_size): # for all in the array

            if DEBUG:
                print("Reading matrix %d of %d ..." % (n, array_size))

             # read the empty line (skip)
            data.readline()

            # read the next matrix elements from the next <rows> lines
            matrix = []
            for r in range(rows):
                line = data.readline().rstrip()
                # print("line = ", line)
                row = list(map(float, line.split()))
                if DEBUG:
                    print("row = ", row)
                matrix.append(row)

            # convert into a 4x4 matrix (add last row)
            if convertTo4x4:
                matrix.append([0.0, 0.0, 0.0, 1.0])

            # append to the list of matrices
            matrix_list.append(matrix)
            if DEBUG:
                print("loaded matrix: ", matrix)
                print("")

    return [Matrix(m) for m in matrix_list]


def read_vector(data, rows, columns, array_size, convertTo4x4):
    vector_list = []
    if rows == 3 and columns == 1: # 3x1 vectors
        for n in range(array_size): # for all in the array

            if DEBUG:
                print("Reading vector %d of %d ..." % (n, array_size))

             # read the empty line (skip)
            data.readline()

            # read the next vector elements from the next <rows> lines
            vector = []
            for r in range(rows):
                line = data.readline().rstrip()
                if DEBUG:
                    print("line = ", line)
                row = list(map(float, line.split()))[0]
                if DEBUG:
                    print("row=", row)
                vector.append(row)

            # convert into a 4x4 matrix
            # if convertTo4x4:
            #     m = Matrix.Translation(vector)
            #     # vector.append(1.0)

            # append to the list of vectors
            vector_list.append(vector)
            if DEBUG:
                print("loaded vector: ", vector)

    return [Matrix.Translation(v) for v in vector_list]


def load_matrix_file_data(filepath):
    # The Matrix file format is :

    # ROWS COLUMNS ARRAY_SIZE
    #
    # R11 R12 R13 TX
    # R21 R22 R23 TY
    # R31 R32 R33 TZ
    #
    # R11 R12 R13 TX
    # R21 R22 R23 TY
    # R31 R32 R33 TZ
    # ...

    print("Loading Matrix from file: ", filepath)

    with open(filepath, 'rt') as file:
        data = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)

        # read the matrix dimensions (skip)
        line = data.readline().rstrip()
        dimensions = list(map(int, line.split()))
        rows, columns, array_size = dimensions
        if DEBUG:
            print("matrix dimensions = ", dimensions)
            print("rows = ", rows)
            print("columns = ", columns)
            print("array_size = ", array_size)

        # if 3 x 4 x 1 .. read a matrix                 => one 4x4 matrix
        # if 3 x 1 x 1 .. read a 3x1 point/vector/axis  => one 3x1 vector
        # if 3 x 4 x N .. read multiple(N) 3x4 matrices => multiple 4x4 matrices
        # if 3 x 1 x N .. read multiple(N) 3x1 vectors  => multiple 3x1 vectors

        if columns == 1: # read vector type
            result = read_vector(data, rows, columns, array_size, True)
            rtype = "VECTOR"
        else: # read matrix type
            result = read_matrix(data, rows, columns, array_size, True)
            rtype = "MATRIX"

        # done reading data.. close the file
        data.close()

        if DEBUG:
            print("returned matrix: ", result)
            print("")

    return result


class SvMatrixLoadNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Matrix, Loading
    Tooltip: Load Matrix from file with SN matrix format
    """
    bl_idname = 'SvMatrixLoadNode'
    bl_label = 'Load Matrix'
    sv_icon = 'SV_MATRIX_IN'

    def add_filepath(self, filepath):
        ''' Callback from file find operator to add a path'''
        filename = os.path.basename(filepath)
        print("* Adding filepath/filename: ", filepath, filename)
        loaded_filepaths_dict[filename] = filepath

    def set_filepath(self, filepath):
        self.file_path = filepath
        # updateNode(self, context)

    def update_path(self, context):
        print("* Updating file path: ", self.file_path)
        updateNode(self, context)

    def update_path_selection(self, context):
        print("* Selected path: ", self.selected_filename)
        self.file_path = loaded_filepaths_dict[self.selected_filename]
        # updateNode(self, context)

    def loaded_filepath_items(self, context):
        filepath_items = [(k, k, v, i) for i, (k,v) in enumerate(loaded_filepaths_dict.items())]
        # pprint(filepath_items)
        return filepath_items

    file_path: StringProperty(
        name="File path",
        description="File path of the currently selected file",
        default="", update=update_path)

    selected_filename: EnumProperty(
        name="Selected file from loaded files",
        items=loaded_filepath_items,
        update=update_path_selection)

    unique_index: BoolProperty(
        name="Unique Index",
        description="Keep input index values unique",
        default=True, update=updateNode)

    set_identity: BoolProperty(
        name="Set Identity",
        description="Set all matrices to identity",
        default=False, update=updateNode)

    def prev_file_item(self, context):
        keys = list(loaded_filepaths_dict.keys())
        this_index = keys.index(self.selected_filename)
        prev_index = (this_index - 1) % len(keys)
        prev_filename = keys[prev_index]
        self.selected_filename = prev_filename
        if DEBUG:
            print("PREV file callback")
            print("this file = ", self.selected_filename)
            print("number of files = ", len(keys))
            print("this index = ", this_index)
            print("prev index = ", prev_index)
            print("prev file = ", prev_filename)

    def next_file_item(self, context):
        keys = list(loaded_filepaths_dict.keys())
        this_index = keys.index(self.selected_filename)
        next_index = (this_index + 1) % len(keys)
        next_filename = keys[next_index]
        self.selected_filename = next_filename
        if DEBUG:
            print("NEXT file callback")
            print("this file = ", self.selected_filename)
            print("number of files = ", len(keys))
            print("this index = ", this_index)
            print("next index = ", next_index)
            print("next file = ", next_filename)

    def reset_file_items(self, context):
        loaded_filepaths_dict.clear()
        # self.selected_filename = ""

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvStringsSocket', "Index")
        self.outputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvStringsSocket', "Filename")
        self.outputs.new('SvStringsSocket', "Index")

    def draw_buttons(self, context, layout):
        row = layout.row()

        row.prop(self, "selected_filename", text="")

        box = layout.box()
        row = box.row(align=True)

        cb = SvNavigateFilelistCallback.bl_idname

        # any files loaded ? => show reset button
        if len(loaded_filepaths_dict) :
            reset_op = row.operator(cb, text="Reset")
            reset_op.function_name = "reset_file_items"

        load_op = row.operator("node.sv_matrix_file_importer", text="Load")
        load_op.idname = self.name
        load_op.idtree = self.id_data.name

        # more than one file loaded and no index socket connected? => show
        if len(loaded_filepaths_dict) > 1 and not self.inputs["Index"].is_linked:
            prev_button = row.operator(cb, text='', icon="PLAY_REVERSE")
            prev_button.function_name = "prev_file_item"
            next_button = row.operator(cb, text='', icon="PLAY")
            next_button.function_name = "next_file_item"

        row = layout.row()
        row.prop(self, "unique_index")
        row.prop(self, "set_identity")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        input_index = self.inputs["Index"].sv_get(default=[[]])[0]

        print("input index = ", input_index)

        # sanitize the inputs (all indices must be within the number of loaded files)
        max_n = max(0, len(loaded_filepaths_dict) - 1)
        input_index = list(map(lambda n: min(int(n), max_n), input_index))
        print("sanitized input index = ", input_index)

        if self.unique_index:
            input_index = list(set(input_index))
            print("unique input index = ", input_index)

        filenames = list(loaded_filepaths_dict.keys())

        matrix_list = []
        filename_list = []
        index_list = []

        # index socket is connected? => use it!
        if self.inputs["Index"].is_linked:
            index_list = input_index
        else: # use the selection from the drop down list
            index = filenames.index(self.selected_filename)
            print("use drop down selection index = ", index)
            print("selected filename: ", self.selected_filename)
            index_list = [index]

        filename_list = [filenames[i] for i in index_list]
        print("filename_list = ", filename_list)

        filepath_list = [loaded_filepaths_dict[f] for f in filename_list]
        if self.set_identity:
            matrix_list = [[Matrix().Identity(4)] * len(filename_list)]
        else:
            matrix_list = [load_matrix_file_data(f) for f in filepath_list]
        print("matrix_list = ", matrix_list)

        self.outputs['Matrix'].sv_set(matrix_list[0])
        self.outputs['Filename'].sv_set([filename_list])
        self.outputs['Index'].sv_set([index_list])


class SvNavigateFilelistCallback(bpy.types.Operator):
    ''' Navigate filelist callback (prev/next) '''
    bl_idname = "nodes.sn_navigate_file_list"
    bl_label = "Navigate file list Items"
    bl_description = "Navigate Prev/Next files in the list"

    function_name: StringProperty()  # what function to call

    def execute(self, context):
        n = context.node
        getattr(n, self.function_name)(context)
        return {"FINISHED"}


class SvMatrixFileImporterOp(bpy.types.Operator, ImportHelper):
    ''' Matrix Import Helper '''
    bl_idname = "node.sv_matrix_file_importer"
    bl_label = "Matrix File Importer"

    filename_ext = ".mat"

    filter_glob: StringProperty(
        default="*.mat",
        options={'HIDDEN'},
        )

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024, default="", subtype='FILE_PATH')

    idname: StringProperty(
        name='idname', description='name of parent node', default='')

    idtree: StringProperty(
        name='idtree', description='name of parent tree', default='')

    def get_node(self):
        node_group = bpy.data.node_groups[self.idtree]
        node = node_group.nodes[self.idname]
        return node

    def execute(self, context):
        dirname = os.path.dirname(self.filepath)
        filepaths = [os.path.join(dirname, f.name) for f in self.files]
        print("selected files: ", filepaths)

        n = self.get_node()
        for p in filepaths:
            print("setting file path: ", p)
            n.add_filepath(p)
        n.set_filepath(filepaths[0])

        print("selected file path: ", n.file_path)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(SvMatrixLoadNode)
    bpy.utils.register_class(SvNavigateFilelistCallback)
    bpy.utils.register_class(SvMatrixFileImporterOp)


def unregister():
    bpy.utils.unregister_class(SvMatrixFileImporterOp)
    bpy.utils.unregister_class(SvNavigateFilelistCallback)
    bpy.utils.unregister_class(SvMatrixLoadNode)


if __name__ == '__main__':
    register()
