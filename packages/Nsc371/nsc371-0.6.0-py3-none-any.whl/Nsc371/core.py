"""
Nsc371 核心编译器
包含 main 函数
"""

import re
import argparse
import os
import sys
import random
from typing import Any, Union, Optional, List

class SuperCodeError(Exception):
    """SuperCode 基础异常类"""
    pass

class CompilationError(SuperCodeError):
    """编译错误异常类"""
    pass

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

class Lexer:
    def __init__(self, code):
        self.code = code
    
    def tokenize(self):
        tokens = []
        lines = self.code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            if line.strip():
                tokens.append(Token('LINE', line, line_num))
        
        return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
    
    def parse(self):
        statements = []
        for token in self.tokens:
            content = token.value
            
            # 检测函数调用语法：函数名(参数)
            function_call_match = re.match(r'(\w+)\(([^)]*)\)', content.strip())
            
            if function_call_match:
                # 函数调用格式
                func_name = function_call_match.group(1)
                args_str = function_call_match.group(2)
                # 分割参数（支持逗号分隔或空格分隔）
                args = [arg.strip() for arg in re.split(r'[,\s]+', args_str) if arg.strip()]
                
                statements.append({
                    'type': 'function_call',
                    'content': content,
                    'line': token.line,
                    'indent': len(content) - len(content.lstrip()),
                    'func_name': func_name,
                    'args': args
                })
            else:
                # 传统命令格式
                statements.append({
                    'type': 'raw_line',
                    'content': content,
                    'line': token.line,
                    'indent': len(content) - len(content.lstrip())
                })
        
        return statements

class Compiler:
    def __init__(self):
        self.functions = {}
        self.block_handlers = {}
        self.classes = {}
    
    def set_func(self, name, func):
        self.functions[name] = func
        return self
    
    def set_block_handler(self, keyword, handler):
        self.block_handlers[keyword] = handler
        return self
    
    def compile(self, code):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        statements = parser.parse()
        
        results = []
        i = 0
        while i < len(statements):
            statement = statements[i]
            result, skip_lines = self._execute_free(statement, statements, i)
            if result is not None:
                results.append(result)
            i += skip_lines + 1
        
        return results
    
    def _execute_free(self, statement, all_statements, current_index):
        line_content = statement['content'].strip()
        
        # 检查是否是函数调用格式
        if statement['type'] == 'function_call':
            func_name = statement['func_name']
            args = statement['args']
            
            # 检查块处理器
            block_handler = self.block_handlers.get(func_name)
            if block_handler:
                return block_handler(args, all_statements, current_index, self)
            
            # 检查普通函数
            func = self.functions.get(func_name)
            if func:
                try:
                    return func(*args), 0
                except Exception as e:
                    return f"Error calling {func_name}: {e}", 0
            
            return f"Unknown function: {func_name}", 0
        
        else:
            # 原有的空格分割逻辑
            parts = line_content.split()
            if not parts:
                return None, 0
            
            first_word = parts[0]
            rest = parts[1:]
            
            # 检查块处理器
            block_handler = self.block_handlers.get(first_word)
            if block_handler:
                return block_handler(rest, all_statements, current_index, self)
            
            # 检查普通函数
            func = self.functions.get(first_word)
            if func:
                try:
                    return func(*rest), 0
                except:
                    return func(line_content), 0
            
            return None, 0

# ==================== 对象系统 ====================

class SuperObject:
    """基础对象类"""
    def __init__(self, value: Any, obj_type: str):
        self.value = value
        self.type = obj_type
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return f"{self.type}({self.value})"

class String(SuperObject):
    """字符串对象"""
    def __init__(self, value: str):
        super().__init__(value, "String")

class Int(SuperObject):
    """数字对象"""
    def __init__(self, value: int):
        super().__init__(value, "Int")

class Bool(SuperObject):
    """布尔对象"""
    def __init__(self, value: bool):
        super().__init__(value, "Bool")

class Any(SuperObject):
    """万能对象"""
    def __init__(self, value: Any):
        super().__init__(value, "Any")

