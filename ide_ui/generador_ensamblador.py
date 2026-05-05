"""
Generador de código ensamblador pseudo-x86 (Intel syntax).
Convierte TAC a instrucciones de ensamblador.
"""

import re


class GeneradorEnsamblador:
    def __init__(self):
        self.asm = []
        self.data_section = []
        self.vars_declaradas = set()

    def _es_numero(self, s):
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False

    def _operand(self, val):
        """Return asm operand: immediate or memory ref."""
        if self._es_numero(val):
            return val
        return f"[{val}]"

    def emit(self, instr):
        self.asm.append(instr)

    def generar(self, tac_lista):
        self.asm = []
        self.data_section = []
        self.vars_declaradas = set()

        self.emit("section .data")
        data_placeholder = len(self.asm)  # Insert data lines here later

        self.emit("")
        self.emit("section .text")
        self.emit("global main")
        self.emit("")

        for instr in tac_lista:
            self._convertir(instr)

        # Insert data declarations after "section .data"
        data_lines = self.data_section[:]
        final = (self.asm[:data_placeholder] +
                 data_lines +
                 self.asm[data_placeholder:])
        self.asm = final
        return self.asm

    def _convertir(self, instr):
        instr = instr.strip()

        # Label: L1:
        if re.match(r'^L\d+:$', instr):
            self.emit(f"{instr}")
            return

        # BEGIN main
        if instr == "BEGIN main":
            self.emit("main:")
            self.emit("    push rbp")
            self.emit("    mov rbp, rsp")
            return

        # DECL type var
        m = re.match(r'^DECL (\w+) (\w+)$', instr)
        if m:
            tipo, var = m.group(1), m.group(2)
            if var not in self.vars_declaradas:
                self.vars_declaradas.add(var)
                directive = "dq 0" if tipo == "double" else "dd 0"
                self.data_section.append(f"    {var} {directive}")
            return

        # DECL_ARR type var size
        m = re.match(r'^DECL_ARR (\w+) (\w+) (\d+)$', instr)
        if m:
            tipo, var, size = m.group(1), m.group(2), int(m.group(3))
            if var not in self.vars_declaradas:
                self.vars_declaradas.add(var)
                directive = "dq" if tipo == "double" else "dd"
                self.data_section.append(f"    {var} times {size} {directive} 0")
            return

        # t1 = arr[idx]
        m = re.match(r'^(\w+) = (\w+)\[(\w+)\]$', instr)
        if m:
            dest, arr, idx = m.group(1), m.group(2), m.group(3)
            if idx.isdigit():
                self.emit(f"    mov eax, [{arr} + {idx}*4]")
            else:
                self.emit(f"    mov ecx, [{idx}]")
                self.emit(f"    mov eax, [{arr} + ecx*4]")
            self._ensure_var(dest)
            self.emit(f"    mov [{dest}], eax")
            return

        # arr[idx] = val
        m = re.match(r'^(\w+)\[(\w+)\] = (.+)$', instr)
        if m:
            arr, idx, val = m.group(1), m.group(2), m.group(3)
            self.emit(f"    mov eax, {self._operand(val)}")
            if idx.isdigit():
                self.emit(f"    mov [{arr} + {idx}*4], eax")
            else:
                self.emit(f"    mov ecx, [{idx}]")
                self.emit(f"    mov [{arr} + ecx*4], eax")
            return

        # result = left OP right
        m = re.match(r'^(\w+) = (\S+) ([+\-*/]) (\S+)$', instr)
        if m:
            dest, left, op, right = m.group(1), m.group(2), m.group(3), m.group(4)
            self._ensure_var(dest)
            self.emit(f"    mov eax, {self._operand(left)}")
            if op == '+':
                self.emit(f"    add eax, {self._operand(right)}")
            elif op == '-':
                self.emit(f"    sub eax, {self._operand(right)}")
            elif op == '*':
                self.emit(f"    imul eax, {self._operand(right)}")
            elif op == '/':
                self.emit(f"    cdq")
                self.emit(f"    mov ecx, {self._operand(right)}")
                self.emit(f"    idiv ecx")
            self.emit(f"    mov [{dest}], eax")
            return

        # result = left CMP right  (comparison)
        m = re.match(r'^(\w+) = (\S+) (<=|>=|==|!=|<|>) (\S+)$', instr)
        if m:
            dest, left, op, right = m.group(1), m.group(2), m.group(3), m.group(4)
            self._ensure_var(dest)
            jump_map = {'<': 'setl', '>': 'setg', '<=': 'setle',
                        '>=': 'setge', '==': 'sete', '!=': 'setne'}
            self.emit(f"    mov eax, {self._operand(left)}")
            self.emit(f"    cmp eax, {self._operand(right)}")
            self.emit(f"    {jump_map[op]} al")
            self.emit(f"    movzx eax, al")
            self.emit(f"    mov [{dest}], eax")
            return

        # var = val  (simple assignment)
        m = re.match(r'^(\w+) = (\S+)$', instr)
        if m:
            dest, val = m.group(1), m.group(2)
            self._ensure_var(dest)
            self.emit(f"    mov eax, {self._operand(val)}")
            self.emit(f"    mov [{dest}], eax")
            return

        # var++ / var--
        m = re.match(r'^(\w+)(\+\+|--)$', instr)
        if m:
            var, op = m.group(1), m.group(2)
            asm_op = "inc" if op == '++' else "dec"
            self.emit(f"    {asm_op} dword [{var}]")
            return

        # IF_FALSE cond GOTO label
        m = re.match(r'^IF_FALSE (\w+) GOTO (L\d+)$', instr)
        if m:
            cond, label = m.group(1), m.group(2)
            self.emit(f"    mov eax, [{cond}]")
            self.emit(f"    cmp eax, 0")
            self.emit(f"    je {label}")
            return

        # IF_TRUE cond GOTO label
        m = re.match(r'^IF_TRUE (\w+) GOTO (L\d+)$', instr)
        if m:
            cond, label = m.group(1), m.group(2)
            self.emit(f"    mov eax, [{cond}]")
            self.emit(f"    cmp eax, 0")
            self.emit(f"    jne {label}")
            return

        # GOTO label
        m = re.match(r'^GOTO (L\d+)$', instr)
        if m:
            self.emit(f"    jmp {m.group(1)}")
            return

        # PRINT val
        m = re.match(r'^PRINT (.+)$', instr)
        if m:
            val = m.group(1).strip()
            self.emit(f"    ; PRINT {val}")
            return

        # READ var
        m = re.match(r'^READ (\w+)$', instr)
        if m:
            self.emit(f"    ; READ {m.group(1)}")
            return

        # RETURN val
        m = re.match(r'^RETURN (.*)$', instr)
        if m:
            val = m.group(1).strip()
            if val and self._es_numero(val):
                self.emit(f"    mov eax, {val}")
            elif val:
                self.emit(f"    mov eax, [{val}]")
            else:
                self.emit(f"    xor eax, eax")
            self.emit(f"    pop rbp")
            self.emit(f"    ret")
            return

        # SWITCH / CASE / DEFAULT — comments in asm
        if instr.startswith(('SWITCH', 'CASE', 'DEFAULT')):
            self.emit(f"    ; {instr}")
            return

    def _ensure_var(self, var):
        if var not in self.vars_declaradas:
            self.vars_declaradas.add(var)
            self.data_section.append(f"    {var} dd 0")

    def formato_texto(self):
        return '\n'.join(self.asm)
