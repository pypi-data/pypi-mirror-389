# coding: utf-8
"""
QPS (Queries Per Second) 异常处理模块

该模块提供QPS限流异常的识别、转换和处理功能，
完全独立于OpenAPI Generator生成的代码。
"""

import json
import logging

logger = logging.getLogger(__name__)


class QPSError(Exception):
    """QPS相关异常的基础类"""
    pass


class QPSLimitExceededException(QPSError):
    """QPS限流异常"""
    
    def __init__(self, original_exception, retry_after=None, limit_info=None):
        self.original_exception = original_exception
        self.retry_after = retry_after
        self.limit_info = limit_info
        self.is_qps_limit = True
        self.status = getattr(original_exception, 'status', None)
        self.reason = getattr(original_exception, 'reason', None)
        
        # 构建异常消息
        message = f"QPS Limit Exceeded: {self.reason or 'Unknown reason'}"
        if self.retry_after:
            message += f" (Retry after: {self.retry_after}s)"
        
        super().__init__(message)
    
    def __str__(self):
        return self.args[0]


def is_qps_limit_exception(exception):
    """
    判断是否为QPS限流异常
    
    Args:
        exception: 异常对象
        
    Returns:
        bool: 是否为QPS限流异常
    """
    # 检查HTTP状态码
    if hasattr(exception, 'status') and exception.status == 429:
        return True
    
    # 检查响应体中的限流信息
    if hasattr(exception, 'body') and exception.body:
        try:
            body_str = str(exception.body).lower()
            qps_keywords = ['rate_limit', 'qps', 'throttle', 'too many requests', '限流', '请求过于频繁']
            if any(keyword in body_str for keyword in qps_keywords):
                return True
        except Exception:
            pass
    
    # 检查异常消息
    if hasattr(exception, 'reason') and exception.reason:
        reason_str = str(exception.reason).lower()
        qps_keywords = ['rate_limit', 'qps', 'throttle', 'too many requests', '限流', '请求过于频繁']
        if any(keyword in reason_str for keyword in qps_keywords):
            return True
    
    return False


def convert_to_qps_exception(original_exception):
    """
    将原始异常转换为QPS异常
    
    Args:
        original_exception: 原始异常对象
        
    Returns:
        QPSLimitExceededException: QPS限流异常对象，如果不是限流异常则返回原异常
    """
    if is_qps_limit_exception(original_exception):
        # 尝试从响应头中提取重试时间信息
        retry_after = None
        limit_info = {}
        
        if hasattr(original_exception, 'headers') and original_exception.headers:
            headers = original_exception.headers
            if 'retry-after' in headers:
                try:
                    retry_after = int(headers['retry-after'])
                except (ValueError, TypeError):
                    pass
            
            # 提取其他限流相关信息
            for key, value in headers.items():
                if key.lower().startswith('x-ratelimit-'):
                    limit_info[key] = value
        
        return QPSLimitExceededException(
            original_exception=original_exception,
            retry_after=retry_after,
            limit_info=limit_info
        )
    
    return original_exception


def extract_qps_info(exception):
    """
    从异常中提取QPS相关信息
    
    Args:
        exception: 异常对象
        
    Returns:
        dict: 包含QPS信息的字典
    """
    info = {
        'is_qps_limit': False,
        'retry_after': None,
        'limit_info': {},
        'status': None,
        'reason': None
    }
    
    if is_qps_limit_exception(exception):
        info['is_qps_limit'] = True
        info['status'] = getattr(exception, 'status', None)
        info['reason'] = getattr(exception, 'reason', None)
        
        # 如果是QPS异常，提取更多信息
        if hasattr(exception, 'is_qps_limit') and exception.is_qps_limit:
            info['retry_after'] = getattr(exception, 'retry_after', None)
            info['limit_info'] = getattr(exception, 'limit_info', {})
    
    return info
