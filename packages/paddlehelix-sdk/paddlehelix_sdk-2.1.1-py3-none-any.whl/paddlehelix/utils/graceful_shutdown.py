"""
优雅退出处理模块

提供信号处理和优雅退出功能，确保在收到SIGTERM/SIGINT信号时
能够等待当前API调用完成，保存任务状态，并正确清理资源。
"""

import signal
import sys
import threading
import time
import logging
from contextlib import contextmanager
from typing import Optional, Callable, Any


class GracefulShutdown:
    """
    优雅退出上下文管理器
    
    捕获SIGTERM和SIGINT信号，提供优雅退出机制，
    确保关键操作完成后再退出程序。
    """
    
    def __init__(self, timeout: int = 30, logger: Optional[logging.Logger] = None):
        """
        初始化优雅退出管理器
        
        Args:
            timeout: 最大等待时间（秒），超时后强制退出
            logger: 日志记录器，如果为None则使用默认logger
        """
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self._shutdown_requested = False
        self._current_operation = None
        self._operation_lock = threading.Lock()
        self._original_handlers = {}
        
    def __enter__(self):
        """进入上下文，注册信号处理器"""
        self._register_signal_handlers()
        self.logger.debug("Graceful shutdown manager activated")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，清理资源"""
        self._unregister_signal_handlers()
        self.logger.debug("Graceful shutdown manager deactivated")
        
    def _register_signal_handlers(self):
        """注册信号处理器"""
        signals = [signal.SIGTERM, signal.SIGINT]
        for sig in signals:
            self._original_handlers[sig] = signal.signal(sig, self._signal_handler)
            
    def _unregister_signal_handlers(self):
        """恢复原始信号处理器"""
        for sig, handler in self._original_handlers.items():
            signal.signal(sig, handler)
            
    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        signal_name = signal.Signals(signum).name
        self.logger.warning(f"Received signal {signal_name}, starting graceful shutdown...")
        self._shutdown_requested = True
        
        # 如果有正在进行的操作，记录日志但不等待
        if self._current_operation:
            self.logger.info(f"Current operation will complete and then exit: {self._current_operation}")
        else:
            self.logger.info("No current operation, exiting immediately")
            sys.exit(0)
            
            
    def is_shutdown_requested(self) -> bool:
        """检查是否收到退出信号"""
        return self._shutdown_requested
        
    @contextmanager
    def protect_operation(self, operation_name: str):
        """
        保护关键操作的上下文管理器
        
        Args:
            operation_name: 操作名称，用于日志记录
        """
        with self._operation_lock:
            if self._shutdown_requested:
                self.logger.info(f"Shutdown signal received, but allowing operation {operation_name} to complete")
                
            self._current_operation = operation_name
            self.logger.debug(f"Starting protected operation: {operation_name}")
            
        try:
            yield
        finally:
            with self._operation_lock:
                self._current_operation = None
                self.logger.debug(f"Completed protected operation: {operation_name}")
                
                # 如果收到关闭信号且操作已完成，立即退出
                if self._shutdown_requested:
                    self.logger.info(f"Operation {operation_name} completed, exiting ...")
                    sys.exit(0)
                
    def check_shutdown(self):
        """检查退出信号，如果收到则抛出异常"""
        if self._shutdown_requested:
            raise KeyboardInterrupt("Shutdown signal received, operation interrupted")


# 全局实例，用于跨模块共享状态
_global_shutdown_manager: Optional[GracefulShutdown] = None


def get_global_shutdown_manager() -> Optional[GracefulShutdown]:
    """获取全局优雅退出管理器实例"""
    return _global_shutdown_manager


def set_global_shutdown_manager(manager: GracefulShutdown):
    """设置全局优雅退出管理器实例"""
    global _global_shutdown_manager
    _global_shutdown_manager = manager


def is_shutdown_requested() -> bool:
    """检查是否收到退出信号（全局检查）"""
    manager = get_global_shutdown_manager()
    return manager.is_shutdown_requested() if manager else False


def check_shutdown():
    """检查退出信号，如果收到则抛出异常（全局检查）"""
    manager = get_global_shutdown_manager()
    if manager:
        manager.check_shutdown()
