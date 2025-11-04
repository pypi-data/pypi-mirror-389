"""
Nsc410 增强版表达式处理器
与 Nsc371 并存，支持用户注册的函数
"""

import re
from core import Compiler

class Nsc410Processor:
    """Nsc410 表达式处理器，支持 Nsc371 注册的函数"""
    
    def __init__(self, compiler=None):
        self.compiler = compiler or Compiler()
    
    def set_compiler(self, compiler):
        """设置编译器实例以获取注册的函数"""
        self.compiler = compiler
    
    def Ns4ev(self, eval_sif, space=None):
        """Ns4ev->es - 增强版表达式处理器"""
        original_input = eval_sif  # 保存原始输入
        
        if space == True:
            pass
        else:
            eval_sif = eval_sif.replace(' ', '')
        
        # 首先检查是否是函数调用（放在最前面）
        func_call_match = re.match(r'^(\w+)\((.*)\)$', eval_sif)
        if func_call_match:
            return self._execute_function_call(func_call_match)
        
        # 处理原始字符串 (r-string)
        if eval_sif.startswith(('r"', "r'")) and eval_sif.endswith(('"', "'")):
            return eval_sif[2:-1]
        
        # 处理字节字符串 (b-string)
        if eval_sif.startswith(('b"', "b'")) and eval_sif.endswith(('"', "'")):
            return eval(eval_sif)
        
        # 处理格式化字符串 (f-string)
        if eval_sif.startswith(('f"', "f'")) and eval_sif.endswith(('"', "'")):
            quote_char = eval_sif[1]
            f_content = eval_sif[2:-1]
            
            # 匹配 {} 中的表达式
            pattern = r'\{([^}]+)\}'
            matches = re.findall(pattern, f_content)
            
            for expr in matches:
                try:
                    # 递归处理 f-string 中的表达式
                    result = str(self.Ns4ev(expr, space))
                    f_content = f_content.replace('{' + expr + '}', result)
                except Exception as e:
                    raise SyntaxError(f'Error: Nsc410 f-string expression "{expr}" is wrong: {e}')
            return f_content
        
        # 处理多行字符串 (三重引号)
        if eval_sif.startswith(('"""', "'''")) and eval_sif.endswith(('"""', "'''")):
            return eval_sif[3:-3]
        
        # 处理普通字符串拼接
        if '"' in eval_sif or "'" in eval_sif:
            # 确定引号类型
            if '"' in eval_sif and "'" in eval_sif:
                if eval_sif.count('"') > eval_sif.count("'"):
                    quote_char = '"'
                else:
                    quote_char = "'"
            elif '"' in eval_sif:
                quote_char = '"'
            else:
                quote_char = "'"
            
            # 分割并处理字符串
            list_es = eval_sif.split(quote_char)
            list_es = [i for i in list_es if i != '' and i != '+']
            result = ''.join(list_es)
            
            # 处理转义字符
            result = (result.replace('\\n', '\n')
                           .replace('\\t', '\t')
                           .replace('\\r', '\r')
                           .replace('\\\\', '\\'))
            return result
        
        # 处理数学表达式
        try:
            # 简单的数学表达式求值
            if all(c in '0123456789+-*/.()' for c in eval_sif):
                return eval(eval_sif)
        except:
            pass
        
        # 如果以上都不匹配，返回原始字符串
        return original_input
    
    def _execute_function_call(self, match):
        """执行函数调用"""
        func_name = match.group(1)
        args_str = match.group(2)
        
        if not self.compiler or func_name not in self.compiler.functions:
            raise SyntaxError(f'Unknown function: {func_name}')
        
        # 解析参数
        args = self._parse_arguments(args_str)
        
        # 获取函数并执行
        func = self.compiler.functions[func_name]
        try:
            return func(*args)
        except Exception as e:
            raise SyntaxError(f'Error calling {func_name}: {e}')
    
    def _parse_arguments(self, args_str):
        """解析参数"""
        if not args_str.strip():
            return []
        
        args = []
        current_arg = ""
        in_string = False
        string_char = None
        escape = False
        
        i = 0
        while i < len(args_str):
            char = args_str[i]
            
            if escape:
                current_arg += char
                escape = False
            elif char == '\\':
                current_arg += char
                escape = True
            elif char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
                current_arg += char
            elif char == string_char and in_string:
                in_string = False
                current_arg += char
            elif char == ',' and not in_string:
                # 参数分隔符 - 只在字符串外部分割
                parsed_arg = self._clean_single_argument(current_arg.strip())
                args.append(parsed_arg)
                current_arg = ""
            else:
                current_arg += char
            
            i += 1
        
        # 添加最后一个参数
        if current_arg.strip():
            parsed_arg = self._clean_single_argument(current_arg.strip())
            args.append(parsed_arg)
        
        return args
    
    def _clean_single_argument(self, arg):
        """清理单个参数"""
        # 如果是带引号的字符串，去掉引号并处理转义
        if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
            content = arg[1:-1]
            # 处理转义字符
            content = (content.replace('\\n', '\n')
                             .replace('\\t', '\t')
                             .replace('\\r', '\r')
                             .replace('\\\\', '\\'))
            return content
        
        # 如果是数字，转换为数字
        try:
            if '.' in arg:
                return float(arg)
            else:
                return int(arg)
        except ValueError:
            pass
        
        # 如果是函数调用，递归处理
        func_call_match = re.match(r'^(\w+)\((.*)\)$', arg)
        if func_call_match:
            return self._execute_function_call(func_call_match)
        
        # 其他情况返回原始值
        return arg

# ==================== 便捷函数 ====================

# 全局处理器实例
_global_processor = Nsc410Processor()

def Ns4ev(eval_sif, space=None, compiler=None):
    """便捷函数，支持指定编译器"""
    if compiler:
        processor = Nsc410Processor(compiler)
        return processor.Ns4ev(eval_sif, space)
    else:
        return _global_processor.Ns4ev(eval_sif, space)

def set_compiler(compiler):
    """设置全局编译器实例"""
    _global_processor.set_compiler(compiler)
                                                                                                                                                                                                                                                      
