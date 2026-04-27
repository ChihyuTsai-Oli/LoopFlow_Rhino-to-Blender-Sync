# MIT License
# Copyright (c) 2018-2024 Nathan Letwory, Joel Putnam, Tom Svilans, Lukas Fertig

import bpy
import uuid
import rhino3dm as r3d
from mathutils import Matrix
from typing import Any, Dict

def tag_data(idblock : bpy.types.ID, tag_dict: Dict[str, Any]) -> None:
    """
    將 Rhino 的原始數據寫入 Blender 物件的自定義屬性中
    """
    idblock['rhid'] = str(tag_dict.get('rhid', None))
    idblock['rhname'] = tag_dict.get('rhname', None)
    idblock['rhmatid'] = str(tag_dict.get('rhmatid', None))
    idblock['rhparentid'] = str(tag_dict.get('rhparentid', None))
    idblock['rhidef'] = tag_dict.get('rhidef', False)
    idblock['rhmat_from_object'] = tag_dict.get('rhmat_from_object', True)

def create_tag_dict(guid, name, matid=None, parentid=None, is_idef=False, mat_from_object=True):
    return {
        'rhid': guid, 'rhname': name, 'rhmatid': matid,
        'rhparentid': parentid, 'rhidef': is_idef, 'rhmat_from_object': mat_from_object
    }

all_dict = dict()

def clear_all_dict():
    """
    相容性修正：Addon 原始的清理函式名稱
    """
    global all_dict
    all_dict = dict()

def reset_all_dict(context):
    """
    執行清理並重新初始化快取字典
    """
    clear_all_dict()
    bases = [
        context.blend_data.objects, context.blend_data.cameras,
        context.blend_data.lights, context.blend_data.meshes,
        context.blend_data.materials, context.blend_data.collections,
        context.blend_data.curves
    ]
    for base in bases:
        # 取得類型名稱作為 key
        t = repr(base).split(',')[1]
        dct = all_dict.setdefault(t, dict())
        for item in base:
            rhid = item.get('rhid', None)
            if rhid:
                dct[rhid] = item

def get_dict_for_base(base):
    global all_dict
    # 從 repr 獲取集合類型字串，例如 'objects'
    t = repr(base).split(',')[1]
    return all_dict.setdefault(t, dict())

def get_or_create_iddata(base : bpy.types.bpy_prop_collection, tag_dict: Dict[str, Any], obdata : bpy.types.ID) -> bpy.types.ID:
    """
    取得或建立數據塊，並同步名稱
    """
    founditem : bpy.types.ID = None
    guid = tag_dict.get('rhid', None)
    name = tag_dict.get('rhname', None)
    dct = get_dict_for_base(base)

    if guid is not None:
        strguid = str(guid)
        if strguid in dct:
            founditem = dct[strguid]

    if founditem:
        theitem = founditem
        # 同步顯示名稱
        if name and theitem.name != name:
            theitem.name = name
        theitem['rhname'] = name
        
        if obdata and type(theitem) != type(obdata):
            theitem.data = obdata
    else:
        # 建立新數據
        if obdata:
            theitem = base.new(name=name, object_data=obdata)
        else:
            theitem = base.new(name=name)
        
        if guid is not None:
            dct[str(guid)] = theitem
        tag_data(theitem, tag_dict)
        
    return theitem

def matrix_from_xform(xform : r3d.Transform):
     return Matrix(
            ((xform.M00, xform.M01, xform.M02, xform.M03),
            (xform.M10, xform.M11, xform.M12, xform.M13),
            (xform.M20, xform.M21, xform.M22, xform.M23),
            (xform.M30, xform.M31, xform.M32, xform.M33))
     )