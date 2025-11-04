import re
from typing import Any, List, Dict, Optional, Tuple

class Token:
    def __init__(self, type_: str, value: str, pos: int):
        self.type = type_; self.value = value; self.pos = pos
    def __repr__(self): return f"Token({self.type}, {self.value!r}, pos={self.pos})"

TOKEN_SPEC = [
    ("NUMBER",   r"\d+(\.\d+)?"),
    ("STRING",   r"'([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\""),
    ("IF",       r"\?\?"),
    ("QMARK",    r"\?"),
    ("AT",       r"@"),
    ("COLON",    r":"),
    ("DOLLAR",   r"\$"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("COMMA",    r","),
    ("SEMICOLON",r";"),
    ("EQ",       r"=="),
    ("NE",       r"!="),
    ("LE",       r"<="),
    ("GE",       r">="),
    ("LT",       r"<"),
    ("GT",       r">"),
    ("ASSIGN",   r"="),
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("MULT",     r"\*"),
    ("DIV",      r"/"),
    ("MOD",      r"%"),
    ("AND",      r"&"),
    ("OR",       r"\|"),
    ("NOT",      r"~"),
    ("PRINT",    r"!"),
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),
    ("SKIP",     r"[ \t\r\n]+"),
    ("DOT",      r"\."),
    ("MISMATCH", r"."),
]
TOKEN_REGEX = "|".join(f"(?P<{name}>{pattern})" for name,pattern in TOKEN_SPEC)
master_re = re.compile(TOKEN_REGEX)

def lex(source: str) -> List[Token]:
    tokens: List[Token] = []
    for mo in master_re.finditer(source):
        kind = mo.lastgroup
        value = mo.group()
        pos = mo.start()
        if kind == "NUMBER":
            tokens.append(Token("NUMBER", value, pos))
        elif kind == "STRING":
            raw = value[1:-1]
            raw = bytes(raw, "utf-8").decode("unicode_escape")
            tokens.append(Token("STRING", raw, pos))
        elif kind in ("IF","QMARK","AT","IDENT","COLON","DOLLAR","LPAREN","RPAREN","LBRACE","RBRACE","COMMA","SEMICOLON",
                      "EQ","NE","LE","GE","LT","GT","ASSIGN","PLUS","MINUS","MULT","DIV","MOD","AND","OR","NOT","PRINT", "DOT"):
            tokens.append(Token(kind, value, pos))
        elif kind == "SKIP":
            continue
        else:
            raise SyntaxError(f"Unexpected character {value!r} at position {pos}")
    tokens.append(Token("EOF", "", len(source)))
    return tokens

def pos_to_linecol(source: str, pos: int) -> Tuple[int,int]:
    line = source.count("\n", 0, pos) + 1
    last_n = source.rfind("\n", 0, pos)
    col = pos - last_n
    return line, col

class ParseError(Exception):
    pass