def string(value: str) -> String:
    """创建字符串对象"""
    return String(value)

def optional(obj: Any) -> dict:
    """创建可选对象"""
    return {"type": "optional", "value": obj}

def r_input(context_var: str) -> dict:
    """创建输入对象，将内容输入到变量"""
    return {"type": "input", "var": context_var}

def endl() -> String:
    """换行对象"""
    return String("\n")

def expr_format(*patterns):
    """
    解析格式化表达式
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def Cexal(expression: str) -> Bool:
    """
    计算表达式并返回布尔值
    """
    result = _enhanced_safe_eval(expression)
    
    if isinstance(result, Bool):
        return result
    else:
        return Bool(bool(result))

# ==================== 修改的 safe_eval 函数 ====================

def _has_string_operands(expr):
    return '"' in expr or "'" in expr

def _eval_string_concat(expr, functions):
    parts = []
    current = ""
    in_string = False
    string_char = None
    escape = False
    
    for i, char in enumerate(expr):
        if escape:
            current += char
            escape = False
        elif char == '\\':
            current += char
            escape = True
        elif char in ('"', "'") and not in_string:
            in_string = True
            string_char = char
            current += char
        elif char == string_char and in_string:
            in_string = False
            current += char
            parts.append(current)
            current = ""
        elif char == '+' and not in_string:
            if current.strip():
                parts.append(current.strip())
            parts.append('+')
            current = ""
        else:
            current += char
    
    if current.strip():
        parts.append(current.strip())
    
    result_parts = []
    for part in parts:
        if part == '+':
            continue
        elif part.startswith(('"', "'")):
            result_parts.append(part[1:-1])
        else:
            evaluated = safe_eval(part, functions)
            result_parts.append(str(evaluated))
    
    return "".join(result_parts)

def _enhanced_safe_eval(expression, functions=None):
    if functions is None:
        functions = {}
    
    # 修改：如果表达式是字符串，直接返回而不计算
    if isinstance(expression, str):
        expression = expression.strip()
        # 只对字符串字面量去掉引号，其他表达式保持为字符串
        if (expression.startswith('"') and expression.endswith('"')) or \
           (expression.startswith("'") and expression.endswith("'")):
            return expression[1:-1]
        # 其他所有情况返回原始字符串
        return expression
    
    if isinstance(expression, (int, float)):
        return expression
    
    expr = expression.strip() if isinstance(expression, str) else str(expression)
    
    if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
        return expr[1:-1]
    
    if '+' in expr and _has_string_operands(expr):
        try:
            return _eval_string_concat(expr, functions)
        except:
            return f"String concat error: {expr}"
    
    if ' or ' in expr:
        parts = expr.split(' or ', 1)
        left = _enhanced_safe_eval(parts[0], functions)
        right = _enhanced_safe_eval(parts[1], functions)
        return Bool(bool(left) or bool(right))
    
    elif ' and ' in expr:
        parts = expr.split(' and ', 1)
        left = _enhanced_safe_eval(parts[0], functions)
        right = _enhanced_safe_eval(parts[1], functions)
        return Bool(bool(left) and bool(right))
    
    elif expr.startswith('not '):
        inner = _enhanced_safe_eval(expr[4:], functions)
        return Bool(not bool(inner))
    
    comparisons = ['==', '!=', '>=', '<=', '>', '<']
    for op in comparisons:
        if f' {op} ' in expr:
            left_str, right_str = expr.split(f' {op} ', 1)
            left = _original_safe_eval(left_str.strip(), functions)
            right = _original_safe_eval(right_str.strip(), functions)
            
            if op == '==':
                return Bool(left == right)
            elif op == '!=':
                return Bool(left != right)
            elif op == '>=':
                return Bool(left >= right)
            elif op == '<=':
                return Bool(left <= right)
            elif op == '>':
                return Bool(left > right)
            elif op == '<':
                return Bool(left < right)
    
    try:
        if '.' in expr:
            return float(expr)
        else:
            return int(expr)
    except ValueError:
        pass
    
    func_call_match = re.match(r'(\w+)\(([^)]*)\)', expr)
    if func_call_match:
        func_name = func_call_match.group(1)
        args_str = func_call_match.group(2)
        
        if func_name in functions:
            args = []
            if args_str.strip():
                raw_args = [arg.strip() for arg in re.split(r',', args_str) if arg.strip()]
                for arg in raw_args:
                    args.append(_enhanced_safe_eval(arg, functions))
            
            func = functions[func_name]
            try:
                return func(*args)
            except Exception as e:
                return f"Error in {func_name}: {e}"
        else:
            return f"Unknown function: {func_name}"
    
    if all(c in '0123456789+-*/.() ' for c in expr):
        try:
            return eval(expr)
        except:
            return f"Math error: {expr}"
    
    if expr in functions:
        return functions[expr]()
    
    return expr

def _original_safe_eval(expression, functions=None):
    if functions is None:
        functions = {}
    
    # 修改：如果表达式是字符串，直接返回而不计算
    if isinstance(expression, str):
        expression = expression.strip()
        # 只对字符串字面量去掉引号，其他表达式保持为字符串
        if (expression.startswith('"') and expression.endswith('"')) or \
           (expression.startswith("'") and expression.endswith("'")):
            return expression[1:-1]
        # 其他所有情况返回原始字符串
        return expression
    
    if isinstance(expression, (int, float)):
        return expression
    
    expr = expression.strip() if isinstance(expression, str) else str(expression)
    
    if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
        return expr[1:-1]
    
    try:
        if '.' in expr:
            return float(expr)
        else:
            return int(expr)
    except ValueError:
        pass
    
    func_call_match = re.match(r'(\w+)\(([^)]*)\)', expr)
    if func_call_match:
        func_name = func_call_match.group(1)
        args_str = func_call_match.group(2)
        
        if func_name in functions:
            args = []
            if args_str.strip():
                raw_args = [arg.strip() for arg in re.split(r',', args_str) if arg.strip()]
                for arg in raw_args:
                    args.append(_original_safe_eval(arg, functions))
            
            func = functions[func_name]
            try:
                return func(*args)
            except Exception as e:
                return f"Error in {func_name}: {e}"
        else:
            return f"Unknown function: {func_name}"
    
    if all(c in '0123456789+-*/.() ' for c in expr):
        try:
            return eval(expr)
        except:
            return f"Math error: {expr}"
    
    if expr in functions:
        return functions[expr]()
    
    return expr

def safe_eval(expression, functions=None):
    result = _enhanced_safe_eval(expression, functions)
    if isinstance(result, Bool):
        return result.value
    return result

# ==================== 条件处理函数 ====================

@expr_format(string('if'), optional(string('(')), r_input('condition'), optional(')'), string(':'), endl(), r_input('body'))
def h_if(condition: str, body: str):
    """
    处理 if 语句
    """
    condition_result = Cexal(condition)
    
    if condition_result.value:
        return f"Execute: {body}"
    else:
        return None

# ==================== 编译器增强 ====================

def _register_advanced_functions(compiler):
    compiler.set_func("if", lambda condition, body: h_if(condition, body))
    compiler.set_func("cexal", lambda expr: Cexal(expr).value)
    compiler.set_func("string", string)
    compiler.set_func("int_obj", Int)
    compiler.set_func("bool_obj", Bool)
    compiler.set_func("any_obj", Any)
    compiler.set_func("Cexal", lambda expr: Cexal(expr).value)

def _create_compiler_with_builtins():
    compiler = Compiler()
    
    # 基础函数 - 只返回值，不输出
    compiler.set_func("print", lambda *args: " ".join(str(arg) for arg in args))
    compiler.set_func("echo", lambda *args: " ".join(str(arg) for arg in args))
    compiler.set_func("calc", lambda expr: safe_eval(expr, compiler.functions))
    compiler.set_func("add", lambda a, b: int(a) + int(b))
    compiler.set_func("sub", lambda a, b: int(a) - int(b))
    compiler.set_func("mul", lambda a, b: int(a) * int(b))
    compiler.set_func("div", lambda a, b: int(a) / int(b) if int(b) != 0 else "Error: Division by zero")
    
    # 字符串函数
    compiler.set_func("upper", lambda s: s.upper())
    compiler.set_func("lower", lambda s: s.lower())
    compiler.set_func("len", lambda s: len(s))
    compiler.set_func("concat", lambda a, b: str(a) + str(b))
    
    # 注册高级函数
    _register_advanced_functions(compiler)
    
    return compiler

# ==================== 命令行功能 ====================

def _execute_code(compiler, code, verbose=False):
    try:
        results = compiler.compile(code)
        return results
    except Exception as e:
        return [f"Execution error: {e}"]

def _execute_file(compiler, filename, verbose=False):
    if not os.path.exists(filename):
        return [f"File not found: {filename}"]
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        results = compiler.compile(code)
        return results
            
    except Exception as e:
        return [f"File execution error: {e}"]

def _show_help():
    return """
