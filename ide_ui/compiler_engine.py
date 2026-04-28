"""
Motor del compilador C++ que envuelve las clases de cpp_compiler.py
para su uso en la interfaz.

Integra: Análisis léxico, declaraciones, tokens, árboles, tabla de símbolos.
"""

import sys
import os
import io

from ide_ui.analizador_lexico import CompiladorCpp
from ide_ui.parser_cpp import ParserCpp
from ide_ui.nodo_arbol import NodoArbol
from ide_ui.tabla_simbolos import TablaSimbolos
from ide_ui.generador_codigo_intermedio import GeneradorCodigoIntermedio
from ide_ui.generador_ensamblador import GeneradorEnsamblador


class CompilerEngine:
    """
    Motor del compilador C++ que integra todas las fases:
    1. Análisis léxico de declaraciones (con ;)
    2. Análisis léxico de expresiones (tokenización)
    3. Tabla de símbolos
    4. Validación de paréntesis y llaves
    5. Análisis sintáctico (árboles)
    """

    def __init__(self):
        self.compilador = CompiladorCpp()
        self.last_errors = []
        self.last_warnings = []

    def reset(self):
        self.compilador = CompiladorCpp()
        self.last_errors = []
        self.last_warnings = []

    # ═══════════════════════════════════════════════
    # FASE 1: ANÁLISIS DE DECLARACIONES C++
    # ═══════════════════════════════════════════════

    def analizar_declaraciones(self, codigo):
        self.compilador.reset()
        lineas = codigo.split('\n')

        resultados = []
        errores = []
        advertencias = []

        resultados.append("═══ ANÁLISIS DE DECLARACIONES C++ ═══")
        resultados.append("")

        for i, linea in enumerate(lineas, 1):
            tipo_patron, mensaje, es_valida = self.compilador.analizar_linea(linea, i)

            if mensaje is not None:
                resultados.append(f"  Línea {i:3d} │ {mensaje}")

                if es_valida is False:
                    errores.append(f"Línea {i}: {mensaje}")
                elif es_valida and tipo_patron == 'declaracion' and 'ambigüedad' in mensaje.lower():
                    advertencias.append(f"Línea {i}: {mensaje}")
                elif es_valida and tipo_patron == 'declaracion' and 'ya declarada' in mensaje.lower():
                    advertencias.append(f"Línea {i}: {mensaje}")

        resultados.append("")
        resultados.append("═══ TABLA DE SÍMBOLOS ═══")
        resultados.append("")
        resultados.append(str(self.compilador.tabla_simbolos))
        resultados.append("")

        if errores:
            resultados.append(f"  ⚠ {len(errores)} error(es) encontrado(s)")
        else:
            resultados.append("  ✓ Sin errores en declaraciones")

        if advertencias:
            resultados.append(f"  ⚠ {len(advertencias)} advertencia(s)")

        self.last_errors.extend(errores)
        self.last_warnings.extend(advertencias)

        return {
            'resultados': resultados,
            'variables': dict(self.compilador.tabla_simbolos.simbolos),
            'errores': errores,
            'ambiguedades': advertencias,
        }

    # ═══════════════════════════════════════════════
    # FASE 2: ANÁLISIS LÉXICO (TOKENS)
    # ═══════════════════════════════════════════════

    def analizar_expresiones(self, codigo):
        lineas = codigo.split('\n')
        resultados = []

        resultados.append("═══ ANÁLISIS LÉXICO (TOKENS) C++ ═══")
        resultados.append("")

        for i, linea in enumerate(lineas, 1):
            linea_limpia = linea.strip()
            if not linea_limpia or linea_limpia.startswith('//'):
                continue

            tokens = self.compilador.tokenizar(linea_limpia)
            if not tokens:
                continue

            resultados.append(f"  Línea {i}: {linea_limpia}")

            for token in tokens:
                tipo = token.tipo
                valor = token.valor

                if tipo == 'TipoDato':
                    resultados.append(f"    ├─ TipoDato:         {valor}")
                elif tipo == 'Variable':
                    resultados.append(f"    ├─ Variable:         {valor}")
                elif tipo == 'PalabraReservada':
                    resultados.append(f"    ├─ PalabraReservada: {valor}")
                elif tipo == 'Numero':
                    resultados.append(f"    ├─ Número:           {valor}")
                elif tipo == 'Cadena':
                    resultados.append(f"    ├─ Cadena:           {valor}")
                elif tipo == 'Caracter':
                    resultados.append(f"    ├─ Carácter:         {valor}")
                elif tipo == 'Booleano':
                    resultados.append(f"    ├─ Booleano:         {valor}")
                elif tipo in ('Suma', 'Resta', 'Multiplicar', 'Dividir'):
                    resultados.append(f"    ├─ Operador:         {valor}")
                elif tipo == 'Asignacion':
                    resultados.append(f"    ├─ Asignación:       {valor}")
                elif tipo == 'PuntoComa':
                    resultados.append(f"    ├─ PuntoComa:        {valor}")
                elif tipo == 'ParenAbre':
                    resultados.append(f"    ├─ ParénAbre:        (")
                elif tipo == 'ParenCierra':
                    resultados.append(f"    ├─ ParénCierra:      )")
                elif tipo == 'LlaveAbre':
                    resultados.append(f"    ├─ LlaveAbre:        {{")
                elif tipo == 'LlaveCierra':
                    resultados.append(f"    ├─ LlaveCierra:      }}")
                elif tipo == 'Invalido':
                    resultados.append(f"    ├─ ✗ Inválido:       {valor}")

            resultados.append(f"    └─ Total tokens: {len(tokens)}")
            resultados.append("")

        # Validar balance global
        todos_tokens = self.compilador.tokenizar(codigo)
        resultado_balance = self.compilador.validar_parentesis(todos_tokens)
        resultados.append(f"  Balance global: {resultado_balance}")

        if "Error" in resultado_balance:
            self.last_errors.append(resultado_balance)

        return {
            'resultados': resultados,
            'tokens_por_expresion': {},
        }

    # ═══════════════════════════════════════════════
    # FASE 3: ÁRBOL SINTÁCTICO
    # ═══════════════════════════════════════════════

    def generar_arboles(self, codigo):
        lineas = codigo.split('\n')
        resultados = []
        arboles = []

        resultados.append("═══ ÁRBOLES SINTÁCTICOS C++ ═══")
        resultados.append("")

        estructuras_control = []
        expresiones_encontradas = []

        for i, linea in enumerate(lineas, 1):
            linea_limpia = linea.strip()
            if not linea_limpia or linea_limpia.startswith('//'):
                continue
            
            # Detectar estructuras de control
            tokens_check = self.compilador.tokenizar(linea_limpia)
            # Detect "} while(cond);" as do-while closing
            if (tokens_check and tokens_check[0].tipo == 'LlaveCierra' and
                    len(tokens_check) >= 4 and
                    any(t.valor == 'while' for t in tokens_check)):
                estructuras_control.append((linea_limpia, 'do_while_end', i))
                continue
            if tokens_check and tokens_check[0].tipo == 'PalabraReservada':
                primer_token = tokens_check[0].valor
                if primer_token in ('while', 'for', 'if', 'switch', 'do'):
                    estructuras_control.append((linea_limpia, primer_token, i))
                    continue
            
            # Buscar líneas con operadores aritméticos que parezcan expresiones
            if any(op in linea_limpia for op in ['+', '-', '*', '/']) \
               and linea_limpia not in ('{', '}'):
                # No considerar declaraciones o palabras reservadas como expresiones
                if tokens_check and tokens_check[0].tipo != 'TipoDato' and tokens_check[0].tipo not in ('PalabraReservada', 'PalabraClave'):
                    # Quitar ; al final si existe para parsear la expresión
                    expr = linea_limpia.rstrip(';').strip()
                    # Quitar asignación si es x = expr
                    if '=' in expr:
                        partes = expr.split('=', 1)
                        expr = partes[1].strip()
                    expresiones_encontradas.append((linea_limpia, expr))

        # Procesar estructuras de control
        for linea_orig, tipo_estructura, num_linea in estructuras_control:
            tokens = self.compilador.tokenizar(linea_orig)
            
            try:
                # Pasar tabla de símbolos al parser para validaciones semánticas
                parser = ParserCpp(tokens, self.compilador.tabla_simbolos)
                
                if tipo_estructura == 'while':
                    arbol = parser.parse_while()
                elif tipo_estructura == 'for':
                    arbol = parser.parse_for(num_linea)
                elif tipo_estructura == 'if':
                    arbol = parser.parse_if()
                elif tipo_estructura == 'switch':
                    arbol = parser.parse_switch()
                elif tipo_estructura == 'do':
                    nodo_cuerpo = NodoArbol(TokenCpp('PalabraReservada', 'do'))
                    nodo_body = NodoArbol(TokenCpp('Cuerpo', '{ ... }'))
                    nodo_cuerpo.agregar_hijo(nodo_body)
                    arbol = nodo_cuerpo
                elif tipo_estructura == 'do_while_end':
                    arbol = parser.parse_do_while()
                else:
                    continue
                
                arboles.append((linea_orig, arbol))
                
                resultados.append(f"  Estructura: {tipo_estructura.upper()}")
                resultados.append(f"  Línea: {linea_orig}")
                
                # Capturar salida del imprimir
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                arbol.imprimir()
                tree_str = buffer.getvalue()
                sys.stdout = old_stdout
                
                for line in tree_str.split('\n'):
                    if line.strip():
                        resultados.append(f"    {line}")
                
                resultados.append("")
                
            except SyntaxError as e:
                resultados.append(f"  Estructura: {tipo_estructura.upper()}")
                resultados.append(f"  Línea: {linea_orig}")
                resultados.append(f"    ✗ Error de sintaxis: {e}")
                resultados.append("")
                self.last_errors.append(f"{tipo_estructura} '{linea_orig}': {e}")

        # Procesar expresiones aritméticas
        for linea_orig, expr in expresiones_encontradas:
            tokens = self.compilador.tokenizar(expr)

            # Solo tokens de expresión (quitar ; y =)
            tokens_expr = [t for t in tokens
                           if t.tipo not in ('PuntoComa', 'Asignacion', 'Invalido',
                                             'LlaveAbre', 'LlaveCierra')]

            if not tokens_expr:
                continue

            # Verificar paréntesis
            resultado_paren = self.compilador.validar_parentesis(tokens_expr)
            if "Error" in resultado_paren:
                resultados.append(f"  Expresión: {expr}")
                resultados.append(f"    ✗ {resultado_paren}")
                resultados.append("")
                continue

            try:
                parser = ParserCpp(tokens_expr)
                arbol = parser.parse()
                arboles.append((expr, arbol))

                resultados.append(f"  Expresión: {expr}")

                # Capturar salida del imprimir
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                arbol.imprimir()
                tree_str = buffer.getvalue()
                sys.stdout = old_stdout

                for line in tree_str.split('\n'):
                    if line.strip():
                        resultados.append(f"    {line}")

                resultados.append("")

            except SyntaxError as e:
                resultados.append(f"  Expresión: {expr}")
                resultados.append(f"    ✗ Error de sintaxis: {e}")
                resultados.append("")
                self.last_errors.append(f"Expresión '{expr}': {e}")

        if not estructuras_control and not expresiones_encontradas:
            resultados.append("  No se encontraron estructuras o expresiones para generar árboles.")
            resultados.append("  (Escribe expresiones como: 3+4*(2-1) )")
            resultados.append("  (O estructuras como: while(x<5){}, for(int i=0;i<10;i++), if(x>5){}, switch(x){})")

        return {
            'resultados': resultados,
            'arboles': arboles,
        }

    # ═══════════════════════════════════════════════
    # FASE 4: CÓDIGO INTERMEDIO (TAC)
    # ═══════════════════════════════════════════════

    def generar_codigo_intermedio(self, codigo):
        gen = GeneradorCodigoIntermedio(self.compilador)
        tac = gen.generar(codigo)
        return {
            'tac': tac,
            'resultados': [gen.formato_texto()],
        }

    # ═══════════════════════════════════════════════
    # FASE 5: GENERACIÓN DE ENSAMBLADOR
    # ═══════════════════════════════════════════════

    def generar_ensamblador(self, tac):
        gen = GeneradorEnsamblador()
        asm = gen.generar(tac)
        return {
            'asm': asm,
            'resultados': [gen.formato_texto()],
        }

    # ═══════════════════════════════════════════════
    # COMPILACIÓN COMPLETA
    # ═══════════════════════════════════════════════

    def compilar_todo(self, codigo):
        self.reset()

        resultado_decl = self.analizar_declaraciones(codigo)
        resultado_expr = self.analizar_expresiones(codigo)
        resultado_arbol = self.generar_arboles(codigo)
        resultado_intermedio = self.generar_codigo_intermedio(codigo)
        resultado_ensamblador = self.generar_ensamblador(resultado_intermedio['tac'])

        total_errores = len(self.last_errors)
        total_warnings = len(self.last_warnings)

        resumen = []
        resumen.append("═══ RESUMEN DE COMPILACIÓN C++ ═══")
        resumen.append("")

        if total_errores == 0 and total_warnings == 0:
            resumen.append("  ✓ Compilación exitosa — Sin errores ni advertencias")
        else:
            if total_errores > 0:
                resumen.append(f"  ✗ {total_errores} error(es) encontrado(s):")
                for err in self.last_errors:
                    resumen.append(f"    • {err}")
            if total_warnings > 0:
                resumen.append(f"  ⚠ {total_warnings} advertencia(s):")
                for warn in self.last_warnings:
                    resumen.append(f"    • {warn}")

        return {
            'declaraciones': resultado_decl,
            'expresiones': resultado_expr,
            'arboles': resultado_arbol,
            'intermedio': resultado_intermedio,
            'ensamblador': resultado_ensamblador,
            'resumen': resumen,
            'total_errores': total_errores,
            'total_warnings': total_warnings,
        }