class Parser:
    PRECEDENCE = {"OR":1,"AND":2,"CMP":3,"PLUS":4,"MULT":5,"UNARY":6}

    def __init__(self, tokens: List[Token], source: str):
        self.tokens = tokens
        self.pos = 0
        self.source = source

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, typ: str) -> Token:
        tok = self.peek()
        if tok.type != typ:
            line,col = pos_to_linecol(self.source, tok.pos)
            raise ParseError(f"Parse error at line {line} col {col}: expected {typ} but got {tok.type}({tok.value})")
        return self.advance()

    def parse(self):
        stmts = []
        while self.peek().type != "EOF":
            if self.peek().type == "SEMICOLON":
                self.advance(); continue
            stmts.append(self.parse_statement())
        return ("PROGRAM", stmts)

    def parse_statement(self):
        tok = self.peek()
        if tok.type == "COLON":
            self.advance(); self.expect("DOLLAR"); name = self.expect("IDENT").value
            if self.peek().type == "ASSIGN":
                self.advance(); expr = self.parse_expression(); self.expect("SEMICOLON"); return ("DECL_ASSIGN", name, expr, tok.pos)
            self.expect("SEMICOLON") 
            return ("DECL", name, tok.pos)
        if tok.type == "QMARK" and self.tokens[self.pos+1].type == "DOLLAR":
            self.advance(); self.expect("DOLLAR"); name = self.expect("IDENT").value; self.expect("SEMICOLON"); return ("INPUT", name, tok.pos)
        if tok.type == "DOLLAR":
            if self.tokens[self.pos+1].type != "IDENT":
                line,col = pos_to_linecol(self.source, tok.pos); raise ParseError(f"Parse error at line {line} col {col}: expected identifier after $")
            if self.tokens[self.pos+2].type == "ASSIGN":
                self.advance(); name = self.expect("IDENT").value; self.expect("ASSIGN"); expr = self.parse_expression(); self.expect("SEMICOLON"); return ("ASSIGN", name, expr, tok.pos)
            elif self.tokens[self.pos+2].type == "SEMICOLON":
                self.advance(); name = self.expect("IDENT").value; self.expect("SEMICOLON"); return ("EXPR", ("VAR", name, tok.pos), tok.pos)
            else:
                self.advance(); name = self.expect("IDENT").value; self.expect("ASSIGN"); expr = self.parse_expression(); self.expect("SEMICOLON"); return ("ASSIGN", name, expr, tok.pos)
        if tok.type == "PRINT":
            self.advance(); expr = self.parse_expression(); self.expect("SEMICOLON"); return ("PRINT", expr, tok.pos)
        if tok.type == "IF":
            start_pos = tok.pos; self.advance(); self.expect("LPAREN"); cond = self.parse_expression(); self.expect("RPAREN"); self.expect("LBRACE")
            then_stmts = []
            while self.peek().type != "RBRACE":
                then_stmts.append(self.parse_statement())
            self.expect("RBRACE")
            else_stmts = []
            if self.peek().type == "COMMA":
                self.advance(); self.expect("LBRACE")
                while self.peek().type != "RBRACE":
                    else_stmts.append(self.parse_statement())
                self.expect("RBRACE")
            self.expect("SEMICOLON")
            return ("IF", cond, then_stmts, else_stmts, start_pos)
        if tok.type == "MULT" and self.tokens[self.pos+1].type == "LPAREN":
            start_pos = tok.pos; self.advance(); self.expect("LPAREN"); cond = self.parse_expression(); self.expect("RPAREN"); self.expect("LBRACE")
            body = []
            while self.peek().type != "RBRACE":
                body.append(self.parse_statement())
            self.expect("RBRACE"); self.expect("SEMICOLON"); return ("LOOP", cond, body, start_pos)
        if tok.type == "AT":
            self.advance(); name = self.expect("IDENT").value; self.expect("LPAREN")
            params = []
            if self.peek().type != "RPAREN":
                while True:
                    if self.peek().type == "DOLLAR": self.advance(); p = self.expect("IDENT").value
                    elif self.peek().type == "IDENT": p = self.advance().value
                    else:
                        line,col = pos_to_linecol(self.source, self.peek().pos)
                        raise ParseError(f"Parse error at line {line} col {col}: expected parameter name")
                    params.append(p)
                    if self.peek().type == "COMMA": self.advance(); continue
                    break
            self.expect("RPAREN"); self.expect("LBRACE")
            body = []
            while self.peek().type != "RBRACE":
                body.append(self.parse_statement())
            self.expect("RBRACE"); self.expect("SEMICOLON")
            return ("FUNC_DECL", name, params, body, tok.pos)
        expr = self.parse_expression()
        self.expect("SEMICOLON")
        return ("EXPR", expr, tok.pos)

    def parse_expression(self, min_prec=1):
        tok = self.peek()
        if tok.type == "NUMBER":
            self.advance(); left = ("NUMBER", float(tok.value) if "." in tok.value else int(tok.value), tok.pos)
        elif tok.type == "STRING":
            self.advance(); left = ("STRING", tok.value, tok.pos)
        elif tok.type == "DOLLAR":
            self.advance()
            if self.peek().type == "DOT":
                self.advance(); name = self.expect("IDENT").value; left = ("DYNVAR", name, tok.pos)
            else:
                name = self.expect("IDENT").value; left = ("VAR", name, tok.pos)
        elif tok.type == "LPAREN":
            self.advance(); left = self.parse_expression(); self.expect("RPAREN")
        elif tok.type == "MINUS":
            self.advance(); operand = self.parse_expression(self.PRECEDENCE["UNARY"]); left = ("UNARY", "NEG", operand, tok.pos)
        elif tok.type == "NOT":
            self.advance(); operand = self.parse_expression(self.PRECEDENCE["UNARY"]); left = ("UNARY", "NOT", operand, tok.pos)
        elif tok.type == "AT":
            self.advance(); name = self.expect("IDENT").value; self.expect("LPAREN")
            args = []
            if self.peek().type != "RPAREN":
                while True:
                    args.append(self.parse_expression())
                    if self.peek().type == "COMMA": self.advance(); continue
                    break
            self.expect("RPAREN")
            left = ("CALL", name, args, tok.pos)
        elif tok.type == "IDENT":
            self.advance(); left = ("VAR", tok.value, tok.pos)
        else:
            line,col = pos_to_linecol(self.source, tok.pos)
            raise ParseError(f"Unexpected token in expression at line {line} col {col}: {tok.type}({tok.value})")

        while True:
            tok = self.peek()
            if tok.type in ("OR","AND","EQ","NE","LT","GT","LE","GE","PLUS","MINUS","MULT","DIV","MOD"):
                prec = self._prec_for(tok.type)
                if prec < min_prec:
                    break
                op = tok.type; self.advance()
                right = self.parse_expression(prec+1)
                left = ("BINARY", op, left, right, tok.pos)
            else:
                break
        return left

    def _prec_for(self, toktype: str) -> int:
        if toktype == "OR": return self.PRECEDENCE["OR"]
        if toktype == "AND": return self.PRECEDENCE["AND"]
        if toktype in ("EQ","NE","LT","GT","LE","GE"): return self.PRECEDENCE["CMP"]
        if toktype in ("PLUS","MINUS"): return self.PRECEDENCE["PLUS"]
        if toktype in ("MULT","DIV","MOD"): return self.PRECEDENCE["MULT"]
        return 0

