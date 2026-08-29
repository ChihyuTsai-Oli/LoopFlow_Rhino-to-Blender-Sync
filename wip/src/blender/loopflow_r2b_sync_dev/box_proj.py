# -*- coding: utf-8 -*-
"""Shader Editor：世界座標 triplanar Box 投影（內建節點、GPU 可跑、不寫 UV）。"""
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
    GROUP_FLAG,
    GROUP_NAME,
    GROUP_VERSION,
    IMAGE_NODE_NAMES,
    LOCATION_SOCKET,
    MIN_SIZE_M,
    NODE_LABEL,
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


def _math_mul(nodes, links, loc, factor=-1.0):
    node = _new(nodes, "ShaderNodeMath", loc)
    node.operation = "MULTIPLY"
    node.inputs[1].default_value = factor
    return node


def _axis_rotate(nodes, loc, axis):
    """AXIS_ANGLE 旋轉；invert 關閉。角度由外部接入（已是弧度、已取負）。"""
    node = _new(nodes, "ShaderNodeVectorRotate", loc)
    node.rotation_type = "AXIS_ANGLE"
    node.invert = False
    _sock(node, "Axis").default_value = axis
    return node


def _inv_euler_on(nodes, links, vector_out, neg_x, neg_y, neg_z, origin):
    """R⁻¹：先 Rz(-z) 再 Ry(-y) 再 Rx(-x)。"""
    x, y = origin
    rz = _axis_rotate(nodes, (x, y), (0.0, 0.0, 1.0))
    ry = _axis_rotate(nodes, (x + 180, y), (0.0, 1.0, 0.0))
    rx = _axis_rotate(nodes, (x + 360, y), (1.0, 0.0, 0.0))
    links.new(vector_out, _sock(rz, "Vector"))
    links.new(_out(neg_z, "Value"), _sock(rz, "Angle"))
    links.new(_out(rz, "Vector"), _sock(ry, "Vector"))
    links.new(_out(neg_y, "Value"), _sock(ry, "Angle"))
    links.new(_out(ry, "Vector"), _sock(rx, "Vector"))
    links.new(_out(neg_x, "Value"), _sock(rx, "Angle"))
    return rx


