"""


"""

import functools
from typing import Any, Dict, List, Optional, Callable, Type
from functools import wraps
from mcp.server.session import ServerSession
from mcp.server.fastmcp import Context
from mcp.types import CallToolResult, TextContent

from .validation import ValidationError, validate_econometric_data, validate_model_parameters
from .cache import cache_result, cache_model, global_econometric_cache
from .monitoring import monitor_performance, track_progress, global_performance_monitor
from .file_parser import FileParser
from ..config import get_config, econometric_config


# ============================================================================
# 
# ============================================================================

class EconometricToolError(Exception):
    """"""
    
    def __init__(self, message: str, tool_name: str = None, original_error: Exception = None):
        self.message = message
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self):
        base_msg = f""
        if self.tool_name:
            base_msg += f" ({self.tool_name})"
        base_msg += f": {self.message}"
        if self.original_error:
            base_msg += f"\n: {self.original_error}"
        return base_msg


class DataValidationError(EconometricToolError):
    """"""
    pass


class ModelFittingError(EconometricToolError):
    """"""
    pass


class ConfigurationError(EconometricToolError):
    """"""
    pass


# ============================================================================
# 
# ============================================================================

def with_file_input(tool_type: str):
    """
    
    
    
    1. file_path: CSV/JSON
    2. file_content: 
    
    Args:
        tool_type:  ('single_var', 'multi_var_dict', 'regression', 'panel', 'time_series')
    
    :
        @with_file_input('regression')
        async def my_tool(ctx, y_data=None, x_data=None, file_path=None, file_content=None, file_format='auto', **kwargs):
            # file_pathfile_content
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 
            ctx = args[0] if args else kwargs.get('ctx')
            file_path = kwargs.get('file_path')
            file_content = kwargs.get('file_content')
            file_format = kwargs.get('file_format', 'auto')
            
            # file_path
            if file_path:
                try:
                    await ctx.info(f": {file_path}")
                    
                    # 
                    parsed = FileParser.parse_file_path(file_path, file_format)
                    
                    await ctx.info(
                        f"{parsed['n_variables']}"
                        f"{parsed['n_observations']}"
                    )
                    
                    # 
                    converted = FileParser.convert_to_tool_format(parsed, tool_type)
                    
                    # kwargs
                    kwargs.update(converted)
                    
                    await ctx.info(f"{tool_type}")
                    
                except Exception as e:
                    await ctx.error(f": {str(e)}")
                    return CallToolResult(
                        content=[TextContent(type="text", text=f": {str(e)}")],
                        isError=True
                    )
            
            # file_pathfile_content
            elif file_content:
                try:
                    await ctx.info("...")
                    
                    # 
                    parsed = FileParser.parse_file_content(file_content, file_format)
                    
                    await ctx.info(
                        f"{parsed['n_variables']}"
                        f"{parsed['n_observations']}"
                    )
                    
                    # 
                    converted = FileParser.convert_to_tool_format(parsed, tool_type)
                    
                    # kwargs
                    kwargs.update(converted)
                    
                    await ctx.info(f"{tool_type}")
                    
                except Exception as e:
                    await ctx.error(f": {str(e)}")
                    return CallToolResult(
                        content=[TextContent(type="text", text=f": {str(e)}")],
                        isError=True
                    )
            
            # 
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def with_error_handling(func: Callable) -> Callable:
    """
    
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if args else kwargs.get('ctx')
        tool_name = func.__name__
        
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await ctx.error(f"{tool_name}: {str(e)}")
            return CallToolResult(
                content=[TextContent(type="text", text=f": {str(e)}")],
                isError=True
            )
    
    return wrapper


