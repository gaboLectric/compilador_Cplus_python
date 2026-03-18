"""

Gramática:
    expr    -> termino ((+ | -) termino)*
    termino -> factor ((* | /) factor)*
    factor  -> Numero | Variable | ( expr )
"""

from ide_ui.token_cpp import TokenCpp
from ide_ui.nodo_arbol import NodoArbol
from ide_ui.errores import obtener_error_sintactico


class ParserCpp:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.token_actual = self.tokens[self.pos] if self.tokens else None

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
        nodo = self.termino()
        while self.token_actual and self.token_actual.tipo in ('Suma', 'Resta'):
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