def _fill_group(ng):
    """世界 P−T → 逐步反 Euler → 除 Scale → 三平面取樣混合。"""
    _wipe_group(ng)
    ng.use_fake_user = True
    ng[VERSION_KEY] = GROUP_VERSION
    iface = ng.interface
    scale_in = iface.new_socket(
        name=SCALE_SOCKET, in_out="INPUT", socket_type="NodeSocketVector"
    )
    _set_interface_vector(scale_in, DEFAULT_SCALE_XYZ, MIN_SIZE_M)
    loc_in = iface.new_socket(
        name=LOCATION_SOCKET, in_out="INPUT", socket_type="NodeSocketVector"
    )
    _set_interface_subtype(loc_in, "TRANSLATION")
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
    gi = _new(nodes, "NodeGroupInput", (-2200, 40))
    go = _new(nodes, "NodeGroupOutput", (1040, 40))
    geo = _new(nodes, "ShaderNodeNewGeometry", (-2200, 280))

    sub = _new(nodes, "ShaderNodeVectorMath", (-1980, 220))
    sub.operation = "SUBTRACT"
    L(_out(geo, "Position"), _sock(sub, "Vector"))
    L(gi.outputs[LOCATION_SOCKET], sub.inputs[1])

    sep_r = _new(nodes, "ShaderNodeSeparateXYZ", (-1980, -80))
    L(gi.outputs[ROTATION_SOCKET], _sock(sep_r, "Vector"))
    neg_x = _math_mul(nodes, links, (-1760, 0))
    neg_y = _math_mul(nodes, links, (-1760, -80))
    neg_z = _math_mul(nodes, links, (-1760, -160))
    L(sep_r.outputs["X"], neg_x.inputs[0])
    L(sep_r.outputs["Y"], neg_y.inputs[0])
    L(sep_r.outputs["Z"], neg_z.inputs[0])

    rot_p = _inv_euler_on(
        nodes, links, _out(sub, "Vector"), neg_x, neg_y, neg_z, (-1540, 220)
    )
    try:
        n_src = _out(geo, "True Normal")
    except KeyError:
        n_src = _out(geo, "Normal")
    rot_n = _inv_euler_on(nodes, links, n_src, neg_x, neg_y, neg_z, (-1540, -80))

    div = _new(nodes, "ShaderNodeVectorMath", (-980, 220))
    div.operation = "DIVIDE"
    L(_out(rot_p, "Vector"), _sock(div, "Vector"))
    L(gi.outputs[SCALE_SOCKET], div.inputs[1])

    sep_p = _new(nodes, "ShaderNodeSeparateXYZ", (-760, 260))
    L(_out(div, "Vector"), _sock(sep_p, "Vector"))
    uv_x = _new(nodes, "ShaderNodeCombineXYZ", (-540, 360))
    uv_y = _new(nodes, "ShaderNodeCombineXYZ", (-540, 220))
    uv_z = _new(nodes, "ShaderNodeCombineXYZ", (-540, 80))
    img_x = _new(nodes, "ShaderNodeTexImage", (-280, 400), IMAGE_NODE_NAMES[0])
    img_y = _new(nodes, "ShaderNodeTexImage", (-280, 200), IMAGE_NODE_NAMES[1])
    img_z = _new(nodes, "ShaderNodeTexImage", (-280, 0), IMAGE_NODE_NAMES[2])
    for img in (img_x, img_y, img_z):
        img.projection = "FLAT"
        img.extension = "REPEAT"

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

    abs_n = _new(nodes, "ShaderNodeVectorMath", (-980, -80))
    abs_n.operation = "ABSOLUTE"
    L(_out(rot_n, "Vector"), _sock(abs_n, "Vector"))
    sep_n = _new(nodes, "ShaderNodeSeparateXYZ", (-760, -80))
    L(_out(abs_n, "Vector"), _sock(sep_n, "Vector"))
    one = _new(nodes, "ShaderNodeMath", (-760, -280))
    one.operation = "SUBTRACT"
    one.inputs[0].default_value = 1.0
    sharp_mul = _new(nodes, "ShaderNodeMath", (-560, -280))
    sharp_mul.operation = "MULTIPLY"
    sharp_mul.inputs[1].default_value = 31.0
    sharp_add = _new(nodes, "ShaderNodeMath", (-360, -280))
    sharp_add.operation = "ADD"
    sharp_add.inputs[1].default_value = 1.0
    L(gi.outputs[BLEND_SOCKET], one.inputs[1])
    L(_out(one, "Value"), _sock(sharp_mul, "Value"))
    L(_out(sharp_mul, "Value"), _sock(sharp_add, "Value"))
    pow_x = _new(nodes, "ShaderNodeMath", (-540, -40))
    pow_y = _new(nodes, "ShaderNodeMath", (-540, -120))
    pow_z = _new(nodes, "ShaderNodeMath", (-540, -200))
    for pw in (pow_x, pow_y, pow_z):
        pw.operation = "POWER"
    L(sep_n.outputs["X"], pow_x.inputs[0])
    L(sep_n.outputs["Y"], pow_y.inputs[0])
    L(sep_n.outputs["Z"], pow_z.inputs[0])
    L(_out(sharp_add, "Value"), pow_x.inputs[1])
    L(_out(sharp_add, "Value"), pow_y.inputs[1])
    L(_out(sharp_add, "Value"), pow_z.inputs[1])
    sum_xy = _new(nodes, "ShaderNodeMath", (-280, -80))
    sum_xy.operation = "ADD"
    sum_xyz = _new(nodes, "ShaderNodeMath", (-80, -80))
    sum_xyz.operation = "ADD"
    clamp_sum = _new(nodes, "ShaderNodeMath", (120, -80))
    clamp_sum.operation = "MAXIMUM"
    clamp_sum.inputs[1].default_value = 0.0001
    L(_out(pow_x, "Value"), sum_xy.inputs[0])
    L(_out(pow_y, "Value"), sum_xy.inputs[1])
    L(_out(sum_xy, "Value"), sum_xyz.inputs[0])
    L(_out(pow_z, "Value"), sum_xyz.inputs[1])
    L(_out(sum_xyz, "Value"), clamp_sum.inputs[0])
    wx = _new(nodes, "ShaderNodeMath", (320, 80))
    wy = _new(nodes, "ShaderNodeMath", (320, -20))
    wz = _new(nodes, "ShaderNodeMath", (320, -120))
    for w in (wx, wy, wz):
        w.operation = "DIVIDE"
    L(_out(pow_x, "Value"), wx.inputs[0])
    L(_out(pow_y, "Value"), wy.inputs[0])
    L(_out(pow_z, "Value"), wz.inputs[0])
    L(_out(clamp_sum, "Value"), wx.inputs[1])
    L(_out(clamp_sum, "Value"), wy.inputs[1])
    L(_out(clamp_sum, "Value"), wz.inputs[1])

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


def ensure_box_projection_template():
    """樣板 Group；version 不符則重填。實際插入時再 copy，避免換圖改到所有材質。"""
    existing = bpy.data.node_groups.get(GROUP_NAME)
    if existing is not None:
        if existing.get(VERSION_KEY) == GROUP_VERSION:
            return existing
        _fill_group(existing)
        return existing
    ng = bpy.data.node_groups.new(GROUP_NAME, "ShaderNodeTree")
    _fill_group(ng)
    return ng


