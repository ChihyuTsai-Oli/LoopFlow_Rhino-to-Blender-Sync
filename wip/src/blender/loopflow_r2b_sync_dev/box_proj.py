# -*- coding: utf-8 -*-
"""Shader Editor：插入 Box 投影 Node Group（不寫 UV、不碰 Sync）。"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from foundation.box_mapping import (
    DEFAULT_SIZE_M,
    GROUP_NAME,
    LOCATION_SOCKET,
    MIN_SIZE_M,
    ROTATION_SOCKET,
    SIZE_SOCKET,
    VECTOR_SOCKET,
)


def _shader_tree(context):
    space = getattr(context, "space_data", None)
    if space is None or space.type != "NODE_EDITOR":
        return None
    if getattr(space, "tree_type", None) != "ShaderNodeTree":
        return None
    return getattr(space, "edit_tree", None)


def _selected_image_nodes(tree):
    return [n for n in tree.nodes if n.select and n.type == "TEX_IMAGE"]


def _set_interface_float(item, default, min_value):
    if hasattr(item, "default_value"):
        item.default_value = default
    if hasattr(item, "min_value"):
        item.min_value = min_value


def _set_interface_subtype(item, subtype):
    if hasattr(item, "subtype"):
        item.subtype = subtype


def ensure_box_projection_group():
    """取得或建立著色器 Node Group：Object 座標 → Mapping → Vector。"""
    existing = bpy.data.node_groups.get(GROUP_NAME)
    if existing is not None:
        return existing

    ng = bpy.data.node_groups.new(GROUP_NAME, "ShaderNodeTree")
    ng.use_fake_user = True
    iface = ng.interface
    size_in = iface.new_socket(
        name=SIZE_SOCKET, in_out="INPUT", socket_type="NodeSocketFloat"
    )
    _set_interface_float(size_in, DEFAULT_SIZE_M, MIN_SIZE_M)
    iface.new_socket(
        name=LOCATION_SOCKET, in_out="INPUT", socket_type="NodeSocketVector"
    )
    rot_in = iface.new_socket(
        name=ROTATION_SOCKET, in_out="INPUT", socket_type="NodeSocketVector"
    )
    _set_interface_subtype(rot_in, "EULER")
    iface.new_socket(
        name=VECTOR_SOCKET, in_out="OUTPUT", socket_type="NodeSocketVector"
    )

    nodes = ng.nodes
    links = ng.links
    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-720, 0)
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (280, 0)
    tex = nodes.new("ShaderNodeTexCoord")
    tex.location = (-480, 160)
    div = nodes.new("ShaderNodeMath")
    div.operation = "DIVIDE"
    div.location = (-480, -40)
    div.inputs[0].default_value = 1.0
    combine = nodes.new("ShaderNodeCombineXYZ")
    combine.location = (-280, -40)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.vector_type = "POINT"
    mapping.location = (0, 40)

    links.new(group_in.outputs[SIZE_SOCKET], div.inputs[1])
    links.new(div.outputs[0], combine.inputs[0])
    links.new(div.outputs[0], combine.inputs[1])
    links.new(div.outputs[0], combine.inputs[2])
    links.new(tex.outputs["Object"], mapping.inputs["Vector"])
    links.new(combine.outputs[0], mapping.inputs["Scale"])
    links.new(group_in.outputs[LOCATION_SOCKET], mapping.inputs["Location"])
    links.new(group_in.outputs[ROTATION_SOCKET], mapping.inputs["Rotation"])
    links.new(mapping.outputs["Vector"], group_out.inputs[VECTOR_SOCKET])
    return ng


def add_box_projection_to_tree(tree, selected_images):
    """在節點樹插入 Group；選中的 Image Texture 設成 Box 並接 Vector。"""
    group = ensure_box_projection_group()
    node = tree.nodes.new("ShaderNodeGroup")
    node.node_tree = group
    node.name = GROUP_NAME
    node.label = GROUP_NAME
    if selected_images:
        anchor = selected_images[0]
        node.location = (anchor.location.x - 280, anchor.location.y)
    wired = 0
    for image in selected_images:
        image.projection = "BOX"
        vec_in = image.inputs.get("Vector")
        if vec_in is None:
            continue
        while vec_in.is_linked:
            tree.links.remove(vec_in.links[0])
        tree.links.new(node.outputs[VECTOR_SOCKET], vec_in)
        wired += 1
    for n in tree.nodes:
        n.select = False
    node.select = True
    tree.nodes.active = node
    return node, wired


class LOOPFLOW_R2B_DEV_OT_add_box_projection(bpy.types.Operator):
    """Insert the Box Projection group. Selected Image Texture nodes are set to Box and wired."""

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
        images = _selected_image_nodes(tree)
        _node, wired = add_box_projection_to_tree(tree, images)
        if wired:
            self.report(
                {"INFO"},
                "Box Projection added; {} image(s) set to Box. Blend stays on the image node.".format(
                    wired
                ),
            )
        else:
            self.report(
                {"INFO"},
                "Box Projection added. Connect an Image Texture Vector input and set Projection to Box.",
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
        col = layout.column()
        col.label(text="Uses object coordinates (no UV).")
        col.label(text="Size is metres per tile (default 1).")
        col.label(text="Blend is on the Image Texture node.")


CLASSES = (
    LOOPFLOW_R2B_DEV_OT_add_box_projection,
    LOOPFLOW_R2B_DEV_PT_box_projection,
)
