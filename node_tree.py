# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Generated documentation - http://nortikin.github.io/sverchok/apidocs/sverchok/node_tree.html

The module includes functionality of main tree (not group tree) and base class
for all nodes (`SverchCustomTreeNode`).

## Blender Data Blocks IDs

Memory addresses of all Blender objects are not constant, read more in
[Blender docs](https://docs.blender.org/api/current/info_gotcha.html#help-my-script-crashes-blender).
So an object itself can be an identifier (at least for a long period of time).
For that reason we have to create our own identifiers (for node trees, nodes,
sockets) to associate data with them which can't be assigned to Blender
objects directly.

Identifiers generated by trees, nodes, sockets are unique for all objects in
a file (or probably even between files =).
"""


import inspect
import time
from contextlib import contextmanager
from itertools import chain, cycle
from typing import Iterable, final

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import NodeTree, NodeSocket

from sverchok.core.sv_custom_exceptions import SvNoDataError, DependencyError
import sverchok.core.events as ev
import sverchok.dependencies as sv_deps
from sverchok.core.event_system import handle_event
from sverchok.data_structure import classproperty, post_load_call
from sverchok.utils import get_node_class_reference
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.utils.docstring import SvDocstring
import sverchok.utils.logging
from sverchok.utils.logging import debug, catch_log_error

from sverchok.ui import color_def
from sverchok.ui.nodes_replacement import set_inputs_mapping, set_outputs_mapping
from sverchok.ui import bgl_callback_nodeview as sv_bgl


class SvNodeTreeCommon:
    """Common class for all Sverchok trees (regular trees and group ones)"""

    #: Identifier of the tree, should be used via `SvNodeTreeCommon.tree_id` property.
    tree_id_memory: StringProperty(default="")

    sv_show_time_nodes: BoolProperty(
        name="Node times",
        default=False,
        options=set(),
        update=lambda s, c: handle_event(ev.TreeEvent(s)))
    show_time_mode: EnumProperty(
        items=[(n, n, '') for n in ["Per node", "Cumulative"]],
        options=set(),
        update=lambda s, c: handle_event(ev.TreeEvent(s)),
        description="Mode of showing node update timings",
    )

    @property
    def tree_id(self):
        """Identifier of the tree. [Rational](#blender-data-blocks-ids)."""
        if not self.tree_id_memory:
            self.tree_id_memory = str(hash(self) ^ hash(time.monotonic()))
        return self.tree_id_memory

    def update_gl_scale_info(self, origin=None):
        """
        the nodeview scale and dpi differs between users and must be queried to get correct nodeview
        x,y and dpi scale info.

        this is instead of calling `get_dpi_factor` on every redraw.
        """

        debug(f"update_gl_scale_info called from {origin or self.name}")
        try:
            from sverchok.utils.context_managers import sv_preferences
            with sv_preferences() as prefs:
                prefs.set_nodeview_render_params(None)
        except Exception as err:
            debug('failed to get gl scale info', err)

    @contextmanager
    def init_tree(self):
        """It suppresses calling the `UpdateNodes.update` method of nodes,
        main usage of it is during generating tree with python (JSON import)

            with tree.init_tree():
                do_something()
        """
        is_already_initializing = 'init_tree' in self
        if is_already_initializing:
            yield self
        else:
            self['init_tree'] = ''
            try:
                yield self
            finally:
                del self['init_tree']

    def update_ui(self, nodes_errors, update_time):
        """ The method get information about node statistic of last update from the handler to show in view space
        The method is usually called by main handler to reevaluate view of the nodes in the tree
        even if the tree is not in the Live update mode"""
        update_time = update_time if self.sv_show_time_nodes else cycle([None])
        for node, error, update in zip(self.nodes, nodes_errors, update_time):
            if hasattr(node, 'update_ui'):
                node.update_ui(error, update)


class SverchCustomTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Nodes'
    bl_icon = 'RNA'

    def turn_off_ng(self, context):
        """
        Turn on/off displaying objects in viewport generated by viewer nodes.
        Viewer nodes should have `show_viewport` method which takes 'to_show' bool argument
        """
        for node in self.nodes:
            try:
                node.show_viewport(self.sv_show)
            except AttributeError:
                pass

    def on_draft_mode_changed(self, context):
        """
        This is triggered when `SverchCustomTree.sv_draft` mode of the tree is toggled.
        It switches properties of some nodes from normal to draft and vise versa,
        and update the nodes.
        """
        draft_nodes = []
        for node in self.nodes:
            if hasattr(node, 'does_support_draft_mode') and node.does_support_draft_mode():
                draft_nodes.append(node)
                node.on_draft_mode_changed(self.sv_draft)

        # From the user perspective, some of node parameters
        # got new parameter values, so the setup should be recalculated;
        # but technically, node properties were not changed
        # (only other properties were shown in UI), so enabling/disabling
        # of draft mode does not automatically trigger tree update.
        # Here we trigger it manually.

        if draft_nodes:
            self.update_nodes(draft_nodes)

    sv_process: BoolProperty(
        name="Process",
        default=True,
        description='Update upon tree and node property changes',
        update=lambda s, c: handle_event(ev.TreeEvent(s)),
        options=set(),
    )
    """If enabled it means that the tree will be evaluated upon changes in its
    topology, changes in node properties or scene changes made by user.
    This property does not effect evaluation upon `SverchCustomTree.sv_animate`
    changes or by re-update all nodes operator. Enabling the property will call
    the tree topology changes trigger."""

    sv_animate: BoolProperty(
        name="Animate",
        default=True,
        description='Animate this layout',
        options=set())
    """If enabled the tree will be reevaluated upon frame change. The update can
    effect not all nodes but only those which have property 
    `UpdateNodes.is_animatable` enabled."""

    sv_show: BoolProperty(
        name="Show",
        default=True,
        description='Show this layout',
        update=turn_off_ng,
        options=set())
    """See `SverchCustomTree.turn_off_ng"""

    sv_show_socket_menus: BoolProperty(
        name = "Show socket menus",
        description = "Display socket dropdown menu buttons. NOTE: options that are enabled in those menus will be effective regardless of this checkbox!",
        default = False,
        options=set())
    """Display socket dropdown menu buttons (only for output).
    Read more in [user documentation](http://nortikin.github.io/sverchok/docs/user_interface/input_menus.html).
    
    ![image](https://user-images.githubusercontent.com/28003269/193573106-6f8a04b7-0e19-489c-965c-4f48008afd69.png)"""

    #: Draft mode replaces selected properties of certain nodes with smaller values to lighten cpu load.
    sv_draft: BoolProperty(
        name="Draft",
        description="Draft (simplified processing) mode",
        default=False,
        update=on_draft_mode_changed,
        options=set(),
    )

    sv_scene_update: BoolProperty(
        name="Scene update",
        description="Update upon changes in the scene",
        options=set(),
        default=True)
    """If enabled together with `SverchCustomTree.sv_process` the tree will be
    reevaluated upon changes in the scene. It will effect only nodes with
    `UpdateNodes.is_interactive` property enabled. The scene changes can be:
    
      - moving objects
      - changing edit / object mode
      - mesh editing
      - assign materials
      - etc.
    """

    def update(self):
        """This method is called if collection of nodes or links of the tree was changed"""
        handle_event(ev.TreeEvent(self))

    def force_update(self):
        """Update whole tree from scratch"""
        # ideally we would never like to use this method but we live in the real world
        handle_event(ev.ForceEvent(self))

    def update_nodes(self, nodes):
        """This method expects to get list of its nodes which should be updated"""
        return handle_event(ev.PropertyEvent(self, nodes))

    def scene_update(self):
        """This method should be called by scene changes handler.
        It ignores scene events generated by sverchok trees (they modify Bledner
        data what cause execution of a scene handler). It updates nodes with
        `UpdateNodes.is_interactive` enabled."""
        handle_event(ev.SceneEvent(self))

    def process_ani(self, frame_changed: bool, animation_playing: bool):
        """
        Process the Sverchok node tree if animation layers show true.
        For `sverchok.core.handlers.sv_update_handler`.
        """
        handle_event(ev.AnimationEvent(self, frame_changed, animation_playing))


class UpdateNodes:
    """Everything related with update system of nodes"""

    n_id: StringProperty(options={'SKIP_SAVE'})
    """Identifier of the node, should be used via `UpdateNodes.node_id` property.
    
    ```text
    ⚠️ There is no sense to override this property
    ```
    """

    @property
    def node_id(self):
        """Identifier of the node. [Rational](#blender-data-blocks-ids)"""
        if not self.n_id:
            self.n_id = str(hash(self) ^ hash(time.monotonic()))
        return self.n_id

    def update_interactive_mode(self, context):
        """When `UpdateNodes.is_interactive` mode is on the method updates only
        outdated nodes"""
        if self.is_interactive:
            self.process_node(context)

    is_interactive: BoolProperty(
        default=True,
        description="Update node upon changes in the scene",
        update=update_interactive_mode,
        name="Interactive")
    """When this option is on arbitrary changes in scene will update this node.
    Those changes can be:  

      - moving objects
      - changing edit / object mode
      - mesh editing
      - assign materials
      - etc.

    This option is used to display it in UI so user could switch it on/off. 
    it should be set to True (together with `UpdateNodes.is_scene_dependent`)
    for nodes which read data from blender scene."""

    is_scene_dependent = False
    """The option switches on to display automatically the `UpdateNodes.is_interactive`
    option as a button inside a node but in this case the `SverchCustomTreeNode.draw_buttons`
    method should not be overridden and `SverchCustomTreeNode.sv_draw_buttons`
    should be used instead.
    
    ![image](https://user-images.githubusercontent.com/28003269/193401197-e5da276b-78bd-4523-8a8d-2e00fc935bda.png)
    """

    def refresh_node(self, context):
        """Together with `UpdateNodes.refresh` property it is used as an
        operator which updates the node."""
        if self.refresh:
            self.refresh = False
            self.process_node(context)

    refresh: BoolProperty(name="Update Node",
                          description="Update Node",
                          update=refresh_node)
    """See `UpdateNodes.refresh_node`.
    
    ![image](https://user-images.githubusercontent.com/28003269/193505561-395ca65c-3354-4e23-b5f7-765b2d830e4b.png)
    
    The button is automatically displayed when at least `UpdateNodes.is_scene_dependent`
    or `UpdateNodes.is_animation_dependent` is on. Also the node should use
    `SverchCustomTreeNode.sv_draw_buttons`.
    """

    is_animatable: BoolProperty(name="Animate Node",
                                description="Update Node on frame change",
                                default=True,
                                update=lambda s, c: s.process_node(c))
    """A switch for user to make a node to update on frame changes in a scene.
    Use `UpdateNodes.is_animation_dependent` to display the option in node UI."""

    is_animation_dependent = False
    """ Use this to display the `UpdateNodes.is_animatable` option in node UI.
    Also the node should use `SverchCustomTreeNode.sv_draw_buttons`.
    
    ![image](https://user-images.githubusercontent.com/28003269/193507101-60a28c3f-50a1-4117-a66f-25b0b4e07e13.png)"""

    def sv_init(self, context):
        """
        This method will be called during node creation
        Typically it is used for socket creating and assigning properties to sockets
        """
        pass

    def sv_update(self):
        """
        This method can be overridden in inherited classes.
        It will be triggered upon any `node tree` editor changes (new/copy/delete links/nodes).
        Calling of this method is unordered among other calls of the method of other nodes in a tree.
        Typically, it is used to change output socket types dependent on what
        type is connected to a node.
        """
        pass

    def sv_copy(self, original):
        """
        Override this method to do anything node-specific (clean properties)
        at the moment of node being copied.
        """
        pass

    def sv_free(self):
        """
        Override this method to do anything node-specific upon node removal
        """
        pass

    @final
    def init(self, context):
        """
        This function is triggered upon node creation, functionality:

          - sets default colors of the node
          - show alpha/beta state of the node
          - logs further  errors
          - delegates further initialization information to `UpdateNodes.sv_init`
        """
        if self.sv_default_color:
            self.use_custom_color = True
            self.color = self.sv_default_color

        if hasattr(self, 'sv_icon') and self.sv_icon in {'SV_ALPHA', 'SV_BETA'}:
            frame = self.id_data.nodes.new("NodeFrame")
            self.parent = frame
            frame.label = f'{"Alpha" if self.sv_icon == "SV_ALPHA" else "Beta"} Node'
            frame.use_custom_color = True
            frame.color = (0.3, 0, 0.7)
            frame.shrink = True
            frame['in_development'] = True  # can be used to distinguish the frame

        with catch_log_error():
            self.sv_init(context)

    def sv_new_input(self, socket_type, name, **attrib_dict):
        """Alias of creating and setting socket properties. Example:

        ```py
        self.sv_new_input('SvStringsSocket', "Polygons",
                          hide_safe=True, prop_name='scale_factor')
        ```"""
        socket = self.inputs.new(socket_type, name)
        for att in attrib_dict:
            setattr(socket, att, attrib_dict[att])
        return socket

    @final
    def free(self):
        """Called upon the node removal

          - calls `UpdateNodes.sv_free
          - cleans socket data catch
          - cleans drawings in the tree editor space"""
        self.sv_free()

        for s in chain(self.inputs, self.outputs):
            s.sv_forget()

        self.update_ui()

    @final
    def copy(self, original):
        """Called upon the node being copied

          - refreshes node and socket ids
          - calls `UpdateNodes.sv_copy`"""
        self.n_id = ""
        for sock in chain(self.inputs, self.outputs):
            sock.s_id = ''
        self.sv_copy(original)

    @final
    def update(self):
        """
        The method will be triggered upon editor changes, typically before node
        tree update method. It calls `UpdateNodes.sv_update`.

        ```text
        ⚠️ It checks special flag in the tree of the node. The flag
        is set by json import module. If the tree has the flag the node skips
        farther execution of the method. This is done for performance reason
        and actually there is no reason to execute the method since the import
        module totally controls building of the tree.
        ```
        The flag can be set by `SvNodeTreeCommon.init_tree`.
        """
        if 'init_tree' in self.id_data:  # tree is building by a script - let it do this
            return

        self.sv_update()

    def update_ui(self, error=None, update_time=None):
        """This method is intended to use by update system to show node errors
        in the tree editors space and to show execution time"""
        sv_settings = bpy.context.preferences.addons[sverchok.__name__].preferences
        exception_color = sv_settings.exception_color
        no_data_color = sv_settings.no_data_color
        error_pref = "error"
        update_pref = "update_time"

        # update error colors
        if error is not None:
            color = no_data_color if isinstance(error, SvNoDataError) else exception_color
            self.set_temp_color(color)
            sv_bgl.draw_text(self, str(error), error_pref + self.node_id, color, 1.3, "UP")
        else:
            sv_bgl.callback_disable(error_pref + self.node_id)
            self.set_temp_color()

        # show update timing
        if update_time is not None:
            update_time = int(update_time * 1000)
            sv_bgl.draw_text(self, f'{update_time}ms', update_pref + self.node_id, align="UP", dynamic_location=False)
        else:
            sv_bgl.callback_disable(update_pref + self.node_id)

    def insert_link(self, link):
        """It will be triggered only if one socket is connected with another by user.
        There is no useful use for the trigger currently."""

    def process_node(self, context):
        """Call this method to revaluate the node whenever its properties
        were changed"""
        self.id_data.update_nodes([self])


class NodeUtils:
    """
    Helper methods.
    Most of them have nothing related with nodes and using as aliases of some functionality.
    The class can be surely ignored during creating of new nodes.
    """
    def get_logger(self):
        if hasattr(self, "draw_label"):
            name = self.draw_label()
        else:
            name = self.label
        if not name:
            name = self.bl_label
        if not name:
            name = self.__class__.__name__

        # add information about the module location
        frame, _, line, *_ = inspect.stack()[2]
        module = inspect.getmodule(frame)
        module_name = module.__name__ if module is not None else ''
        name = f'{module_name} {line} ({name})'
        return sverchok.utils.logging.getLogger(name)

    def debug(self, msg, *args, **kwargs):
        self.get_logger().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.get_logger().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.get_logger().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.get_logger().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.get_logger().exception(msg, *args, **kwargs)

    def wrapper_tracked_ui_draw_op(self, layout_element, operator_idname, **keywords):
        """
        this wrapper allows you to track the origin of a clicked operator, by automatically passing
        the node_name and tree_name to the operator.

        example usage:

            row.separator()
            self.wrapper_tracked_ui_draw_op(row, "node.view3d_align_from", icon='CURSOR', text='')

        """
        op = layout_element.operator(operator_idname, **keywords)
        op.node_name = self.name
        op.tree_name = self.id_data.name
        return op

    def get_bpy_data_from_name(self, identifier, bpy_data_kind):  # todo, method which have nothing related with nodes
        """
        fail gracefully?
        This function acknowledges that the identifier being passed can be a string or an object proper.
        for a long time Sverchok stored the result of a prop_search as a StringProperty, and many nodes will
        be stored with that data in .blends, here we try to permit older blends having data stored as a string,
        but newly used prop_search results will be stored as a pointerproperty of type bpy.types.Object
        regarding the need to trim the first 3 chars of a stored StringProperty, best let Blender devs enlighten you
        https://developer.blender.org/T58641

        example usage inside a node:

            text = self.get_bpy_data_from_name(self.filename, bpy.data.texts)

        if the text does not exist you get None
        """
        if not identifier:
            # this can happen if a json import goes through attributes arbitrarily.
            # self.info("no identifier passed to the get_bpy_data_from_name function.")
            return None

        try:
            if isinstance(identifier, bpy.types.Object) and identifier.name in bpy_data_kind:
                return bpy_data_kind.get(identifier.name)  # todo it looks ridiculous to search known object

            elif isinstance(identifier, str):
                if identifier in bpy_data_kind:
                    return bpy_data_kind.get(identifier)
                elif identifier[3:] in bpy_data_kind:
                    return bpy_data_kind.get(identifier[3:])
                
                # something went wrong. the blend does not contain the objectname
                self.info(f"{identifier} not found in {bpy_data_kind}, returning None instead")
                if bpy_data_kind.bl_rna.identifier == 'BlendDataTexts':
                    # if we are in texts and this key is not found:
                    # - it's possible the named datablock incurred name collision
                    # - or it has not yet been created (usually json import, attribute order issue)
                    file_names = {t.name for t in bpy_data_kind}
                    self.info(f"The currently loaded blend file does contain the following text files {file_names}")


        except Exception as err:
            self.error(f"identifier '{identifier}' not found in {bpy_data_kind} - with error {err}")

        return None

    def safe_socket_remove(self, kind, key, failure_message=None):
        sockets = getattr(self, kind)
        if key in sockets:
            sockets.remove(sockets[key])
        else:
            canned_msg = f"{self.name}.{kind} has no socket named {key} - did not remove"
            self.debug(failure_message or canned_msg)


class NodeDependencies:
    """The mix-in keeps information about optional libraries which are used by
    a node. Names of libraries should be assigned to `NodeDependencies.sv_dependencies`
    only if a node can't work without them. In this case it won't be possible
    to add the node into a node tree and its tooltip will show the names of
    dependent libraries.

    ![image](https://user-images.githubusercontent.com/28003269/197936383-e6b80beb-43f2-4168-8082-5ba92f1e72f4.png)

    If opened tree already has dependent nodes the Dependency error will be
    shown with names of dependent libraries.

    ![image](https://user-images.githubusercontent.com/28003269/197694508-da963845-574b-4087-8c55-108c9b41ba47.png)

    If libraries are optional and a node has a mode which lets to execute the
    node without them don't assign any libraries to `NodeDependencies.sv_dependencies`.
    Check availability the libraries manually inside the `process` method and
    call the `DependencyError` if appropriate.
    """
    sv_dependencies: set[str] = set()  #: dependent module names

    _missing_dependency = None
    _dependency_error = None

    @classproperty
    def missing_dependency(cls) -> bool:
        """Returns True if any of dependent libraries are not installed"""
        if cls._missing_dependency is None:
            for dep in cls.sv_dependencies:
                if getattr(sv_deps, dep) is None:
                    cls._missing_dependency = True
                    break
            else:
                cls._missing_dependency = False
        return cls._missing_dependency

    @property
    def dependency_error(self):
        """Returns DependencyError instance with the library names if some of
        them are not installed or None"""
        if self.missing_dependency:
            if self._dependency_error is None:
                msg = ", ".join(f'"{s}"' for s in self.sv_dependencies)
                if len(self.sv_dependencies) == 1:
                    self._dependency_error = DependencyError(f'{msg} is not installed')
                else:
                    self._dependency_error = DependencyError(f'{msg} are not installed')
            return self._dependency_error
        return


class SverchCustomTreeNode(UpdateNodes, NodeUtils, NodeDependencies):
    """Base class for all nodes. Documentation of a custom node class is used
    to give information about the node UI. Minimal example of a custom node:

    ```py
    class SvSomeOperationNode(SverchCustomTreeNode, bpy.types.Node):
    \"""
    Triggers: vector multiply scale  # <- tags
    Tooltip: This node performs some operation

    Merely for illustration of node creation workflow  # Description
    \"""
    bl_idname = 'SvSomeOperationNode'  # should be added to `sverchok/index.md` file
    bl_label = 'Name shown in menu'
    bl_icon = 'GREASEPENCIL'
    ```

    It's possible to apply Alpha/Beta icons to sv_icon class attribute of the
    node to mark a node as in development state and that it can change its
    behaviour or even be removed. Usually new nodes should be marked in this way
    until new release.

        class Node:
            sv_icon = 'SV_ALPHA'  # or 'SV_BETA'

    ![image](https://user-images.githubusercontent.com/28003269/194234662-2a55bb27-fa58-4935-a433-f2beed1591cd.png)
    """
    _docstring = None  # A cache for docstring property
    sv_category = ''  #: Add node to a category by its name to display with Shift+S

    @final
    def draw_buttons(self, context, layout):
        """This method is used to display extra UI element of a node which are
        generated automatically. To display elements specific to certain nodes
        use `SverchCustomTreeNode.sv_draw_buttons`."""
        if self.id_data.bl_idname == SverchCustomTree.bl_idname:
            row = layout.row(align=True)
            if self.is_animation_dependent:
                row.prop(self, 'is_animatable', icon='ANIM', icon_only=True)
            if self.is_scene_dependent:
                row.prop(self, 'is_interactive', icon='SCENE_DATA', icon_only=True)
            if self.is_animation_dependent or self.is_scene_dependent:
                row.prop(self, 'refresh', icon='FILE_REFRESH')
        self.sv_draw_buttons(context, layout)

    def sv_draw_buttons(self, context, layout):
        """Override to display node properties, text, operators etc. Read more in
        [Blender docs](https://docs.blender.org/api/3.3/bpy.types.UILayout.html)."""
        pass

    def draw_buttons_ext(self, context, layout):
        """This method is used to display extra UI element of a node which are
        generated automatically. To display elements specific to certain nodes
        use `SverchCustomTreeNode.sv_draw_buttons_ext`. This UI is displayed
        on a property panel of the tree editor."""
        if self.id_data.bl_idname == SverchCustomTree.bl_idname:
            row = layout.row(align=True)
            if self.is_animation_dependent:
                row.prop(self, 'is_animatable', icon='ANIM')
            if self.is_scene_dependent:
                row.prop(self, 'is_interactive', icon='SCENE_DATA')
            if self.is_animation_dependent or self.is_scene_dependent:
                row.prop(self, 'refresh', icon='FILE_REFRESH')
        self.sv_draw_buttons_ext(context, layout)

    def sv_draw_buttons_ext(self, context, layout):
        """Override to display node properties, text, operators etc. Read more in
        [Blender docs](https://docs.blender.org/api/3.3/bpy.types.UILayout.html).
        This UI is displayed on a property panel of the tree editor."""
        self.sv_draw_buttons(context, layout)

    @property
    def sv_internal_links(self) -> Iterable[tuple[NodeSocket, NodeSocket]]:
        """Override the property to change logic of connecting sockets
        when the node is muted.
        Also, there are some basic implementations `sverchok.utils.nodes_mixins.sockets_config`"""
        for link in self.internal_links:
            yield link.from_socket, link.to_socket

    @classproperty
    def docstring(cls):
        """
        Get SvDocstring instance parsed from node's docstring.
        """
        if cls._docstring is None:
            cls._docstring = SvDocstring(cls.__doc__)
        return cls._docstring

    @classmethod
    def poll(cls, ntree):
        """Can be overridden to make impossible to add certain nodes either to
        main trees or to group trees. Also since Blender 3.4 presence of this
        method is preventing Sverchok nodes from appearing in build-in tree
        editors. See [details](https://developer.blender.org/T101259#1423746)."""
        return ntree.bl_idname in ['SverchCustomTreeType', 'SvGroupTree']

    @property
    def absolute_location(self) -> tuple[float, float]:
        """
        When a node is inside a frame (and parented to it) then node.location is relative to its parent's location.
        This function returns the location in absolute screen terms whether the node is framed or not.
        """
        return recursive_framed_location_finder(self, self.location[:])

    @property
    def sv_default_color(self):
        """Returns default color of the node which can be changed in add-on settings."""
        return color_def.get_color(self.bl_idname)

    def set_temp_color(self, color=None):
        """This method memorize its initial color and override it with given one
        if given color is None it tries to return its initial color or do nothing"""

        if color is None:
            # looks like the node should return its initial color (user choice)
            if 'user_color' in self:
                self.use_custom_color = self['use_user_color']
                del self['use_user_color']
                self.color = self['user_color']
                del self['user_color']

        # set temporary color
        else:
            # save overridden color (only once)
            if 'user_color' not in self:
                self['use_user_color'] = self.use_custom_color
                self['user_color'] = self.color
            self.use_custom_color = True
            self.color = color

    def rclick_menu(self, context, layout):
        """
        Override this method to add specific items into the node's right-click menu.
        Default implementation calls `SverchCustomTreeNode.node_replacement_menu'.
        """
        self.node_replacement_menu(context, layout)

    def node_replacement_menu(self, context, layout):
        """
        Draw menu items with node replacement operators.
        This is called from `SverchCustomTreeNode.rclick_menu` method by default.
        Items are defined by `replacement_nodes` class property.
        Expected format is:

            replacement_nodes = [
                (new_node_bl_idname, inputs_mapping_dict, outputs_mapping_dict)
            ]

        where:

          - `new_node_bl_idname` is bl_idname of replacement node class,
          - `inputs_mapping_dict` is a dictionary mapping names of inputs of
            this node to names of inputs to new node,
          - `outputs_mapping_dict` is a dictionary mapping names of outputs
            of this node to names of outputs of new node.

        `inputs_mapping_dict` and `outputs_mapping_dict` can be None.
        """
        if hasattr(self, "replacement_nodes"):
            for bl_idname, inputs_mapping, outputs_mapping in self.replacement_nodes:
                node_class = get_node_class_reference(bl_idname)
                if node_class:
                    text = "Replace with {}".format(node_class.bl_label)
                    op = layout.operator("node.sv_replace_node", text=text)
                    op.old_node_name = self.name
                    op.new_bl_idname = bl_idname
                    set_inputs_mapping(op, inputs_mapping)
                    set_outputs_mapping(op, outputs_mapping)
                else:
                    self.error("Can't build replacement menu: no such node class: %s",bl_idname)

    def migrate_links_from(self, old_node, operator):
        """
        This method is called by `sverchok.ui.nodes_replacement.SvReplaceNode`.
        By default, it removes existing links from old_node
        and creates corresponding links for this (new) node.
        Override it to implement custom re-linking at node
        replacement.
        Most nodes do not have to override this method.
        """
        tree = self.id_data
        # Copy incoming / outgoing links
        old_in_links = [link for link in tree.links if link.to_node == old_node]
        old_out_links = [link for link in tree.links if link.from_node == old_node]

        for old_link in old_in_links:
            new_target_socket_name = operator.get_new_input_name(old_link.to_socket.name)
            if new_target_socket_name in self.inputs:
                new_target_socket = self.inputs[new_target_socket_name]
                new_link = tree.links.new(old_link.from_socket, new_target_socket)
            else:
                self.debug("New node %s has no input named %s, skipping", self.name, new_target_socket_name)
            tree.links.remove(old_link)

        for old_link in old_out_links:
            new_source_socket_name = operator.get_new_output_name(old_link.from_socket.name)
            # We have to remove old link before creating new one
            # Blender would not allow two links pointing to the same target socket
            old_target_socket = old_link.to_socket
            tree.links.remove(old_link)
            if new_source_socket_name in self.outputs:
                new_source_socket = self.outputs[new_source_socket_name]
                new_link = tree.links.new(new_source_socket, old_target_socket)
            else:
                self.debug("New node %s has no output named %s, skipping", self.name, new_source_socket_name)

    def migrate_from(self, old_node):
        """
        This method is called by `sverchok.ui.nodes_replacement.SvReplaceNode`.
        Override it to correctly copy settings from old_node
        to this (new) node.
        This is called after `SverchCustomTreeNode.migrate_links_from`.
        Default implementation does nothing.
        """
        pass

    @property
    def prefs_over_sized_buttons(self) -> bool:
        """Returns information whether buttons should be shown in big variant

        ![image](https://user-images.githubusercontent.com/28003269/193561093-0084dcef-90da-4e4c-a9c5-71c1dc6efca3.png)
        """
        try:
            addon = bpy.context.preferences.addons.get(sverchok.__name__)
            prefs = addon.preferences
        except Exception as err:
            print('failed to access addon preferences for button size', err)
            return False
        return prefs.over_sized_buttons


@post_load_call
def add_use_fake_user_to_trees():
    """When ever space node editor switches to another tree or creates new one,
    this function will set True to `use_fake_user` of all Sverchok trees"""
    def set_fake_user():
        [setattr(t, 'use_fake_user', True) for t in bpy.data.node_groups if t.bl_idname == 'SverchCustomTreeType']
    bpy.msgbus.subscribe_rna(key=(bpy.types.SpaceNodeEditor, 'node_tree'), owner=object(), args=(),
                             notify=set_fake_user)


register, unregister = bpy.utils.register_classes_factory([SverchCustomTree])
