"""
Compatibility of data structures between different Python versions
"""
import sys

# 兼容低于3.9版本数据结构类型不存在的情况
dict_type = dict
list_type = list
tuple_type = tuple
if sys.version_info < (3, 9):
    # Python 3.8 及以下版本
    from typing import Dict, List, Tuple
    dict_type = Dict
    list_type = List
    tuple_type = Tuple
