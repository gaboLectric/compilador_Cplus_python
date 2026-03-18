"""
Token para el compilador C++.
Representa una unidad léxica individual.
"""


class TokenCpp:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

    def __repr__(self):
        return f"<TKN {self.tipo}, {self.valor}>"