Nsc371 Help:

Commands:
  help, ?       Show this help
  exit, quit    Exit REPL
  clear         Clear screen
  funcs         Show available functions
  eval <expr>   Evaluate expression

Built-in functions:
  print, echo   Output text
  calc          Calculate expression
  add, sub      Arithmetic operations
  mul, div      Multiplication and division
  upper, lower  Case conversion
  len           String length
  concat        String concatenation
  cexal         Conditional expression
  if            Conditional statement
"""

def _show_functions(compiler):
    functions = list(compiler.functions.keys())
    return f"Available functions: {', '.join(functions)}"

def _start_repl(compiler):
    print(f"Nsc371 REPL v{__version__}")
    print("Type 'help' for help, 'exit' to quit")
    
    while True:
        try:
            line = input("nsc> ").strip()
            
            if not line:
                continue
                
            if line.lower() in ('exit', 'quit', 'q'):
                break
            elif line.lower() in ('help', '?'):
                print(_show_help())
                continue
            elif line.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            elif line.lower() == 'funcs':
                print(_show_functions(compiler))
                continue
            elif line.lower().startswith('eval '):
                expr = line[5:].strip()
                result = safe_eval(expr, compiler.functions)
                print(f"= {result}")
                continue
            
            results = compiler.compile(line)
            for result in results:
                if result is not None:
                    print(result)
                    
        except KeyboardInterrupt:
            break
        except EOFError:
            break

def main():
    parser = argparse.ArgumentParser(description='Nsc371 - Simple Script Interpreter')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-c', '--code', help='Execute single line of code')
    group.add_argument('-e', '--eval', help='Evaluate expression')
    group.add_argument('file', nargs='?', help='Script file to execute')
    
    parser.add_argument('-v', '--version', action='store_true', help='Show version information')
    parser.add_argument('--verbose', action='store_true', help='Verbose output mode')
    
    args = parser.parse_args()
    
    compiler = _create_compiler_with_builtins()
    
    if args.version:
        print(f"Nsc371 v{__version__}")
        return
    
    if args.code:
        results = _execute_code(compiler, args.code, verbose=args.verbose)
        for result in results:
            if result is not None:
                print(result)
    elif args.eval:
        result = safe_eval(args.eval, compiler.functions)
        print(result)
    elif args.file:
        results = _execute_file(compiler, args.file, verbose=args.verbose)
        for result in results:
            if result is not None:
                print(result)
    else:
        _start_repl(compiler)

# ==================== 便捷函数 ====================

def set_func(name, func):
    def config(compiler):
        compiler.set_func(name, func)
    return config

def set_block_handler(keyword, handler):
    def config(compiler):
        compiler.set_block_handler(keyword, handler)
    return config

def Compiler_Code(code):
    return Compiler().compile(code)

# ==================== 版本信息 ====================

__version__ = "0.5.0"

if __name__ == "__main__":
    main()