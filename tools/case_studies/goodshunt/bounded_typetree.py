"""Reject malformed inferred array lengths before allocation; pure Python parser."""
from UnityPy.helpers import TypeTreeHelper as H
H.read_typetree_boost = None
original_value = H.read_value
original_array = H.read_value_array
def check(size,reader,byte_array=False):
    limit=64*1024*1024 if byte_array else 1000000
    if size < 0 or size > limit or size > reader.Length:
        raise ValueError('Invalid or excessive array size ' + str(size))
def value(node,reader,config):
    if node.m_Children and node.m_Children[0].m_Type == 'Array':
        pos=reader.Position
        size=reader.read_int()
        reader.Position=pos
        child=node.m_Children[0].m_Children[1]
        check(size,reader,child.m_Type in ['UInt8','char','SInt8'] and not child.m_Children)
    return original_value(node,reader,config)
def array(node,reader,config,size):
    check(size,reader,node.m_Type in ['UInt8','char','SInt8'] and not node.m_Children)
    if node.m_Children and node.m_Children[0].m_Type == 'Array':
        return [value(node,reader,config) for _ in range(size)]
    return original_array(node,reader,config,size)
H.read_value=value
H.read_value_array=array
