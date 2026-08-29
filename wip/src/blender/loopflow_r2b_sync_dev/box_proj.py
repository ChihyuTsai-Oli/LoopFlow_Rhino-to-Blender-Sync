# -*- coding: utf-8 -*-
"""Shader Editor：世界座標 triplanar Box 投影（不寫 UV、不碰 Sync）。"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from foundation.box_mapping import (
    BLEND_SOCKET,
    COLOR_SOCKET,
    DEFAULT_SCALE_XYZ,
    GROUP_NAME,
    GROUP_VERSION,
    IMAGE_NODE_NAMES,
    LOCATION_SOCKET,
    MIN_SIZE_M,
    ROTATION_SOCKET,
    SCALE_SOCKET,
    VERSION_KEY,
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


def _set_interface_float(item, default, min_value, max_value=None):
    if hasattr(item, "default_value"):
        item.default_value = default
    if hasattr(item, "min_value"):
        item.min_value = min_value
    if max_value is not None and hasattr(item, "max_value"):
        item.max_value = max_value


def _set_interface_vector(item, default, min_value=None):
    if hasattr(item, "default_value"):
        item.default_value = default
    if min_value is not None and hasattr(item, "min_value"):
        item.min_value = min_value


def _set_interface_subtype(item, subtype):
    if hasattr(item, "subtype"):
        item.subtype = subtype


def _sock(node, *names):
    for name in names:
        if name in node.inputs:
            return node.inputs[name]
    for inp in node.inputs:
        if inp.name in names:
            return inp
    raise KeyError("{0}: {1}".format(node.bl_idname, names))


def _out(node, *names):
    for name in names:
        if name in node.outputs:
            return node.outputs[name]
    for out in node.outputs:
        if out.name in names:
            return out
    raise KeyError("{0}: {1}".format(node.bl_idname, names))


def _wipe_group(ng):
    ng.links.clear()
    for node in list(ng.nodes):
        ng.nodes.remove(node)
    iface = ng.interface
    for item in reversed(list(iface.items_tree)):
        try:
            iface.remove(item)
        except Exception:
            pass


def _new(nodes, bl_idname, location, name=None):
    node = nodes.new(bl_idname)
    node.location = location
    if name:
        node.name = name
        node.label = name
    return node


def _fill_group(ng):
    """世界 P−T → 逆旋轉 P 與 N → 除 Scale → 三平面取樣混合。"""
    _wipe_group(ng)
    ng.use_fake_user = True
    ng[VERSION_KEY] = GROUP_VERSION
    iface = ng.interface
    scale_in = iface.new_socket(
        name=SCALE_SOCKET, in_out="INPUT", socket_type="NodeSocketVector"
    )
    _set_interface_vector(scale_in, DEFAULT_SCALE_XYZ, MIN_SIZE_M)
    iface.new_socket(
        name=LOCATION_SOCKET, in_out="INPUT", socket_type="NodeSocketVector"
    )
    rot_in = iface.new_socket(
        name=ROTATION_SOCKET, in_out="INPUT", socket_type="NodeSocketVector"
    )
    _set_interface_subtype(rot_in, "EULER")
    blend_in = iface.new_socket(
        name=BLEND_SOCKET, in_out="INPUT", socket_type="NodeSocketFloat"
    )
    _set_interface_float(blend_in, 0.0, 0.0, 1.0)
    iface.new_socket(
        name=COLOR_SOCKET, in_out="OUTPUT", socket_type="NodeSocketColor"
    )

    nodes = ng.nodes
    links = ng.links
    L = links.new
    gi = _new(nodes, "NodeGroupInput", (-1680, 40))
    go = _new(nodes, "NodeGroupOutput", (1040, 40))
    geo = _new(nodes, "ShaderNodeNewGeometry", (-1680, 280))

    sub = _new(nodes, "ShaderNodeVectorMath", (-1440, 220))
    sub.operation = "SUBTRACT"
    rot_p = _new(nodes, "ShaderNodeVectorRotate", (-1220, 220))
    rot_p.rotation_type = "EULER_XYZ"
    rot_p.invert = True
    rot_n = _new(nodes, "ShaderNodeVectorRotate", (-1220, -40))
    rot_n.rotation_type = "EULER_XYZ"
    rot_n.invert = True
    div = _new(nodes, "ShaderNodeVectorMath", (-980, 220))
    div.operation = "DIVIDE"

    sep_p = _new(nodes, "ShaderNodeSeparateXYZ", (-760, 260))
    uv_x = _new(nodes, "ShaderNodeCombineXYZ", (-540, 360))
    uv_y = _new(nodes, "ShaderNodeCombineXYZ", (-540, 220))
    uv_z = _new(nodes, "ShaderNodeCombineXYZ", (-540, 80))
    img_x = _new(nodes, "ShaderNodeTexImage", (-280, 400), IMAGE_NODE_NAMES[0])
    img_y = _new(nodes, "ShaderNodeTexImage", (-280, 200), IMAGE_NODE_NAMES[1])
    img_z = _new(nodes, "ShaderNodeTexImage", (-280, 0), IMAGE_NODE_NAMES[2])
    for img in (img_x, img_y, img_z):
        img.projection = "FLAT"

    abs_n = _new(nodes, "ShaderNodeVectorMath", (-980, -80))
    abs_n.operation = "ABSOLUTE"
    sep_n = _new(nodes, "ShaderNodeSeparateXYZ", (-760, -80))
    one = _new(nodes, "ShaderNodeMath", (-760, -280))
    one.operation = "SUBTRACT"
    one.inputs[0].default_value = 1.0
    sharp_mul = _new(nodes, "ShaderNodeMath", (-560, -280))
    sharp_mul.operation = "MULTIPLY"
    sharp_mul.inputs[1].default_value = 31.0
    sharp_add = _new(nodes, "ShaderNodeMath", (-360, -280))
    sharp_add.operation = "ADD"
    sharp_add.inputs[1].default_value = 1.0
    pow_x = _new(nodes, "ShaderNodeMath", (-540, -40))
    pow_y = _new(nodes, "ShaderNodeMath", (-540, -120))
    pow_z = _new(nodes, "ShaderNodeMath", (-540, -200))
    for pw in (pow_x, pow_y, pow_z):
        pw.operation = "POWER"
    sum_xy = _new(nodes, "ShaderNodeMath", (-280, -80))
    sum_xy.operation = "ADD"
    sum_xyz = _new(nodes, "ShaderNodeMath", (-80, -80))
    sum_xyz.operation = "ADD"
    clamp_sum = _new(nodes, "ShaderNodeMath", (120, -80))
    clamp_sum.operation = "MAXIMUM"
    clamp_sum.inputs[1].default_value = 0.0001
    wx = _new(nodes, "ShaderNodeMath", (320, 80))
    wy = _new(nodes, "ShaderNodeMath", (320, -20))
    wz = _new(nodes, "ShaderNodeMath", (320, -120))
    for w in (wx, wy, wz):
        w.operation = "DIVIDE"

    mx = _new(nodes, "ShaderNodeMix", (560, 280))
    my = _new(nodes, "ShaderNodeMix", (560, 80))
    mz = _new(nodes, "ShaderNodeMix", (560, -120))
    add_xy = _new(nodes, "ShaderNodeMix", (800, 180))
    add_xyz = _new(nodes, "ShaderNodeMix", (800, 0))
    for mix in (mx, my, mz):
        mix.data_type = "RGBA"
        mix.blend_type = "MIX"
        try:
            _sock(mix, "A", "Color1").default_value = (0.0, 0.0, 0.0, 1.0)
        except Exception:
            pass
    for mix in (add_xy, add_xyz):
        mix.data_type = "RGBA"
        mix.blend_type = "ADD"
        _sock(mix, "Factor", "Fac").default_value = 1.0

    L(_out(geo, "Position"), _sock(sub, "Vector"))
    L(gi.outputs[LOCATION_SOCKET], sub.inputs[1])
    L(_out(sub, "Vector"), _sock(rot_p, "Vector"))
    L(gi.outputs[ROTATION_SOCKET], _sock(rot_p, "Rotation"))
    L(_out(geo, "Normal"), _sock(rot_n, "Vector"))
    L(gi.outputs[ROTATION_SOCKET], _sock(rot_n, "Rotation"))
    L(_out(rot_p, "Vector"), _sock(div, "Vector"))
    L(gi.outputs[SCALE_SOCKET], div.inputs[1])
    L(_out(div, "Vector"), _sock(sep_p, "Vector"))

    # X 面用 YZ；Y 面用 XZ；Z 面用 XY
    L(sep_p.outputs["Y"], uv_x.inputs["X"])
    L(sep_p.outputs["Z"], uv_x.inputs["Y"])
    L(sep_p.outputs["X"], uv_y.inputs["X"])
    L(sep_p.outputs["Z"], uv_y.inputs["Y"])
    L(sep_p.outputs["X"], uv_z.inputs["X"])
    L(sep_p.outputs["Y"], uv_z.inputs["Y"])
    L(_out(uv_x, "Vector"), _sock(img_x, "Vector"))
    L(_out(uv_y, "Vector"), _sock(img_y, "Vector"))
    L(_out(uv_z, "Vector"), _sock(img_z, "Vector"))

    L(_out(rot_n, "Vector"), _sock(abs_n, "Vector"))
    L(_out(abs_n, "Vector"), _sock(sep_n, "Vector"))
    L(gi.outputs[BLEND_SOCKET], one.inputs[1])
    L(_out(one, "Value"), _sock(sharp_mul, "Value"))
    L(_out(sharp_mul, "Value"), _sock(sharp_add, "Value"))
    L(sep_n.outputs["X"], pow_x.inputs[0])
    L(sep_n.outputs["Y"], pow_y.inputs[0])
    L(sep_n.outputs["Z"], pow_z.inputs[0])
    L(_out(sharp_add, "Value"), pow_x.inputs[1])
    L(_out(sharp_add, "Value"), pow_y.inputs[1])
    L(_out(sharp_add, "Value"), pow_z.inputs[1])
    L(_out(pow_x, "Value"), sum_xy.inputs[0])
    L(_out(pow_y, "Value"), sum_xy.inputs[1])
    L(_out(sum_xy, "Value"), sum_xyz.inputs[0])
    L(_out(pow_z, "Value"), sum_xyz.inputs[1])
    L(_out(sum_xyz, "Value"), clamp_sum.inputs[0])
    L(_out(pow_x, "Value"), wx.inputs[0])
    L(_out(pow_y, "Value"), wy.inputs[0])
    L(_out(pow_z, "Value"), wz.inputs[0])
    L(_out(clamp_sum, "Value"), wx.inputs[1])
    L(_out(clamp_sum, "Value"), wy.inputs[1])
    L(_out(clamp_sum, "Value"), wz.inputs[1])

    L(_out(wx, "Value"), _sock(mx, "Factor", "Fac"))
    L(_out(img_x, "Color"), _sock(mx, "B", "Color2"))
    L(_out(wy, "Value"), _sock(my, "Factor", "Fac"))
    L(_out(img_y, "Color"), _sock(my, "B", "Color2"))
    L(_out(wz, "Value"), _sock(mz, "Factor", "Fac"))
    L(_out(img_z, "Color"), _sock(mz, "B", "Color2"))
    L(_out(mx, "Result", "Color"), _sock(add_xy, "A", "Color1"))
    L(_out(my, "Result", "Color"), _sock(add_xy, "B", "Color2"))
    L(_out(add_xy, "Result", "Color"), _sock(add_xyz, "A", "Color1"))
    L(_out(mz, "Result", "Color"), _sock(add_xyz, "B", "Color2"))
    L(_out(add_xyz, "Result", "Color"), go.inputs[COLOR_SOCKET])


def ensure_box_projection_group():
    """取得或重建 triplanar Node Group（version 不符則重填內部）。"""
    existing = bpy.data.node_groups.get(GROUP_NAME)
    if existing is not None:
        if existing.get(VERSION_KEY) == GROUP_VERSION:
            return existing
        _fill_group(existing)
        return existing
    ng = bpy.data.node_groups.new(GROUP_NAME, "ShaderNodeTree")
    _fill_group(ng)
    return ng


def _assign_image_to_group(group, image_node):
    image = getattr(image_node, "image", None)
    interpolation = getattr(image_node, "interpolation", "Linear")
    extension = getattr(image_node, "extension", "REPEAT")
    for name in IMAGE_NODE_NAMES:
        node = group.nodes.get(name)
        if node is None:
            continue
        node.image = image
        node.interpolation = interpolation
        node.extension = extension
        node.projection = "FLAT"


def _replace_color_links(tree, from_node, group_node):
    color_out = from_node.outputs.get("Color")
    group_color = group_node.outputs.get(COLOR_SOCKET)
    if color_out is None or group_color is None:
        return 0
    targets = [(lnk.to_socket) for lnk in list(color_out.links)]
    for lnk in list(color_out.links):
        tree.links.remove(lnk)
    for to_socket in targets:
        tree.links.new(group_color, to_socket)
    return len(targets)


def add_box_projection_to_tree(tree, selected_images):
    """插入 Group（輸出 Color）。選中的 Image Texture 複製進組內並改接 Color。"""
    group = ensure_box_projection_group()
    node = tree.nodes.new("ShaderNodeGroup")
    node.node_tree = group
    node.name = GROUP_NAME
    node.label = GROUP_NAME
    if selected_images:
        anchor = selected_images[0]
        node.location = (anchor.location.x - 280, anchor.location.y)
        _assign_image_to_group(group, anchor)
    wired = 0
    for image in selected_images:
        wired += _replace_color_links(tree, image, node)
    for n in tree.nodes:
        n.select = False
    node.select = True
    tree.nodes.active = node
    return node, wired


class LOOPFLOW_R2B_DEV_OT_add_box_projection(bpy.types.Operator):
    """Insert world-space triplanar Box Projection. Selected Image Texture is copied into the group."""

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
                "Box Projection added; Color rewired from {} image(s). Scale is metres per axis.".format(
                    wired
                ),
            )
        elif images:
            self.report(
                {"INFO"},
                "Box Projection added with the selected image. Connect the group Color output.",
            )
        else:
            self.report(
                {"INFO"},
                "Box Projection added. Select an Image Texture and run again to copy the image.",
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
        col.label(text="World-space triplanar (no UV).")
        col.label(text="Scale XYZ = metres per tile.")
        col.label(text="Location moves in world XYZ.")
        col.label(text="Blend 0 = sharp seams.")


CLASSES = (
    LOOPFLOW_R2B_DEV_OT_add_box_projection,
    LOOPFLOW_R2B_DEV_PT_box_projection,
)
