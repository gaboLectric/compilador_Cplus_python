"""
Generador de Código Intermedio (TAC - Three-Address Code).
Procesa el código fuente línea por línea y emite instrucciones TAC.
"""

import re
from ide_ui.token_cpp import TokenCpp


class GeneradorCodigoIntermedio:
    def __init__(self, compilador):
        self.compilador = compilador  # CompiladorCpp instance (already ran declaraciones)
        self.tac = []          # List of TAC instruction strings
        self._temp_count = 0
        self._label_count = 0
        self._do_stack = []    # Stack of do-while labels

    def nuevo_temp(self):
        self._temp_count += 1
        return f"t{self._temp_count}"

    def nueva_etiqueta(self):
        self._label_count += 1
        return f"L{self._label_count}"

    def emit(self, instruccion):
        self.tac.append(instruccion)

    def generar(self, codigo):
        self.tac = []
        self._temp_count = 0
        self._label_count = 0
        self._do_stack = []

        lineas = codigo.split('\n')
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()
            i += 1
            if not linea or linea.startswith('//') or linea.startswith('/*'):
                continue

            tokens = [t for t in self.compilador.tokenizar(linea)
                      if t.tipo not in ('Espacio', 'Comentario')]
            if not tokens:
                continue

            self._procesar_linea(tokens, linea)

        return self.tac

    def _procesar_linea(self, tokens, linea_orig):
        if not tokens:
            return

        primer = tokens[0]

        # Function declaration: int main() { or void printArray(...) {
        if primer.tipo == 'TipoDato' and len(tokens) >= 5 and tokens[2].tipo == 'ParenAbre':
            nombre = tokens[1].valor
            self.emit(f"BEGIN {nombre}")
            return

        # Cierre de bloque }
        if primer.tipo == 'LlaveCierra' and len(tokens) == 1:
            if self._do_stack:
                frame = self._do_stack[-1]
                if isinstance(frame, tuple) and len(frame) == 3 and frame[0] not in ('if', 'else', 'switch'):
                    # for loop: emit increment then GOTO
                    inicio, fin, inc_code = frame
                    self._do_stack.pop()
                    if inc_code:
                        self.emit(inc_code)
                    self.emit(f"GOTO {inicio}")
                    self.emit(f"{fin}:")
                elif isinstance(frame, tuple) and frame[0] in ('if', 'else'):
                    _, fin = frame
                    self._do_stack.pop()
                    self.emit(f"{fin}:")
                elif isinstance(frame, tuple) and frame[0] == 'switch':
                    _, var, fin = frame
                    self._do_stack.pop()
                    self.emit(f"{fin}:")
                elif isinstance(frame, tuple) and len(frame) == 2 and frame[0] not in ('if', 'else', 'switch'):
                    # while loop
                    inicio, fin = frame
                    self._do_stack.pop()
                    self.emit(f"GOTO {inicio}")
                    self.emit(f"{fin}:")
            return

        # } while(cond); — do-while end
        if primer.tipo == 'LlaveCierra' and len(tokens) >= 4 and tokens[1].valor == 'while':
            if self._do_stack:
                inicio, fin = self._do_stack.pop()
                # Extract condition tokens: between ( and )
                cond_tokens = []
                in_paren = False
                for t in tokens[2:]:
                    if t.tipo == 'ParenAbre':
                        in_paren = True
                        continue
                    if t.tipo == 'ParenCierra':
                        break
                    if in_paren:
                        cond_tokens.append(t)
                cond_temp = self._gen_condicion(cond_tokens)
                self.emit(f"IF_TRUE {cond_temp} GOTO {inicio}")
                self.emit(f"{fin}:")
            return

        # Array declaration: int arr[N];
        if (primer.tipo == 'TipoDato' and len(tokens) == 6 and
                tokens[2].tipo == 'CorcheteAbre'):
            tipo = primer.valor
            nombre = tokens[1].valor
            tamano = tokens[3].valor
            self.emit(f"DECL_ARR {tipo} {nombre} {tamano}")
            return

        # Array declaration with init: int arr[] = { ... };
        if (primer.tipo == 'TipoDato' and len(tokens) >= 7 and
                tokens[2].tipo == 'CorcheteAbre' and tokens[3].tipo == 'CorcheteCierra' and
                tokens[4].tipo == 'Asignacion' and tokens[5].tipo == 'LlaveAbre'):
            tipo = primer.valor
            nombre = tokens[1].valor
            elementos = [t for t in tokens[6:-2] if t.tipo in ('Numero', 'Variable')]
            tamano = len(elementos)
            self.emit(f"DECL_ARR {tipo} {nombre} {tamano}")
            for idx, el in enumerate(elementos):
                self.emit(f"{nombre}[{idx}] = {el.valor}")
            return

        # Variable declaration: int x;
        if (primer.tipo == 'TipoDato' and len(tokens) == 3 and
                tokens[1].tipo == 'Variable' and tokens[2].tipo == 'PuntoComa'):
            self.emit(f"DECL {primer.valor} {tokens[1].valor}")
            return

        # Variable declaration with assignment: int x = expr;
        if (primer.tipo == 'TipoDato' and len(tokens) >= 5 and
                tokens[1].tipo == 'Variable' and tokens[2].tipo == 'Asignacion' and tokens[-1].tipo == 'PuntoComa'):
            self.emit(f"DECL {primer.valor} {tokens[1].valor}")
            expr_tokens = tokens[3:-1]
            result = self._gen_expr(expr_tokens)
            self.emit(f"{tokens[1].valor} = {result}")
            return

        # Assignment: x = expr;  or  arr[i] = expr;
        if primer.tipo == 'Variable' and len(tokens) >= 4 and tokens[-1].tipo == 'PuntoComa':
            # arr[i] = expr;
            if tokens[1].tipo == 'CorcheteAbre':
                idx_tokens = []
                j = 2
                while j < len(tokens) and tokens[j].tipo != 'CorcheteCierra':
                    idx_tokens.append(tokens[j])
                    j += 1
                j += 2  # skip ] =
                expr_tokens = tokens[j:-1]
                idx = self._gen_expr(idx_tokens)
                val = self._gen_expr(expr_tokens)
                self.emit(f"{primer.valor}[{idx}] = {val}")
                return
            # x = expr;
            if tokens[1].tipo == 'Asignacion':
                expr_tokens = tokens[2:-1]
                result = self._gen_expr(expr_tokens)
                if result != primer.valor:
                    self.emit(f"{primer.valor} = {result}")
                return

        # Increment: x++;  ++x;
        if len(tokens) >= 2 and tokens[-1].tipo == 'PuntoComa':
            if tokens[0].tipo == 'Variable' and tokens[1].tipo == 'Incremento':
                op = '++' if tokens[1].valor == '++' else '--'
                self.emit(f"{tokens[0].valor}{op}")
                return
            if tokens[0].tipo == 'Incremento' and tokens[1].tipo == 'Variable':
                op = '++' if tokens[0].valor == '++' else '--'
                self.emit(f"{tokens[1].valor}{op}")
                return

        # cout << expr;
        if primer.valor == 'cout' and len(tokens) >= 4:
            expr_tokens = tokens[2:-1]
            val = self._gen_expr(expr_tokens)
            self.emit(f"PRINT {val}")
            return

        # cin >> variable;
        if primer.valor == 'cin' and len(tokens) >= 4:
            self.emit(f"READ {tokens[2].valor}")
            return

        # Function call: func(arg1, arg2);
        if primer.tipo == 'Variable' and len(tokens) >= 4 and tokens[1].tipo == 'ParenAbre' and tokens[-2].tipo == 'ParenCierra' and tokens[-1].tipo == 'PuntoComa':
            nombre = primer.valor
            args_tokens = tokens[2:-2]
            args = []
            for t in args_tokens:
                if t.tipo in ('Variable', 'Numero', 'Caracter', 'Cadena'):
                    args.append(t.valor)
            for arg in args:
                self.emit(f"PARAM {arg}")
            self.emit(f"CALL {nombre}")
            return

        # return expr;
        if primer.valor == 'return':
            expr_tokens = tokens[1:-1]
            val = self._gen_expr(expr_tokens) if expr_tokens else ''
            self.emit(f"RETURN {val}")
            return

        # while (cond) {
        if primer.valor == 'while' and len(tokens) >= 2 and tokens[1].tipo == 'ParenAbre':
            inicio = self.nueva_etiqueta()
            fin = self.nueva_etiqueta()
            self.emit(f"{inicio}:")
            cond_tokens = self._extraer_paren(tokens)
            cond_temp = self._gen_condicion(cond_tokens)
            self.emit(f"IF_FALSE {cond_temp} GOTO {fin}")
            self._do_stack.append((inicio, fin))
            return

        # do {
        if primer.valor == 'do' and tokens[-1].tipo == 'LlaveAbre':
            inicio = self.nueva_etiqueta()
            fin = self.nueva_etiqueta()
            self.emit(f"{inicio}:")
            self._do_stack.append((inicio, fin))
            return

        # for (int i=0; i<N; i++) {
        if primer.valor == 'for' and len(tokens) >= 2 and tokens[1].tipo == 'ParenAbre':
            interior = self._extraer_paren(tokens)
            condiciones = self._split_semicolons(interior)
            if len(condiciones) == 3:
                cond1, cond2, cond3 = condiciones
                # Init
                if len(cond1) >= 4:
                    tipo = cond1[0].valor
                    var = cond1[1].valor
                    val = cond1[3].valor
                    self.emit(f"DECL {tipo} {var}")
                    self.emit(f"{var} = {val}")
                inicio = self.nueva_etiqueta()
                fin = self.nueva_etiqueta()
                self.emit(f"{inicio}:")
                cond_temp = self._gen_condicion(cond2)
                self.emit(f"IF_FALSE {cond_temp} GOTO {fin}")
                inc_code = self._gen_incremento(cond3)
                self._do_stack.append((inicio, fin, inc_code))
            return

        # if (cond) {
        if primer.valor == 'if' and len(tokens) >= 2 and tokens[1].tipo == 'ParenAbre':
            fin = self.nueva_etiqueta()
            cond_tokens = self._extraer_paren(tokens)
            cond_temp = self._gen_condicion(cond_tokens)
            self.emit(f"IF_FALSE {cond_temp} GOTO {fin}")
            self._do_stack.append(('if', fin))
            return

        # else {  or  } else {
        if any(t.valor == 'else' for t in tokens):
            if self._do_stack and self._do_stack[-1][0] == 'if':
                _, fin = self._do_stack.pop()
                skip = self.nueva_etiqueta()
                self.emit(f"GOTO {skip}")
                self.emit(f"{fin}:")
                self._do_stack.append(('else', skip))
            return

        # switch (var) {
        if primer.valor == 'switch' and len(tokens) >= 2 and tokens[1].tipo == 'ParenAbre':
            var_token = tokens[2]
            fin = self.nueva_etiqueta()
            self.emit(f"SWITCH {var_token.valor}")
            self._do_stack.append(('switch', var_token.valor, fin))
            return

        # case N:
        if primer.valor == 'case' and len(tokens) >= 3:
            case_val = tokens[1].valor
            label = self.nueva_etiqueta()
            if self._do_stack and self._do_stack[-1][0] == 'switch':
                var = self._do_stack[-1][1]
                self.emit(f"CASE {var} == {case_val} GOTO {label}")
                self.emit(f"{label}:")
            return

        # default:
        if primer.valor == 'default':
            label = self.nueva_etiqueta()
            self.emit(f"DEFAULT GOTO {label}")
            self.emit(f"{label}:")
            return

        # break;
        if primer.valor == 'break':
            for frame in reversed(self._do_stack):
                if isinstance(frame, tuple) and frame[0] in ('switch',):
                    self.emit(f"GOTO {frame[-1]}")
                    break
                elif isinstance(frame, tuple) and len(frame) >= 2 and frame[0] not in ('if', 'else', 'switch'):
                    self.emit(f"GOTO {frame[1]}")
                    break
            return

    # ─── HELPERS ───

    def _extraer_paren(self, tokens):
        """Return tokens between first ( and matching )."""
        resultado = []
        nivel = 0
        inside = False
        for t in tokens:
            if t.tipo == 'ParenAbre':
                if inside:
                    resultado.append(t)
                nivel += 1
                inside = True
            elif t.tipo == 'ParenCierra':
                nivel -= 1
                if nivel == 0:
                    break
                resultado.append(t)
            elif inside:
                resultado.append(t)
        return resultado

    def _split_semicolons(self, tokens):
        """Split token list on PuntoComa — returns list of lists."""
        grupos = []
        actual = []
        for t in tokens:
            if t.tipo == 'PuntoComa':
                grupos.append(actual)
                actual = []
            else:
                actual.append(t)
        grupos.append(actual)
        return grupos

    def _gen_expr(self, tokens):
        """Generate TAC for an expression; return the result variable/temp."""
        if not tokens:
            return ''
        if len(tokens) == 1:
            return tokens[0].valor
            
        # sizeof
        if tokens[0].valor == 'sizeof' and tokens[1].tipo == 'ParenAbre':
            if tokens[2].tipo == 'Variable' and tokens[3].tipo == 'ParenCierra':
                var = tokens[2].valor
                if self.compilador.tabla_simbolos.existe(var):
                    info = self.compilador.tabla_simbolos.obtener(var)
                    m = re.search(r'\[(\d+)\]', info['tipo'])
                    if m:
                        return str(int(m.group(1)) * 4)
            return "4"
            
        # Array access: var [ idx ]
        if (len(tokens) >= 4 and tokens[0].tipo == 'Variable' and
                tokens[1].tipo == 'CorcheteAbre'):
            arr = tokens[0].valor
            idx_tokens = tokens[2:-1]
            idx = self._gen_expr(idx_tokens)
            temp = self.nuevo_temp()
            self.emit(f"{temp} = {arr}[{idx}]")
            return temp
        # Binary expression — find lowest-precedence operator
        for target in (('Suma', 'Resta'), ('Multiplicar', 'Dividir')):
            nivel_paren = 0
            for j in range(len(tokens) - 1, -1, -1):
                t = tokens[j]
                if t.tipo == 'ParenCierra':
                    nivel_paren += 1
                elif t.tipo == 'ParenAbre':
                    nivel_paren -= 1
                elif nivel_paren == 0 and t.tipo in target:
                    left = self._gen_expr(tokens[:j])
                    right = self._gen_expr(tokens[j + 1:])
                    temp = self.nuevo_temp()
                    self.emit(f"{temp} = {left} {t.valor} {right}")
                    return temp
        # Parenthesized
        if tokens[0].tipo == 'ParenAbre' and tokens[-1].tipo == 'ParenCierra':
            return self._gen_expr(tokens[1:-1])
        # Fallback
        return ' '.join(t.valor for t in tokens)

    def _gen_condicion(self, tokens):
        """Generate TAC for a boolean condition; return temp holding 0/1."""
        if not tokens:
            return 'true'
        for j, t in enumerate(tokens):
            if t.tipo == 'Comparacion':
                left = self._gen_expr(tokens[:j])
                right = self._gen_expr(tokens[j + 1:])
                temp = self.nuevo_temp()
                self.emit(f"{temp} = {left} {t.valor} {right}")
                return temp
        return self._gen_expr(tokens)

    def _gen_incremento(self, tokens):
        """Return TAC string for increment like i++ or ++i."""
        if not tokens:
            return ''
        if tokens[0].tipo == 'Variable' and len(tokens) >= 2 and tokens[1].tipo == 'Incremento':
            op = '+' if tokens[1].valor == '++' else '-'
            return f"{tokens[0].valor} = {tokens[0].valor} {op} 1"
        if tokens[0].tipo == 'Incremento' and len(tokens) >= 2:
            op = '+' if tokens[0].valor == '++' else '-'
            return f"{tokens[1].valor} = {tokens[1].valor} {op} 1"
        return ''

    def formato_texto(self):
        """Return TAC as formatted string for display."""
        lineas = []
        for i, instr in enumerate(self.tac, 1):
            if instr.endswith(':'):
                lineas.append(f"  {instr}")
            else:
                lineas.append(f"    {i:3d}  {instr}")
        return '\n'.join(lineas)
