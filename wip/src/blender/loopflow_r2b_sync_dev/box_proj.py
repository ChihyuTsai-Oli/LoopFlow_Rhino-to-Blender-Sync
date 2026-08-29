# -*- coding: utf-8 -*-
"""Shader Editor：Cycles OSL Box 投影（不寫 UV、不碰 Sync）。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from foundation.box_mapping import (
    COLOR_SOCKET,
    FILENAME_SOCKET,
    NODE_LABEL,
    OSL_FILE_NAME,
    OSL_NODE_FLAG,
    OSL_TEXT_NAME,
)

_OSL_PATH = Path(__file__).resolve().parent / OSL_FILE_NAME


def _shader_tree(context):
    space = getattr(context, "space_data", None)
    if space is None or space.type != "NODE_EDITOR":
        return None
    if getattr(space, "tree_type", None) != "ShaderNodeTree":
        return None
    return getattr(space, "edit_tree", None)


def _selected_image_nodes(tree):
    return [n for n in tree.nodes if n.select and n.type == "TEX_IMAGE"]


def _osl_source():
    return _OSL_PATH.read_text(encoding="utf-8")


def ensure_osl_text():
    """把 add-on 內 .osl 同步到 blend Text，Script 節點走 INTERNAL（不寫 .oso 進 Git）。"""
    src = _osl_source()
    text = bpy.data.texts.get(OSL_TEXT_NAME)
    if text is None:
        text = bpy.data.texts.new(OSL_TEXT_NAME)
    if text.as_string() != src:
        if hasattr(text, "from_string"):
            text.from_string(src)
        else:
            text.clear()
            text.write(src)
    return text


def ensure_cycles_osl(scene):
    cycles = getattr(scene, "cycles", None)
    if cycles is None:
        return "Cycles is not available on this scene"
    if hasattr(cycles, "shading_system"):
        cycles.shading_system = True
    return ""


def image_osl_path(image):
    if image is None:
        return ""
    raw = getattr(image, "filepath", "") or ""
    path = bpy.path.abspath(raw)
    if not path or not os.path.isfile(path):
        return ""
    return path.replace("\\", "/")


def _set_filename(node, image):
    sock = node.inputs.get(FILENAME_SOCKET)
    if sock is None:
        return ""
    path = image_osl_path(image)
    sock.default_value = path
    return path


def _replace_color_links(tree, from_node, to_node):
    color_out = from_node.outputs.get("Color")
    dest = to_node.outputs.get(COLOR_SOCKET)
    if color_out is None or dest is None:
        return 0
    targets = [lnk.to_socket for lnk in list(color_out.links)]
    for lnk in list(color_out.links):
        tree.links.remove(lnk)
    for to_socket in targets:
        tree.links.new(dest, to_socket)
    return len(targets)


def _update_script_node(context, node):
    tree = node.id_data
    tree.nodes.active = node
    node.select = True
    try:
        bpy.ops.node.shader_script_update()
    except Exception:
        pass


def add_box_projection_to_tree(context, tree, selected_images):
    """插入一顆 OSL Script 節點。"""
    err = ensure_cycles_osl(context.scene)
    text = ensure_osl_text()
    node = tree.nodes.new("ShaderNodeScript")
    node.mode = "INTERNAL"
    node.script = text
    node.label = NODE_LABEL
    node[OSL_NODE_FLAG] = 1
    if selected_images:
        anchor = selected_images[0]
        node.location = (anchor.location.x - 280, anchor.location.y)
    else:
        node.location = (0, 0)
    _update_script_node(context, node)
    wired = 0
    image = None
    if selected_images:
        image = getattr(selected_images[0], "image", None)
        _set_filename(node, image)
        if image is not None:
            context.scene.r2b_box_image = image
        for tex in selected_images:
            wired += _replace_color_links(tree, tex, node)
    for n in tree.nodes:
        n.select = False
    node.select = True
    tree.nodes.active = node
    return node, wired, err, image


def _on_box_image_update(self, context):
    tree = _shader_tree(context)
    if tree is None:
        return
    node = tree.nodes.active
    if node is None or node.get(OSL_NODE_FLAG) != 1:
        flagged = [n for n in tree.nodes if n.get(OSL_NODE_FLAG) == 1]
        node = flagged[0] if flagged else None
    if node is None:
        return
    path = _set_filename(node, self.r2b_box_image)
    if self.r2b_box_image and not path:
        return


class LOOPFLOW_R2B_DEV_OT_add_box_projection(bpy.types.Operator):
    """Insert a Cycles OSL Box Projection script. Selected Image Texture path is copied; Color is rewired."""

    bl_idname = "loopflow_r2b_dev.add_box_projection"
    bl_label = "Add Box Projection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _shader_tree(context) is not None

    def execute(self, context):
        tree = _shader_tree(context)
        if tree is None:
            self.report({"ERROR"}, "Open a Shader Editor with a material node tree")
            return {"CANCELLED"}
        if not _OSL_PATH.is_file():
            self.report({"ERROR"}, "OSL file missing: {}".format(_OSL_PATH))
            return {"CANCELLED"}
        images = _selected_image_nodes(tree)
        _node, wired, osl_err, image = add_box_projection_to_tree(
            context, tree, images
        )
        if osl_err:
            self.report({"WARNING"}, osl_err)
        if image is not None and not image_osl_path(image):
            self.report(
                {"WARNING"},
                "Image has no file on disk. Save/unpack it, then pick it in the N-panel.",
            )
        if wired:
            self.report(
                {"INFO"},
                "OSL Box Projection added (Cycles). Color rewired. Rotation is degrees.",
            )
        else:
            self.report(
                {"INFO"},
                "OSL Box Projection added (Cycles). Connect Color; pick an image in the N-panel.",
            )
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_PT_box_projection(bpy.types.Panel):
    bl_label = "Box Projection"
    bl_idname = "LOOPFLOW_R2B_DEV_PT_box_projection"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "LoopFlow"

    @classmethod
    def poll(cls, context):
        return _shader_tree(context) is not None

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "loopflow_r2b_dev.add_box_projection", text="Add Box Projection"
        )
        layout.template_ID(context.scene, "r2b_box_image", open="image.open")
        col = layout.column()
        col.label(text="Cycles + OSL only. One Script node.")
        col.label(text="Scale XYZ = metres per tile.")
        col.label(text="Location = world XYZ. Rotation = degrees.")
        col.label(text="Image must be a file on disk.")


def register_props():
    bpy.types.Scene.r2b_box_image = bpy.props.PointerProperty(
        name="Image",
        type=bpy.types.Image,
        update=_on_box_image_update,
    )


def unregister_props():
    if hasattr(bpy.types.Scene, "r2b_box_image"):
        del bpy.types.Scene.r2b_box_image


CLASSES = (
    LOOPFLOW_R2B_DEV_OT_add_box_projection,
    LOOPFLOW_R2B_DEV_PT_box_projection,
)
