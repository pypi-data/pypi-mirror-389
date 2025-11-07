# coding: utf-8
"""
SDK 异常处理模块

该模块提供SDK异常的识别、转换和处理功能，
完全独立于OpenAPI Generator生成的代码。
"""

import logging

logger = logging.getLogger(__name__)


class SDKError(Exception):
    """SDK相关异常的基础类"""
    pass