class RuntimeErrorWithPos(Exception):
    pass

class Function:
    def __init__(self, name: str, params: List[str], body: List[Any]):
        self.name = name; self.params = params; self.body = body

class Interpreter:
    def __init__(self, source: str, input_values: Optional[List[str]] = None, real_input: bool = False):
        self.source = source
        self.vars: Dict[str, Any] = {}
        self.dynamic_exprs: Dict[str, Any] = {}
        self.dependents: Dict[str, set] = {}
        self.funcs: Dict[str, Function] = {}
        self.input_values = input_values or []
        self.real_input = real_input
        self.input_pos = 0

    def eval_program(self, ast):
        _, stmts = ast
        for s in stmts:
            self.exec_stmt(s)

    def exec_stmt(self, stmt):
        kind = stmt[0]
        if kind == "DECL":
            _, name, pos = stmt
            if name in self.vars:
                self._runtime_error(pos, f"Variable {name} already declared")
            self.vars[name] = None
        elif kind == "DECL_ASSIGN":
            _, name, expr, pos = stmt
            dyn_deps = self._collect_dyn_vars(expr)
            if dyn_deps:
                dyn_expr = self._snapshot_expr(expr)
                self._register_dynamic(name, dyn_expr)
            else:
                val = self.eval_expr(expr)
                if name in self.vars:
                    self._runtime_error(pos, f"Variable {name} already declared")
                self.vars[name] = val
        elif kind == "ASSIGN":
            _, name, expr, pos = stmt
            val = self.eval_expr(expr)
            self._unregister_dynamic(name)
            if name not in self.vars:
                self.vars[name] = None
            self.vars[name] = val
            self._propagate_change(name, set())
        elif kind == "PRINT":
            _, expr, pos = stmt
            val = self.eval_expr(expr)
            print(self._repr(val))
        elif kind == "IF":
            _, cond, then_stmts, else_stmts, pos = stmt
            c = self.eval_expr(cond)
            if self._is_true(c):
                for ts in then_stmts: self.exec_stmt(ts)
            else:
                for es in else_stmts: self.exec_stmt(es)
        elif kind == "INPUT":
            _, name, pos = stmt
            val = self._get_input()
            self._unregister_dynamic(name)
            if name not in self.vars:
                self.vars[name] = None
            self.vars[name] = val
            self._propagate_change(name, set())
        elif kind == "LOOP":
            _, cond, body, pos = stmt
            while self._is_true(self.eval_expr(cond)):
                for b in body: self.exec_stmt(b)
        elif kind == "FUNC_DECL":
            _, name, params, body, pos = stmt
            if name in self.funcs:
                self._runtime_error(pos, f"Function {name} already declared")
            self.funcs[name] = Function(name, params, body)
        elif kind == "EXPR":
            _, expr, pos = stmt
            self.eval_expr(expr)
        else:
            self._runtime_error(None, f"Unknown statement kind: {kind}")

    def eval_expr(self, node):
        t = node[0]
        if t == "NUMBER": return node[1]
        if t == "STRING": return node[1]
        if t == "VAR":
            name = node[1]; pos = node[2] if len(node) > 2 else None
            if name not in self.vars:
                self._runtime_error(pos, f"Undeclared variable {name}")
            return self.vars[name]
        if t == "DYNVAR":
            name = node[1]
            pos = node[2] if len(node) > 2 else None
            if name not in self.vars:
                self._runtime_error(pos, f"Undeclared variable {name}")
            return self.vars[name]
        if t == "UNARY":
            _, op, operand, pos = node
            val = self.eval_expr(operand)
            if op == "NEG":
                if not isinstance(val, (int, float)): self._runtime_error(pos, "Unary - applied to non-number")
                return -val
            if op == "NOT":
                return not self._is_true(val)
            self._runtime_error(pos, f"Unknown unary op {op}")
        if t == "BINARY":
            _, op, left, right, pos = node
            L = self.eval_expr(left); R = self.eval_expr(right)
            if op in ("PLUS","MINUS","MULT","DIV","MOD"):
                if isinstance(L,(int,float)) and isinstance(R,(int,float)):
                    if op=="PLUS": return L+R
                    if op=="MINUS": return L-R
                    if op=="MULT": return L*R
                    if op=="DIV":
                        if R==0: self._runtime_error(pos, "Division by zero")
                        return L/R
                    if op=="MOD": return L%R
                if op=="PLUS" and (isinstance(L,str) or isinstance(R,str)):
                    return str(L)+str(R)
                self._runtime_error(pos, "Type error in arithmetic")
            if op in ("EQ","NE","LT","GT","LE","GE"):
                if op=="EQ": return L==R
                if op=="NE": return L!=R
                if op=="LT": return L<R
                if op=="GT": return L>R
                if op=="LE": return L<=R
                if op=="GE": return L>=R
            if op == "AND": return self._is_true(L) and self._is_true(R)
            if op == "OR": return self._is_true(L) or self._is_true(R)
            self._runtime_error(pos, f"Unknown binary op {op}")
        if t == "CALL":
            _, name, args, pos = node
            if name not in self.funcs:
                self._runtime_error(pos, f"Call to undeclared function {name}")
            func = self.funcs[name]
            if len(args) != len(func.params):
                self._runtime_error(pos, f"Function {name} expected {len(func.params)} args but got {len(args)}")
            saved_vars = self.vars.copy()
            for i,p in enumerate(func.params):
                self.vars[p] = self.eval_expr(args[i])
            ret = None
            for s in func.body:
                if s[0] == "DECL":
                    _, nm, _ = s; self.vars[nm] = None
                if s[0] == "EXPR":
                    ret = self.eval_expr(s[1])
                else:
                    self.exec_stmt(s)
            self.vars = saved_vars
            return ret
        self._runtime_error(None, f"Unknown expr node {node}")

    def _is_true(self, v):
        if v is None: return False
        if isinstance(v, bool): return v
        if isinstance(v, (int, float)): return v != 0
        if isinstance(v, str): return len(v) > 0
        return bool(v)

    def _get_input(self):
        if self.real_input:
            s = input(); return self._auto_cast(s)
        if self.input_pos < len(self.input_values):
            s = self.input_values[self.input_pos]; self.input_pos += 1; return self._auto_cast(s)
        self._runtime_error(None, "No more input values provided")

    def _auto_cast(self, s: str):
        if s is None: return None
        if isinstance(s, (int, float, bool)): return s
        if isinstance(s, str) and s.lower() in ("true","false"): return s.lower()=="true"
        try:
            if isinstance(s, str) and "." in s: return float(s)
            if isinstance(s, str): return int(s)
        except Exception:
            return s

    def _repr(self, v):
        if v is None: return "null"
        if isinstance(v, bool): return "true" if v else "false"
        return str(v)

    def _runtime_error(self, pos: Optional[int], msg: str):
        if pos is not None:
            line,col = pos_to_linecol(self.source, pos)
            raise RuntimeErrorWithPos(f"Runtime error at line {line} col {col}: {msg}")
        else:
            raise RuntimeErrorWithPos(f"Runtime error: {msg}")
    
    def _collect_dyn_vars(self, node) -> set:
        t = node[0]
        if t == "DYNVAR":
            return {node[1]}
        if t in ("NUMBER", "STRING"):
            return set()
        if t == "VAR":
            return set()
        if t == "UNARY":
            return self._collect_dyn_vars(node[2])
        if t == "BINARY":
            return self._collect_dyn_vars(node[2]) | self._collect_dyn_vars(node[3])
        if t == "CALL":
            s = set()
            for a in node[2]:
                s |= self._collect_dyn_vars(a)
            return s
        return set()

    def _snapshot_expr(self, node):
        t = node[0]
        if t == "NUMBER" or t == "STRING":
            return node
        if t == "VAR":
            name = node[1]
            if name not in self.vars:
                self._runtime_error(node[2] if len(node)>2 else None, f"Undeclared variable {name} used in declaration snapshot")
            val = self.vars[name]
            if isinstance(val, (int, float)):
                return ("NUMBER", val, node[2] if len(node)>2 else None)
            if isinstance(val, str):
                return ("STRING", val, node[2] if len(node)>2 else None)
            if isinstance(val, bool):
                return ("NUMBER", 1 if val else 0, node[2] if len(node)>2 else None)
            if val is None:
                return ("NUMBER", 0, node[2] if len(node)>2 else None)
            return ("STRING", str(val), node[2] if len(node)>2 else None)
        if t == "DYNVAR":
            return node
        if t == "UNARY":
            op = node[1]; operand = self._snapshot_expr(node[2]); return ("UNARY", op, operand, node[3] if len(node)>3 else None)
        if t == "BINARY":
            op = node[1]; L = self._snapshot_expr(node[2]); R = self._snapshot_expr(node[3]); return ("BINARY", op, L, R, node[4] if len(node)>4 else None)
        if t == "CALL":
            name = node[1]; args = [self._snapshot_expr(a) for a in node[2]]; return ("CALL", name, args, node[3] if len(node)>3 else None)
        return node

    def _register_dynamic(self, name: str, dyn_expr):
        self._unregister_dynamic(name)
        deps = self._collect_dyn_vars(dyn_expr)
        self.dynamic_exprs[name] = dyn_expr
        for d in deps:
            self.dependents.setdefault(d, set()).add(name)
        self.vars[name] = self.eval_expr(dyn_expr)

    def _unregister_dynamic(self, name: str):
        if name in self.dynamic_exprs:
            old_deps = self._collect_dyn_vars(self.dynamic_exprs[name])
            for d in old_deps:
                self.dependents.get(d, set()).discard(name)
            del self.dynamic_exprs[name]

    def _propagate_change(self, varname: str, visiting: set):
        if varname in visiting:
            self._runtime_error(None, f"Cycle detected in dynamic dependencies involving {varname}")
        visiting.add(varname)
        for dep in list(self.dependents.get(varname, [])):
            if dep not in self.dynamic_exprs:
                continue
            new_val = self.eval_expr(self.dynamic_exprs[dep])
            old_val = self.vars.get(dep)
            if new_val != old_val:
                self.vars[dep] = new_val
                self._propagate_change(dep, visiting)
        visiting.remove(varname)

def run_genlang(source: str, input_values: Optional[List[str]] = None, real_input: bool = False):
    tokens = lex(source)
    parser = Parser(tokens, source)
    ast = parser.parse()
    interp = Interpreter(source, input_values=input_values, real_input=real_input)
    interp.eval_program(ast)
    return interp