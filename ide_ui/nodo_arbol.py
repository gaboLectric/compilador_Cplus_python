"""
Nodo del árbol sintáctico para el compilador C++.
Soporta tanto estructura binaria (izquierdo/derecho) como multi-hijo (lista de hijos).
"""


class NodoArbol:
    def __init__(self, token):
        self.token = token
        self.izquierdo = None
        self.derecho = None
        self.hijos = []  # Lista de hijos para estructuras de control

    def __repr__(self):
        return f"Nodo({self.token.tipo}, {self.token.valor})"

    def agregar_hijo(self, hijo):
        """Agrega un hijo a la lista de hijos (para estructuras de control)"""
        self.hijos.append(hijo)

    def imprimir(self, prefijo="", es_derecho=True, es_raiz=True):
        if es_raiz:
            conector = ""
            nuevo_prefijo = ""
        else:
            conector = "└── " if es_derecho else "├── "
            nuevo_prefijo = prefijo + ("    " if es_derecho else "│   ")
        print(f"{prefijo}{conector}{self.token.valor}")
        
        # Prioridad: usar lista de hijos si existe, sino usar izquierdo/derecho
        if self.hijos:
            for i, hijo in enumerate(self.hijos):
                es_ultimo = (i == len(self.hijos) - 1)
                hijo.imprimir(nuevo_prefijo, es_ultimo, False)
        else:
            hijos = []
            if self.izquierdo:
                hijos.append(self.izquierdo)
            if self.derecho:
                hijos.append(self.derecho)
            for i, hijo in enumerate(hijos):
                es_ultimo = (i == len(hijos) - 1)
                hijo.imprimir(nuevo_prefijo, es_ultimo, False)
