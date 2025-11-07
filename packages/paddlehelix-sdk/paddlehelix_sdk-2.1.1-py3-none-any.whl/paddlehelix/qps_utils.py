# coding: utf-8
"""
QPS (Queries Per Second) 工具函数模块

该模块提供QPS控制、重试机制和智能休眠等工具函数，
完全独立于OpenAPI Generator生成的代码。
"""

import time
import logging
from functools import wraps
from paddlehelix.qps_exceptions import is_qps_limit_exception

logger = logging.getLogger(__name__)


def calculate_retry_delay(attempt, base_delay, max_delay, multiplier):
    """
    计算指数退避重试延迟
    
    Args:
        attempt (int): 当前重试次数（从1开始）
        base_delay (float): 基础重试延迟（秒）
        max_delay (float): 最大重试延迟（秒）
        multiplier (float): 重试延迟倍数
        
    Returns:
        float: 计算出的重试延迟时间（秒）
    """
    delay = base_delay * (multiplier ** (attempt - 1))
    return min(delay, max_delay)


def qps_aware_retry(max_retries=5, base_delay=1, max_delay=60, multiplier=2):
    """
    QPS感知的重试装饰器
    
    Args:
        max_retries (int): 最大重试次数
        base_delay (float): 基础重试延迟（秒）
        max_delay (float): 最大重试延迟（秒）
        multiplier (float): 重试延迟倍数
        
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否为QPS限流异常
                    if is_qps_limit_exception(e):
                        if attempt < max_retries:
                            delay = calculate_retry_delay(
                                attempt + 1, base_delay, max_delay, multiplier
                            )
                            logger.warning(
                                f"QPS limit hit, retrying in {delay:.1f}s "
                                f"(attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(f"QPS limit exceeded, max retries ({max_retries}) reached")
                    else:
                        # 非限流异常，直接抛出
                        logger.debug(f"Non-QPS exception occurred: {type(e).__name__}")
                    break
            
            raise last_exception
        
        return wrapper
    
    return decorator


def smart_sleep_for_qps(qps_value, last_call_time=None):
    """
    智能QPS休眠函数
    
    Args:
        qps_value (float): QPS值（每秒请求数）
        last_call_time (float, optional): 上次调用时间戳
        
    Returns:
        float: 下次可用的时间戳
    """
    if qps_value <= 0:
        return time.time()
    
    current_time = time.time()
    if last_call_time is None:
        return current_time
    
    min_interval = 1.0 / qps_value
    elapsed = current_time - last_call_time
    
    if elapsed < min_interval:
        sleep_time = min_interval - elapsed
        if sleep_time > 0.001:  # 只对大于1ms的延迟进行休眠
            logger.debug(f"QPS control: sleeping for {sleep_time:.3f}s")
            time.sleep(sleep_time)
            return current_time + sleep_time
    
    return current_time


def handle_qps_exception(exception, max_retries=3, base_delay=1, max_delay=30):
    """
    处理QPS异常的统一接口
    
    Args:
        exception: 异常对象
        max_retries (int): 最大重试次数
        base_delay (float): 基础重试延迟（秒）
        max_delay (float): 最大重试延迟（秒）
        
    Returns:
        bool: True表示应该重试，False表示不应该重试
    """
    if not hasattr(exception, 'is_qps_limit') or not exception.is_qps_limit:
        return False
    
    logger.warning(f"QPS limit exceeded: {getattr(exception, 'reason', 'Unknown reason')}")
    
    # 检查是否有建议的重试时间
    retry_after = getattr(exception, 'retry_after', None)
    if retry_after is not None:
        delay = min(retry_after, max_delay)
        logger.info(f"Using server-suggested retry delay: {delay}s")
    else:
        delay = min(base_delay, max_delay)
        logger.info(f"Using default retry delay: {delay}s")
    
    if max_retries > 0:
        time.sleep(delay)
        return True
    
    return False


def create_qps_controller(qps_limit, burst_allowance=1.0):
    """
    创建QPS控制器
    
    Args:
        qps_limit (float): QPS限制值
        burst_allowance (float): 突发请求允许倍数
        
    Returns:
        function: QPS控制函数
    """
    last_call_time = None
    min_interval = 1.0 / qps_limit if qps_limit > 0 else 0
    
    def qps_control():
        nonlocal last_call_time
        current_time = time.time()
        
        if last_call_time is not None:
            elapsed = current_time - last_call_time
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                if sleep_time > 0.001:
                    time.sleep(sleep_time)
                    current_time = time.time()
        
        last_call_time = current_time
        return current_time
    
    return qps_control


def adaptive_qps_sleep(current_qps, target_qps, last_call_time=None, 
                      adjustment_factor=0.1, min_interval=0.1):
    """
    自适应QPS休眠函数
    
    Args:
        current_qps (float): 当前实际QPS
        target_qps (float): 目标QPS
        last_call_time (float, optional): 上次调用时间戳
        adjustment_factor (float): 调整因子
        min_interval (float): 最小间隔时间
        
    Returns:
        float: 下次可用的时间戳
    """
    if target_qps <= 0:
        return time.time()
    
    current_time = time.time()
    if last_call_time is None:
        return current_time
    
    # 计算当前间隔
    current_interval = current_time - last_call_time
    
    # 根据当前QPS与目标QPS的差异调整休眠时间
    if current_qps > target_qps:
        # 当前QPS过高，增加休眠时间
        target_interval = 1.0 / target_qps
        adjustment = (current_qps - target_qps) * adjustment_factor
        sleep_time = max(target_interval + adjustment - current_interval, min_interval)
        
        if sleep_time > 0.001:
            logger.debug(f"Adaptive QPS control: sleeping for {sleep_time:.3f}s")
            time.sleep(sleep_time)
            return current_time + sleep_time
    
    return current_time
