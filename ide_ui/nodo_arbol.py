"""
Nodo del árbol sintáctico para el compilador C++.
"""


class NodoArbol:
    def __init__(self, token):
        self.token = token
        self.izquierdo = None
        self.derecho = None

    def __repr__(self):
        return f"Nodo({self.token.tipo}, {self.token.valor})"

    def imprimir(self, prefijo="", es_derecho=True, es_raiz=True):
        if es_raiz:
            conector = ""
            nuevo_prefijo = ""
        else:
            conector = "└── " if es_derecho else "├── "
            nuevo_prefijo = prefijo + ("    " if es_derecho else "│   ")
        print(f"{prefijo}{conector}{self.token.valor}")
        hijos = []
        if self.izquierdo:
            hijos.append(self.izquierdo)
        if self.derecho:
            hijos.append(self.derecho)
        for i, hijo in enumerate(hijos):
            es_ultimo = (i == len(hijos) - 1)
            hijo.imprimir(nuevo_prefijo, es_ultimo, False)
