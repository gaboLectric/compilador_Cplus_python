"""

Gramática:
    expr    -> comparacion ((+ | -) comparacion)*
    comparacion -> termino ((< | > | <= | >= | == | !=) termino)*
    termino -> factor ((* | /) factor)*
    factor  -> Numero | Variable | ( expr )
    
    Estructuras de control:
    while   -> while ( expr ) { statement* }
    for     -> for ( init ; cond ; inc ) { statement* }
    if      -> if ( expr ) { statement* } else { statement* }
    switch  -> switch ( expr ) { case* default? }
"""

from ide_ui.token_cpp import TokenCpp
from ide_ui.nodo_arbol import NodoArbol
from ide_ui.errores import obtener_error_sintactico, obtener_error_semantico


class ParserCpp:
    def __init__(self, tokens, tabla_simbolos=None):
        self.tokens = tokens
        self.pos = 0
        self.token_actual = self.tokens[self.pos] if self.tokens else None
        self.tabla_simbolos = tabla_simbolos
        self.cases_switch = set()  # Track case values for duplicate detection

    def avanzar(self, tipo_esperado):
        if self.token_actual and self.token_actual.tipo == tipo_esperado:
            self.pos += 1
            if self.pos < len(self.tokens):
                self.token_actual = self.tokens[self.pos]
            else:
                self.token_actual = TokenCpp('Fin', '')
        else:
            tipo_real = self.token_actual.tipo if self.token_actual else 'None'
            codigo = 6
            if tipo_esperado == 'PuntoComa': codigo = 1
            elif tipo_esperado == 'LlaveCierra': codigo = 2
            elif tipo_esperado == 'Asignacion': codigo = 3
            elif tipo_esperado == 'ParenCierra': codigo = 4
            elif tipo_esperado == 'Variable': codigo = 5
            elif tipo_esperado == 'Numero': codigo = 7
            elif tipo_esperado == 'LlaveAbre': codigo = 9
            mensaje = obtener_error_sintactico(codigo)
            raise SyntaxError(f"{mensaje}. Se esperaba {tipo_esperado}, se encontró {tipo_real}")

    def parse(self):
        return self.expr()

    def expr(self):
        nodo = self.comparacion()
        while self.token_actual and self.token_actual.tipo in ('Suma', 'Resta'):
            token_op = self.token_actual
            self.avanzar(token_op.tipo)
            nodo_op = NodoArbol(token_op)
            nodo_op.izquierdo = nodo
            nodo_op.derecho = self.comparacion()
            nodo = nodo_op
        return nodo

    def comparacion(self):
        nodo = self.termino()
        while self.token_actual and self.token_actual.tipo == 'Comparacion':
            token_op = self.token_actual
            self.avanzar(token_op.tipo)
            nodo_op = NodoArbol(token_op)
            nodo_op.izquierdo = nodo
            nodo_op.derecho = self.termino()
            nodo = nodo_op
        return nodo

    def termino(self):
        nodo = self.factor()
        while self.token_actual and self.token_actual.tipo in ('Multiplicar', 'Dividir'):
            token_op = self.token_actual
            self.avanzar(token_op.tipo)
            nodo_op = NodoArbol(token_op)
            nodo_op.izquierdo = nodo
            nodo_op.derecho = self.factor()
            nodo = nodo_op
        return nodo

    def factor(self):
        token = self.token_actual
        if token.tipo == 'Numero':
            self.avanzar('Numero')
            return NodoArbol(token)
        elif token.tipo == 'Variable':
            self.avanzar('Variable')
            return NodoArbol(token)
        elif token.tipo == 'ParenAbre':
            self.avanzar('ParenAbre')
            nodo = self.expr()
            self.avanzar('ParenCierra')
            return nodo
        else:
            raise SyntaxError(f"Token inesperado: {token.tipo} '{token.valor}'. {obtener_error_sintactico(6)}")

    # ═══════════════════════════════════════════════
    # PARSERS DE ESTRUCTURAS DE CONTROL
    # ═══════════════════════════════════════════════

    def parse_while(self):
        """Parse: while ( variable operador constante ) { ... }"""
        if self.token_actual.valor != 'while':
            raise SyntaxError("Se esperaba 'while'")
        
        nodo_while = NodoArbol(self.token_actual)
        self.avanzar('PalabraReservada')
        
        # (
        self.avanzar('ParenAbre')
        
        # Condición: variable operador constante
        if self.token_actual.tipo != 'Variable':
            raise SyntaxError(f"{obtener_error_semantico(6, 'Condición while debe iniciar con variable')}")
        
        var_token = self.token_actual
        nodo_var = NodoArbol(var_token)
        self.avanzar('Variable')
        
        # Validar que variable exista en tabla de símbolos
        if self.tabla_simbolos and not self.tabla_simbolos.existe(var_token.valor):
            raise SyntaxError(f"{obtener_error_semantico(1, var_token.valor)}")
        
        # Operador
        if self.token_actual.tipo not in ('Comparacion', 'Suma', 'Resta', 'Multiplicar', 'Dividir'):
            raise SyntaxError(f"{obtener_error_semantico(6, 'Condición while requiere operador de comparación o aritmético')}")
        
        op_token = self.token_actual
        nodo_op = NodoArbol(op_token)
        nodo_op.izquierdo = nodo_var
        self.avanzar(op_token.tipo)
        
        # Constante o variable
        if self.token_actual.tipo not in ('Numero', 'Variable', 'Booleano'):
            raise SyntaxError(f"{obtener_error_semantico(6, 'Condición while requiere constante o variable después del operador')}")
        
        const_token = self.token_actual
        nodo_const = NodoArbol(const_token)
        nodo_op.derecho = nodo_const
        self.avanzar(const_token.tipo)
        
        nodo_while.agregar_hijo(nodo_op)  # Condición
        
        # )
        self.avanzar('ParenCierra')
        
        # {
        self.avanzar('LlaveAbre')
        
        # Cuerpo (por ahora vacío, se podría extender para parsear statements)
        nodo_cuerpo = NodoArbol(TokenCpp('Cuerpo', '{ ... }'))
        nodo_while.agregar_hijo(nodo_cuerpo)
        
        return nodo_while

    def parse_for(self, linea_actual=0):
        """Parse: for ( tipo var = valor ; var op valor ; var++ ) { ... }"""
        if self.token_actual.valor != 'for':
            raise SyntaxError("Se esperaba 'for'")
        
        nodo_for = NodoArbol(self.token_actual)
        self.avanzar('PalabraReservada')
        
        # (
        self.avanzar('ParenAbre')
        
        # Parte 1: inicialización (tipo var = valor)
        if self.token_actual.tipo != 'TipoDato':
            raise SyntaxError("condicion1 debe iniciar con tipo de dato (e.g., int x=0)")
        
        tipo_token = self.token_actual
        nodo_tipo = NodoArbol(tipo_token)
        self.avanzar('TipoDato')
        
        if self.token_actual.tipo != 'Variable':
            raise SyntaxError("condicion1 mal formada, esperaba <TipoDato> <Variable> = <valor>")
        
        var_token = self.token_actual
        nodo_var = NodoArbol(var_token)
        self.avanzar('Variable')
        
        # Registrar variable en tabla de símbolos
        if self.tabla_simbolos:
            self.tabla_simbolos.agregar(var_token.valor, tipo_token.valor, linea_actual)
        
        self.avanzar('Asignacion')
        
        if self.token_actual.tipo not in ('Numero', 'Variable', 'Caracter'):
            raise SyntaxError("condicion1 mal formada, esperaba <TipoDato> <Variable> = <valor>")
        
        valor_token = self.token_actual
        nodo_valor = NodoArbol(valor_token)
        self.avanzar(valor_token.tipo)
        
        nodo_init = NodoArbol(TokenCpp('Init', 'inicialización'))
        nodo_init.agregar_hijo(nodo_tipo)
        nodo_init.agregar_hijo(nodo_var)
        nodo_init.agregar_hijo(nodo_valor)
        nodo_for.agregar_hijo(nodo_init)
        
        # ;
        self.avanzar('PuntoComa')
        
        # Parte 2: condición (var op valor)
        if self.token_actual.tipo != 'Variable':
            raise SyntaxError("condicion2 mal formada, esperaba <Variable> <Operador> <valor>")
        
        var_cond_token = self.token_actual
        nodo_var_cond = NodoArbol(var_cond_token)
        
        # Validar que variable exista
        if self.tabla_simbolos and not self.tabla_simbolos.existe(var_cond_token.valor):
            raise SyntaxError(f"{obtener_error_semantico(1, var_cond_token.valor)}")
        
        self.avanzar('Variable')
        
        if self.token_actual.tipo != 'Comparacion':
            raise SyntaxError("condicion2 mal formada, esperaba <Variable> <Operador> <valor>")
        
        op_cond_token = self.token_actual
        nodo_op_cond = NodoArbol(op_cond_token)
        nodo_op_cond.izquierdo = nodo_var_cond
        self.avanzar('Comparacion')
        
        if self.token_actual.tipo not in ('Numero', 'Variable'):
            raise SyntaxError("condicion2 mal formada, esperaba <Variable> <Operador> <valor>")
        
        valor_cond_token = self.token_actual
        nodo_valor_cond = NodoArbol(valor_cond_token)
        nodo_op_cond.derecho = nodo_valor_cond
        self.avanzar(valor_cond_token.tipo)
        
        nodo_for.agregar_hijo(nodo_op_cond)  # Condición
        
        # ;
        self.avanzar('PuntoComa')
        
        # Parte 3: incremento (var++ o ++var)
        if self.token_actual.tipo == 'Variable':
            var_inc_token = self.token_actual
            nodo_var_inc = NodoArbol(var_inc_token)
            self.avanzar('Variable')
            
            if self.token_actual.tipo != 'Incremento':
                raise SyntaxError("condicion3 mal formada, esperaba <Variable> ++/--")
            
            inc_token = self.token_actual
            nodo_inc = NodoArbol(inc_token)
            nodo_inc.izquierdo = nodo_var_inc
            self.avanzar('Incremento')
        elif self.token_actual.tipo == 'Incremento':
            inc_token = self.token_actual
            nodo_inc = NodoArbol(inc_token)
            self.avanzar('Incremento')
            
            if self.token_actual.tipo != 'Variable':
                raise SyntaxError("condicion3 mal formada, esperaba <Variable> ++/--")
            
            var_inc_token = self.token_actual
            nodo_var_inc = NodoArbol(var_inc_token)
            nodo_inc.derecho = nodo_var_inc
            self.avanzar('Variable')
        else:
            raise SyntaxError("condicion3 mal formada, esperaba <Variable> ++/--")
        
        nodo_for.agregar_hijo(nodo_inc)  # Incremento
        
        # )
        self.avanzar('ParenCierra')
        
        # {
        self.avanzar('LlaveAbre')
        
        # Cuerpo
        nodo_cuerpo = NodoArbol(TokenCpp('Cuerpo', '{ ... }'))
        nodo_for.agregar_hijo(nodo_cuerpo)
        
        return nodo_for

    def parse_if(self):
        """Parse: if ( expr ) { ... }"""
        if self.token_actual.valor != 'if':
            raise SyntaxError("Se esperaba 'if'")
        
        nodo_if = NodoArbol(self.token_actual)
        self.avanzar('PalabraReservada')
        
        # (
        self.avanzar('ParenAbre')
        
        # Condición (reutilizamos expr para expresiones generales)
        nodo_cond = self.expr()
        nodo_if.agregar_hijo(nodo_cond)
        
        # )
        self.avanzar('ParenCierra')
        
        # {
        self.avanzar('LlaveAbre')
        
        # Cuerpo then
        nodo_then = NodoArbol(TokenCpp('Then', '{ ... }'))
        nodo_if.agregar_hijo(nodo_then)
        
        return nodo_if

    def parse_switch(self):
        """Parse: switch ( var ) { ... } - Simplificado para línea única"""
        if self.token_actual.valor != 'switch':
            raise SyntaxError("Se esperaba 'switch'")
        
        nodo_switch = NodoArbol(self.token_actual)
        self.avanzar('PalabraReservada')
        
        # (
        self.avanzar('ParenAbre')
        
        # Variable o constante
        if self.token_actual.tipo not in ('Variable', 'Numero', 'Caracter'):
            raise SyntaxError("switch espera una variable o constante")
        
        var_token = self.token_actual
        nodo_var = NodoArbol(var_token)
        
        # Validar que variable exista
        if var_token.tipo == 'Variable' and self.tabla_simbolos and not self.tabla_simbolos.existe(var_token.valor):
            raise SyntaxError(f"{obtener_error_semantico(1, var_token.valor)}")
        
        self.avanzar(var_token.tipo)
        nodo_switch.agregar_hijo(nodo_var)
        
        # )
        self.avanzar('ParenCierra')
        
        # {
        self.avanzar('LlaveAbre')
        
        # Cuerpo simplificado (los cases se manejan en líneas separadas por el analizador léxico)
        nodo_cuerpo = NodoArbol(TokenCpp('Cuerpo', '{ cases... }'))
        nodo_switch.agregar_hijo(nodo_cuerpo)
        
        return nodo_switch