def _new_group_copy():
    proto = ensure_box_projection_template()
    ng = proto.copy()
    ng[VERSION_KEY] = GROUP_VERSION
    return ng


def _image_nodes(group):
    found = []
    for name in IMAGE_NODE_NAMES:
        node = group.nodes.get(name)
        if node is not None:
            found.append(node)
    return found


def _set_group_image(group, image, interpolation="Linear", extension="REPEAT"):
    for node in _image_nodes(group):
        node.image = image
        node.interpolation = interpolation
        node.extension = extension
        node.projection = "FLAT"


def _assign_image_from_tex(group, image_node):
    image = getattr(image_node, "image", None)
    interpolation = getattr(image_node, "interpolation", "Linear")
    _set_group_image(group, image, interpolation, "REPEAT")


def _replace_color_links(tree, from_node, group_node):
    color_out = from_node.outputs.get("Color")
    group_color = group_node.outputs.get(COLOR_SOCKET)
    if color_out is None or group_color is None:
        return 0
    targets = [lnk.to_socket for lnk in list(color_out.links)]
    for lnk in list(color_out.links):
        tree.links.remove(lnk)
    for to_socket in targets:
        tree.links.new(group_color, to_socket)
    return len(targets)


def _is_box_group_node(node):
    if node is None or node.bl_idname != "ShaderNodeGroup":
        return False
    if node.get(GROUP_FLAG) == 1:
        return True
    tree = getattr(node, "node_tree", None)
    return tree is not None and tree.get(VERSION_KEY) is not None


def _box_group_node(tree):
    if tree is None:
        return None
    active = tree.nodes.active
    if _is_box_group_node(active):
        return active
    for node in tree.nodes:
        if _is_box_group_node(node):
            return node
    return None


def add_box_projection_to_tree(context, tree, selected_images):
    """插入獨立 Group 複本。選中 Image Texture 時共用同一張圖並改接 Color。"""
    group = _new_group_copy()
    node = tree.nodes.new("ShaderNodeGroup")
    node.node_tree = group
    node.name = GROUP_NAME
    node.label = NODE_LABEL
    node[GROUP_FLAG] = 1
    image = None
    if selected_images:
        anchor = selected_images[0]
        node.location = (anchor.location.x - 280, anchor.location.y)
        _assign_image_from_tex(group, anchor)
        image = getattr(anchor, "image", None)
        if image is not None:
            context.scene.r2b_box_image = image
    else:
        node.location = (0, 0)
    wired = 0
    for tex in selected_images:
        wired += _replace_color_links(tree, tex, node)
    for n in tree.nodes:
        n.select = False
    node.select = True
    tree.nodes.active = node
    return node, wired, image


def _on_box_image_update(self, context):
    """只改組內三張 Image Texture 的同一 datablock，不碰 OSL、不重編譯。"""
    node = _box_group_node(_shader_tree(context))
    if node is None or node.node_tree is None:
        return
    _set_group_image(node.node_tree, self.r2b_box_image)


def _draw_xyz(layout, sock, text):
    col = layout.column(align=True)
    col.label(text=text)
    row = col.row(align=True)
    row.prop(sock, "default_value", index=0, text="X")
    row.prop(sock, "default_value", index=1, text="Y")
    row.prop(sock, "default_value", index=2, text="Z")


class LOOPFLOW_R2B_DEV_OT_add_box_projection(bpy.types.Operator):
    """Insert world-space triplanar Box Projection (native nodes, GPU). Selected Image Texture is shared inside the group."""

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
        _node, wired, image = add_box_projection_to_tree(context, tree, images)
        if wired:
            self.report(
                {"INFO"},
                "Box Projection added (GPU). Color rewired. Rotation is degrees.",
            )
        elif image is not None:
            self.report(
                {"INFO"},
                "Box Projection added with the selected image. Connect Color to the shader.",
            )
        else:
            self.report(
                {"INFO"},
                "Box Projection added. Pick an image in the N-panel, then connect Color.",
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

        node = _box_group_node(_shader_tree(context))
        if node is None:
            layout.label(text="Add first, then edit Scale / Location / Rotation here.")
            return

        scale = node.inputs.get(SCALE_SOCKET)
        location = node.inputs.get(LOCATION_SOCKET)
        rotation = node.inputs.get(ROTATION_SOCKET)
        blend = node.inputs.get(BLEND_SOCKET)
        if scale is None or location is None or rotation is None or blend is None:
            layout.label(text="Group sockets missing. Add again.")
            return

        layout.separator()
        _draw_xyz(layout, scale, "Scale (m per tile)")
        _draw_xyz(layout, location, "Location (world)")
        layout.prop(rotation, "default_value", text="Rotation")
        layout.prop(blend, "default_value", text="Blend", slider=True)


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
