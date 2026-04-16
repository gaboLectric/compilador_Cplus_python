"""
Analizador léxico (tokenizador) para C++.

Tipos de datos: int, double, float, char, string, bool, void
Patrones:
    Declaración:  <TDato> <Variable> ;
    Main:         <TDato|void> main ( ) {
    Asignación:   <Variable> = <constante> ;
    Cierre:       }
    cout:         cout << <expr> ;
    cin:          cin >> <Variable> ;
    if:           if ( <expr> ) {
    else:         else {  |  } else {
    while:        while ( <expr> ) {
    for:          for ( ... ) {
    return:       return <expr> ;
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from automata import Automata

from ide_ui.token_cpp import TokenCpp
from ide_ui.tabla_simbolos import TablaSimbolos
from ide_ui.errores import obtener_error_sintactico, obtener_error_semantico


class CompiladorCpp:
    TIPOS_DATOS = {'int', 'double', 'float', 'char', 'string', 'bool'}

    DESCRIPCION_TIPO = {
        'int':    'tipo de dato entero',
        'double': 'tipo de dato entero largo',
        'float':  'tipo de dato punto flotante',
        'char':   'tipo de dato caracter',
        'string': 'tipo de dato cadena',
        'bool':   'tipo de dato booleano',
        'void':   'tipo vacío',
    }

    PALABRAS_RESERVADAS = {
        'main', 'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'default',
        'break', 'continue', 'void', 'true', 'false',
        'cout', 'cin', 'endl', 'include', 'using', 'namespace', 'std',
    }

    PALABRAS_CLAVE = {
        'import', 'public', 'private', 'return'
    }

    PATRON_TOKENS = re.compile(r"""
        (?P<Numero>\d+(\.\d+)?)        |
        (?P<Cadena>"[^"]*")            |
        (?P<Caracter>'[^']*')          |
        (?P<Comentario>//.*|/\*[\s\S]*?\*/) |
        (?P<Identificador>[a-zA-Z_]\w*)|
        (?P<PuntoComa>;)               |
        (?P<Insercion><<)              |
        (?P<Extraccion>>>)             |
        (?P<And>&&)                    |
        (?P<Or>\|\|)                   |
        (?P<Comparacion><=|>=|==|!=|<|>) |
        (?P<Asignacion>=)              |
        (?P<Incremento>\+\+|--)        |
        (?P<Suma>\+)                   |
        (?P<Resta>-)                   |
        (?P<Multiplicar>\*)            |
        (?P<Dividir>/)                 |
        (?P<ParenAbre>\()              |
        (?P<ParenCierra>\))            |
        (?P<LlaveAbre>\{)             |
        (?P<LlaveCierra>\})            |
        (?P<CorcheteAbre>\[)           |
        (?P<CorcheteCierra>\])         |
        (?P<DosPuntos>:)               |
        (?P<Espacio>\s+)              |
        (?P<Invalido>.)
    """, re.VERBOSE)

    def __init__(self):
        self.automata = Automata()
        self.tabla_simbolos = TablaSimbolos()

    def reset(self):
        self.automata = Automata()
        self.tabla_simbolos = TablaSimbolos()

    # ─── TOKENIZACIÓN ───

    def tokenizar(self, texto):
        tokens = []
        for match in self.PATRON_TOKENS.finditer(texto):
            tipo = match.lastgroup
            valor = match.group()
            if tipo == 'Espacio':
                continue
            if tipo == 'Comentario':
                tokens.append(TokenCpp(tipo, valor))
                continue
            if tipo == 'Identificador':
                if valor in self.TIPOS_DATOS or valor == 'void':
                    tipo = 'TipoDato'
                elif valor in ('true', 'false'):
                    tipo = 'Booleano'
                elif valor in self.PALABRAS_CLAVE:
                    tipo = 'PalabraClave'
                elif valor in self.PALABRAS_RESERVADAS:
                    tipo = 'PalabraReservada'
                else:
                    if self.automata.procesar_cadena(valor):
                        tipo = 'Variable'
                    else:
                        tipo = 'Invalido'
            tokens.append(TokenCpp(tipo, valor))
        return tokens

    # ─── ANÁLISIS DE UNA LÍNEA ───

    def analizar_linea(self, linea, num_linea):
        linea_limpia = linea.strip()
        if not linea_limpia:
            return ('vacia', None, None)

        tokens_todos = self.tokenizar(linea_limpia)
        if not tokens_todos:
            return ('vacia', None, None)

        # Filtrar comentarios para el análisis lógico, pero conservarlos para el reporte
        tokens = [t for t in tokens_todos if t.tipo != 'Comentario']
        
        if not tokens: # Solo había comentarios
            return ('comentario', f"{linea_limpia}", True)

        if len(tokens) == 1 and tokens[0].tipo == 'LlaveCierra':
            return ('cierre', f"{linea_limpia} // cierre de bloque", True)

        if len(tokens) == 1 and tokens[0].tipo == 'LlaveAbre':
            return ('apertura', f"{linea_limpia} // apertura de bloque", True)

        # Validación: No usar palabras reservadas como identificadores
        for t in tokens:
            if t.tipo == 'PalabraReservada' or t.tipo == 'TipoDato':
                # Si está en una posición donde debería haber una variable
                # Ejemplo: int if;  -> tokens[1] es PalabraReservada
                if len(tokens) >= 2 and tokens[0].tipo == 'TipoDato' and t == tokens[1]:
                    return ('error', f"{linea_limpia} // {obtener_error_semantico(5, f'No puedes usar la palabra reservada {t.valor} como nombre de variable')}", False)


        if self._es_patron_main(tokens):
            tipo_ret = tokens[0].valor
            return ('main', f"{linea_limpia} // función principal, retorna {tipo_ret}", True)

        if self._es_patron_declaracion(tokens):
            tipo_dato = tokens[0].valor
            nombre_var = tokens[1].valor
            desc = self.DESCRIPCION_TIPO.get(tipo_dato, tipo_dato)
            exito, msg = self.tabla_simbolos.agregar(nombre_var, tipo_dato, num_linea)
            mensaje = f"{linea_limpia} // {desc}, variable {nombre_var}"
            if not exito:
                mensaje += f", {msg}"
            return ('declaracion', mensaje, True)

        if self._es_declaracion_sin_punto_coma(tokens):
            return ('error', f"{linea_limpia} // {obtener_error_sintactico(1)}", False)

        if self._es_orden_incorrecto(tokens):
            return ('error', f"{linea_limpia} // {obtener_error_sintactico(10)}", False)

        if self._es_tipo_sin_variable(tokens):
            return ('error', f"{linea_limpia} // {obtener_error_sintactico(11)}", False)

        if self._es_patron_asignacion(tokens):
            nombre_var = tokens[0].valor
            valor = tokens[2].valor
            tipo_val = tokens[2].tipo
            if self.tabla_simbolos.existe(nombre_var):
                var_info = self.tabla_simbolos.obtener(nombre_var)
                tipo_var = var_info['tipo']
                
                # Regla semántica: Utilización de tipos de datos
                error_tipo = False
                if tipo_var in ('int', 'double', 'float') and tipo_val not in ('Numero', 'Variable', 'Booleano'):
                    error_tipo = True
                elif tipo_var == 'string' and tipo_val not in ('Cadena', 'Variable'):
                    error_tipo = True
                elif tipo_var == 'char' and tipo_val not in ('Caracter', 'Variable'):
                    error_tipo = True
                elif tipo_var == 'bool' and tipo_val not in ('Booleano', 'Numero', 'Variable'):
                    error_tipo = True
                    
                if error_tipo:
                    return ('error', f"{linea_limpia} // {obtener_error_semantico(4, f'Tipo incompatible: esperado {tipo_var}, entregado {tipo_val}')}", False)

                # Regla semántica: si el valor es otra variable, verificar existencia
                if tipo_val == 'Variable':
                    if not self.tabla_simbolos.existe(valor):
                        return ('error', f"{linea_limpia} // {obtener_error_semantico(1, valor)} (variable asignada no existe)", False)

                self.tabla_simbolos.asignar_valor(nombre_var, valor)
                return ('asignacion', f"{linea_limpia} // asignación: {nombre_var} = {valor}", True)
            else:
                return ('error', f"{linea_limpia} // {obtener_error_semantico(1, nombre_var)}", False)

        # cout << expr ;
        if self._es_patron_cout(tokens):
            contenido = ' '.join(t.valor for t in tokens[2:-1])  # entre << y ;
            return ('cout', f"{linea_limpia} // salida: cout << {contenido}", True)

        # cin >> variable ;
        if self._es_patron_cin(tokens):
            nombre_var = tokens[2].valor
            return ('cin', f"{linea_limpia} // entrada: cin >> {nombre_var}", True)

        # if ( expr ) {
        if self._es_patron_if(tokens):
            err = self._validar_flujo_semantico(tokens)
            if err: return ('error', f"{linea_limpia} // {obtener_error_semantico(5, err)}", False)
            return ('if', f"{linea_limpia} // estructura condicional if", True)

        # else {  o  } else {
        if self._es_patron_else(tokens):
            return ('else', f"{linea_limpia} // estructura condicional else", True)

        # while ( expr ) {
        if self._es_patron_while(tokens):
            err = self._validar_ciclo_semantico(tokens)
            if err: return ('error', f"{linea_limpia} // {obtener_error_semantico(6, err)}", False)
            return ('while', f"{linea_limpia} // ciclo while", True)

        # for ( ... ) {
        if tokens[0].tipo == 'ParenAbre' and any(t.valor == 'for' for t in tokens):
             return ('error', f"{linea_limpia} // {obtener_error_semantico(6, 'Orden incorrecto, keyword for desplazado')}", False)

        if tokens[0].valor == 'for':
            err_sint, err_sem = self._validar_for_sintactico(tokens, num_linea)
            if err_sint:
                return ('error', f"{linea_limpia} // Error sintáctico: {err_sint}", False)
            if err_sem:
                 return ('error', f"{linea_limpia} // {obtener_error_semantico(6, err_sem)}", False)
            return ('for', f"{linea_limpia} // ciclo for", True)

        # Incremento independiente: variable++; o ++variable;
        if len(tokens) >= 2 and tokens[-1].tipo == 'PuntoComa':
            if (tokens[0].tipo == 'Variable' and tokens[1].tipo == 'Incremento') or \
               (tokens[0].tipo == 'Incremento' and tokens[1].tipo == 'Variable'):
                nombre_var = tokens[0].valor if tokens[0].tipo == 'Variable' else tokens[1].valor
                if self.tabla_simbolos.existe(nombre_var):
                    return ('incremento', f"{linea_limpia} // operación de incremento/decremento", True)
                else:
                    return ('error', f"{linea_limpia} // {obtener_error_semantico(1, nombre_var)}", False)

        # return expr ;
        if self._es_patron_return(tokens):
            valor_ret = ' '.join(t.valor for t in tokens[1:-1])
            return ('return', f"{linea_limpia} // retorno: {valor_ret}", True)

        # break ;
        if tokens[0].valor == 'break':
            if len(tokens) < 2 or tokens[1].tipo != 'PuntoComa':
                return ('error', f"{linea_limpia} // Error sintáctico: break debe terminar con ;", False)
            return ('break', f"{linea_limpia} // interrupción de flujo", True)

        # default :
        if tokens[0].valor == 'default':
            if len(tokens) < 2 or tokens[1].tipo != 'DosPuntos':
                return ('error', f"{linea_limpia} // Error sintáctico: falta ':' después de default", False)
            return ('default', f"{linea_limpia} // caso por defecto de switch", True)

        # ─── SWITCH ───
        if tokens[0].valor == 'switch':
            # Error: switch sin paréntesis abre, e.g. "switch opcion {"
            if len(tokens) < 2 or tokens[1].tipo != 'ParenAbre':
                return ('error', f"{linea_limpia} // {obtener_error_sintactico(4)} — falta '(' en switch", False)
            # Error: switch( sin cierre, e.g. "switch(opcion {"
            if len(tokens) < 3 or tokens[2].tipo not in ('Variable', 'Numero', 'Caracter'):
                return ('error', f"{linea_limpia} // {obtener_error_sintactico(5)} — switch espera una variable o constante", False)
            if len(tokens) < 4 or tokens[3].tipo != 'ParenCierra':
                return ('error', f"{linea_limpia} // {obtener_error_sintactico(4)} — falta ')' en switch", False)
            # Error: sin llave abre
            if len(tokens) < 5 or tokens[4].tipo != 'LlaveAbre':
                return ('error', f"{linea_limpia} // {obtener_error_sintactico(9)} — falta '{{' en switch", False)
            # Error semántico: variable del switch no declarada
            if tokens[2].tipo == 'Variable' and not self.tabla_simbolos.existe(tokens[2].valor):
                return ('error', f"{linea_limpia} // {obtener_error_semantico(1, tokens[2].valor)} — variable no declarada en switch", False)
            return ('switch', f"{linea_limpia} // estructura de control switch", True)

        # Orden incorrecto: (variable) switch  → la variable aparece antes que switch
        if (len(tokens) >= 2 and
                tokens[0].tipo in ('Variable', 'ParenAbre') and
                any(t.valor == 'switch' for t in tokens)):
            return ('error', f"{linea_limpia} // {obtener_error_semantico(5, 'Orden incorrecto, esperaba switch(variable)')}", False)

        # Orden incorrecto: break case  o  case break
        if len(tokens) >= 2 and tokens[0].valor == 'break' and tokens[1].valor == 'case':
            return ('error', f"{linea_limpia} // {obtener_error_semantico(5, 'Orden incorrecto: break antes de case')}", False)

        if len(tokens) >= 3 and tokens[0].valor == 'case' and tokens[2].valor == 'break':
            return ('error', f"{linea_limpia} // {obtener_error_semantico(5, 'Orden incorrecto: break dentro de etiqueta case')}", False)

        # ─── CASE ───
        if tokens[0].valor == 'case':
            if len(tokens) < 3:
                return ('error', f"{linea_limpia} // Error sintáctico: case incompleto, esperaba 'case <valor>:'", False)
            if tokens[1].tipo not in ('Numero', 'Cadena', 'Caracter', 'Variable', 'Booleano', 'PalabraReservada'):
                return ('error', f"{linea_limpia} // Error sintáctico: case espera un valor constante o variable", False)
            if tokens[2].tipo != 'DosPuntos':
                return ('error', f"{linea_limpia} // Error sintáctico: falta ':' después del valor en case", False)
            return ('case', f"{linea_limpia} // caso de switch: {tokens[1].valor}", True)

        return ('no_identificado', f"{linea_limpia} // {obtener_error_sintactico(6)}", False)

    # ─── VERIFICACIÓN DE PATRONES ───

    def _es_patron_main(self, tokens):
        if len(tokens) < 5:
            return False
        tipos = [t.tipo for t in tokens]
        return (tipos[0] == 'TipoDato' and
                tokens[1].valor == 'main' and
                tipos[2] == 'ParenAbre' and
                tipos[3] == 'ParenCierra' and
                tipos[4] == 'LlaveAbre')

    def _es_patron_declaracion(self, tokens):
        if len(tokens) != 3:
            return False
        return (tokens[0].tipo == 'TipoDato' and tokens[0].valor != 'void' and
                tokens[1].tipo == 'Variable' and tokens[2].tipo == 'PuntoComa')

    def _es_declaracion_sin_punto_coma(self, tokens):
        if len(tokens) != 2:
            return False
        return (tokens[0].tipo == 'TipoDato' and tokens[0].valor != 'void' and
                tokens[1].tipo == 'Variable')

    def _es_orden_incorrecto(self, tokens):
        if len(tokens) < 2:
            return False
        return (tokens[0].tipo == 'Variable' and tokens[1].tipo == 'TipoDato')

    def _es_tipo_sin_variable(self, tokens):
        if len(tokens) != 2:
            return False
        return (tokens[0].tipo == 'TipoDato' and tokens[1].tipo == 'PuntoComa')

    def _es_patron_asignacion(self, tokens):
        if len(tokens) != 4:
            return False
        return (tokens[0].tipo == 'Variable' and tokens[1].tipo == 'Asignacion' and
                tokens[2].tipo in ('Numero', 'Cadena', 'Caracter', 'Booleano', 'Variable') and
                tokens[3].tipo == 'PuntoComa')

    # ─── PATRONES NUEVOS: cout, cin, if, else, while, for, return ───

    def _es_patron_cout(self, tokens):
        """cout << expr ;  (mín 4 tokens: cout << algo ;)"""
        if len(tokens) < 4:
            return False
        return (tokens[0].valor == 'cout' and
                tokens[1].tipo == 'Insercion' and
                tokens[-1].tipo == 'PuntoComa')

    def _es_patron_cin(self, tokens):
        """cin >> variable ;"""
        if len(tokens) < 4:
            return False
        return (tokens[0].valor == 'cin' and
                tokens[1].tipo == 'Extraccion' and
                tokens[-1].tipo == 'PuntoComa')

    def _es_patron_if(self, tokens):
        """if ( ... ) {  o  if ( ... )"""
        if len(tokens) < 4:
            return False
        return (tokens[0].valor == 'if' and
                tokens[1].tipo == 'ParenAbre')

    def _es_patron_else(self, tokens):
        """else {  o  } else {"""
        for t in tokens:
            if t.valor == 'else':
                return True
        return False

    def _es_patron_while(self, tokens):
        """while ( ... ) {"""
        if len(tokens) < 4:
            return False
        return (tokens[0].valor == 'while' and
                tokens[1].tipo == 'ParenAbre')

    def _es_patron_for(self, tokens):
        """for ( ... ) {"""
        if len(tokens) < 4:
            return False
        return (tokens[0].valor == 'for' and
                tokens[1].tipo == 'ParenAbre')

    def _es_patron_return(self, tokens):
        """return expr ;  o  return ;"""
        if len(tokens) < 2:
            return False
        return (tokens[0].valor == 'return' and
                tokens[-1].tipo == 'PuntoComa')

    # ─── VALIDACIÓN DE BALANCE ───

    def validar_parentesis(self, tokens):
        paren = 0
        llaves = 0
        corch = 0
        for token in tokens:
            if token.tipo == 'ParenAbre': paren += 1
            elif token.tipo == 'ParenCierra':
                paren -= 1
                if paren < 0:
                    return "Error: se encontró ')' sin un '(' correspondiente."
            elif token.tipo == 'LlaveAbre': llaves += 1
            elif token.tipo == 'LlaveCierra':
                llaves -= 1
                if llaves < 0:
                    return "Error: se encontró '}' sin un '{' correspondiente."
            elif token.tipo == 'CorcheteAbre': corch += 1
            elif token.tipo == 'CorcheteCierra':
                corch -= 1
                if corch < 0:
                    return "Error: se encontró ']' sin un '[' correspondiente."
        errores = []
        if paren > 0: errores.append(f"faltan {paren} paréntesis de cierre")
        if llaves > 0: errores.append(f"faltan {llaves} llaves de cierre")
        if corch > 0: errores.append(f"faltan {corch} corchetes de cierre")
        if errores:
            return "Error: " + ", ".join(errores) + "."
        return "Paréntesis y llaves balanceados correctamente."
        
    def _validar_flujo_semantico(self, tokens):
        """ Control de flujo: asegura que la condición if/while sea válida."""
        en_parentesis = False
        paren_nivel = 0
        elementos_condicion = 0
        for t in tokens:
            if t.tipo == 'ParenAbre':
                paren_nivel += 1
                en_parentesis = True
                continue
            if t.tipo == 'ParenCierra':
                paren_nivel -= 1
                if paren_nivel == 0:
                    en_parentesis = False
                continue
                
            if en_parentesis:
                elementos_condicion += 1
                if t.tipo == 'Variable' and not self.tabla_simbolos.existe(t.valor):
                    return f"Variable '{t.valor}' en condición no declarada"
                if t.tipo in ('TipoDato', 'PalabraReservada', 'PalabraClave'):
                    return f"Léxico inválido en condición ('{t.valor}')"
                    
        if elementos_condicion == 0:
            return "Condición de flujo vacía"
        return None

    def _validar_ciclo_semantico(self, tokens):
        """ Control de ciclos: asegura estructura mínima coherente."""
        # Se reutiliza parte de la lógica de flujo
        if tokens[0].valor == 'while':
            return self._validar_flujo_semantico(tokens)
        return None

    def _validar_for_sintactico(self, tokens, linea_actual=0):
        """ Control de sintaxis y semántica para for """
        if len(tokens) < 3 or tokens[1].tipo != 'ParenAbre':
             return ("falta '(' en for", None)
             
        if tokens[-1].tipo != 'LlaveAbre':
             return (f"{obtener_error_sintactico(9)} para for", None)
             
        if tokens[-2].tipo != 'ParenCierra':
             return (f"{obtener_error_sintactico(4)} o ')' faltante", None)

        interior = tokens[2:-2]
        
        condiciones = []
        actual = []
        for t in interior:
            if t.tipo == 'PuntoComa':
                condiciones.append(actual)
                actual = []
            else:
                actual.append(t)
        condiciones.append(actual)
        
        if len(condiciones) != 3:
            return ("estructura de for incompleta, se esperaban 3 partes separadas por ;", None)
            
        cond1, cond2, cond3 = condiciones
        
        # Validar semántica de orden incorrecto
        if cond1 and cond1[0].tipo != 'TipoDato':
            return (None, "condicion1 debe iniciar con tipo de dato (e.g., int x=0)")
            
        # cond1: <TipoDato> <Variable> <Asignacion> <Numero/...>
        if len(cond1) < 4:
            return ("condicion1 incompleta, esperaba <TipoDato> <Variable> = <valor>", None)
        if cond1[0].tipo != 'TipoDato' or cond1[1].tipo != 'Variable' or cond1[2].tipo != 'Asignacion' or cond1[3].tipo not in ('Numero', 'Variable', 'Caracter'):
            return ("condicion1 mal formada, esperaba <TipoDato> <Variable> = <valor>", None)
        
        # --- NUEVO: Registrar variable del for en la tabla de símbolos ---
        tipo_var = cond1[0].valor
        nombre_var = cond1[1].valor
        self.tabla_simbolos.agregar(nombre_var, tipo_var, linea_actual)
            
        # cond2: <Variable> <Comparacion> <Numero/...>
        if len(cond2) < 3:
            return ("condicion2 incompleta, esperaba <Variable> <Operador> <valor>", None)
        if cond2[0].tipo != 'Variable' or cond2[1].tipo != 'Comparacion' or cond2[2].tipo not in ('Numero', 'Variable'):
            return ("condicion2 mal formada, esperaba <Variable> <Operador> <valor>", None)
        
        # Validar semántica: variable en cond2 debe existir
        if not self.tabla_simbolos.existe(cond2[0].valor):
            return (None, f"Variable '{cond2[0].valor}' en condicion2 no declarada")
            
        # cond3: <Variable> <Incremento>
        if len(cond3) < 2:
            return ("condicion3 incompleta, esperaba <Variable> <Incremento>", None)
        if (cond3[0].tipo == 'Variable' and cond3[1].tipo == 'Incremento') or \
           (cond3[0].tipo == 'Incremento' and cond3[1].tipo == 'Variable'):
            nombre_inc = cond3[0].valor if cond3[0].tipo == 'Variable' else cond3[1].valor
            if not self.tabla_simbolos.existe(nombre_inc):
                return (None, f"Variable '{nombre_inc}' en condicion3 no declarada")
        else:
            return ("condicion3 mal formada, esperaba <Variable> ++/--", None)
            
        return (None, None)