def with_logging(func: Callable) -> Callable:
    """
    
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if args else kwargs.get('ctx')
        tool_name = func.__name__
        
        await ctx.info(f" {tool_name}")
        result = await func(*args, **kwargs)
        await ctx.info(f"{tool_name} ")
        
        return result
    
    return wrapper


def with_file_support_decorator(
    tool_type: str,
    enable_error_handling: bool = True,
    enable_logging: bool = True
):
    """
    
    
    Args:
        tool_type: 
        enable_error_handling: 
        enable_logging: 
    
    :
        @with_file_support_decorator('regression')
        async def ols_regression(ctx, y_data=None, x_data=None, **kwargs):
            # 
            pass
    """
    def decorator(func: Callable) -> Callable:
        wrapped = func
        
        if enable_error_handling:
            wrapped = with_error_handling(wrapped)
        
        wrapped = with_file_input(tool_type)(wrapped)
        
        if enable_logging:
            wrapped = with_logging(wrapped)
        
        return wrapped
    
    return decorator


# ============================================================================
# 
# ============================================================================

class EconometricTool:
    """
    
    
    """
    
    def __init__(self, tool_name: str):
        """
        
        
        Args:
            tool_name: 
        """
        self.tool_name = tool_name
        self._cache_enabled = get_config("cache_enabled", True)
        self._monitoring_enabled = get_config("monitoring_enabled", True)
        self._validation_strict = get_config("data_validation_strict", True)
    
    def _validate_input_data(self, data: Any, data_type: str = "generic") -> Any:
        """
        
        
        Args:
            data: 
            data_type: 
            
        Returns:
            Any: 
            
        Raises:
            DataValidationError: 
        """
        try:
            if data_type == "econometric":
                return validate_econometric_data(data)
            elif data_type == "time_series":
                from .validation import validate_time_series_data
                return validate_time_series_data(data)
            elif data_type == "model_parameters":
                return validate_model_parameters(data)
            else:
                return data
        except ValidationError as e:
            error_msg = f": {e.message}"
            if self._validation_strict:
                raise DataValidationError(error_msg, self.tool_name, e)
            else:
                # 
                import warnings
                warnings.warn(f"{self.tool_name}: {error_msg}")
                return data
    
    def _handle_errors(self, func: Callable) -> Callable:
        """
        
        
        Args:
            func: 
            
        Returns:
            Callable: 
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (DataValidationError, ModelFittingError, ConfigurationError):
                # 
                raise
            except ValidationError as e:
                # 
                raise DataValidationError(f": {e.message}", self.tool_name, e)
            except Exception as e:
                # 
                error_msg = f": {str(e)}"
                raise EconometricToolError(error_msg, self.tool_name, e)
        
        return wrapper
    
    def _apply_optimizations(self, func: Callable) -> Callable:
        """
        
        
        Args:
            func: 
            
        Returns:
            Callable: 
        """
        # 
        if self._monitoring_enabled:
            func = monitor_performance(self.tool_name)(func)
        
        # 
        if self._cache_enabled:
            cache_config = econometric_config.get_cache_config()
            func = cache_result(ttl=cache_config["ttl"], max_size=cache_config["max_size"])(func)
        
        # 
        func = self._handle_errors(func)
        
        return func
    
    def create_optimized_function(self, func: Callable) -> Callable:
        """
        
        
        Args:
            func: 
            
        Returns:
            Callable: 
        """
        return self._apply_optimizations(func)
    
    def execute_with_progress(self, total_steps: int, description: str = ""):
        """
        
        
        Args:
            total_steps: 
            description: 
            
        Returns:
            ContextManager: 
        """
        return track_progress(total_steps, f"{self.tool_name}: {description}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        
        
        Returns:
            Dict[str, Any]: 
        """
        if not self._monitoring_enabled:
            return {}
        
        stats = global_performance_monitor.get_function_stats(self.tool_name)
        if stats:
            return {
                "execution_time": stats.execution_time,
                "peak_memory_mb": stats.peak_memory_mb,
                "cpu_percent": stats.cpu_percent,
                "timestamp": stats.timestamp
            }
        return {}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        
        
        Returns:
            Dict[str, Any]: 
        """
        if not self._cache_enabled:
            return {}
        
        return global_econometric_cache.result_cache.get_function_cache_stats(self.tool_name) or {}


# ============================================================================
# 
# ============================================================================

def econometric_tool_with_optimization(tool_name: str = None):
    """
    
    
    
    
    Args:
        tool_name: 
        
    Returns:
        Callable: 
        
    :
        @econometric_tool_with_optimization('my_analysis')
        def my_analysis(data):
            # 
            pass
    """
    def decorator(func):
        name = tool_name or func.__name__
        tool = EconometricTool(name)
        return tool.create_optimized_function(func)
    
    return decorator


def validate_input(data_type: str = "generic"):
    """
    
    
    Args:
        data_type: 
        
    Returns:
        Callable: 
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 
            if args:
                validated_args = list(args)
                validated_args[0] = EconometricTool(func.__name__)._validate_input_data(args[0], data_type)
                args = tuple(validated_args)
            
            # 
            validated_kwargs = {}
            for key, value in kwargs.items():
                if key in ["data", "y_data", "x_data"]:
                    validated_kwargs[key] = EconometricTool(func.__name__)._validate_input_data(value, data_type)
                else:
                    validated_kwargs[key] = value
            
            return func(*args, **validated_kwargs)
        
        return wrapper
    
    return decorator


# 
__all__ = [
    # 
    "EconometricToolError",
    "DataValidationError", 
    "ModelFittingError",
    "ConfigurationError",
    # 
    "EconometricTool",
    # 
    "with_file_input",
    "with_error_handling",
    "with_logging",
    "with_file_support_decorator",
    "econometric_tool_with_optimization",
    "validate_input"
]