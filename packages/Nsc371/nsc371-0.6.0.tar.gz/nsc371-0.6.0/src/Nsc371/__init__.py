from .core import (
    # 编译器核心
    Compiler, Compiler_Code,
    
    # 配置函数
    set_func, set_block_handler,
    
    # 主函数和命令行
    main,
    
    # 表达式计算
    safe_eval, Cexal,
    
    # 对象系统
    String, Int, Bool, Any, string, Int as IntObj, Bool as BoolObj, Any as AnyObj,
    
    # 表达式解析
    expr_format, optional, r_input, endl,
    
    # 条件处理
    h_if,
    

)

from .nsc512 import Ns4ev, set_compiler, Nsc410Processor

__version__ = "0.6.0"
__author__ = "王子毅"

__all__ = [
    # 编译器核心
    'Compiler', 'Compiler_Code',
    
    # 配置函数
    'set_func', 'set_block_handler',
    
    # 主函数和命令行
    'main',
    
    # 表达式计算
    'safe_eval', 'Cexal',
    
    # 对象系统
    'String', 'Int', 'Bool', 'Any', 'string', 'IntObj', 'BoolObj', 'AnyObj',
    
    # 表达式解析
    'expr_format', 'optional', 'r_input', 'endl',
    
    # 条件处理
    'h_if',
    
    # Nsc410 功能
    'Ns4ev', 'set_compiler', 'Nsc410Processor'
]