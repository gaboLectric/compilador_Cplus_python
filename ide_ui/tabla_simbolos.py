"""
Tabla de símbolos para el compilador C++.
Almacena las variables declaradas: nombre, tipo, línea, valor.
"""


import re

from ide_ui.errores import obtener_error_semantico

class TablaSimbolos:
    def __init__(self):
        self.simbolos = {}
        self.lista_simbolos = []

    def agregar(self, nombre, tipo_dato, linea):
        if nombre in self.simbolos:
            prev = self.simbolos[nombre]
            # Si se registra en la misma línea con el mismo tipo, permitirlo (por el pre-registro)
            if prev['linea'] == linea and prev['tipo'] == tipo_dato:
                return (True, f"Variable '{nombre}' ya registrada en esta línea")
                
            if prev['tipo'] != tipo_dato:
                return (False, obtener_error_semantico(3, f"'{nombre}' ya es '{prev['tipo']}' en línea {prev['linea']}"))
            else:
                return (False, obtener_error_semantico(2, f"'{nombre}' ya es '{prev['tipo']}' en línea {prev['linea']}"))

        entrada = {'nombre': nombre, 'tipo': tipo_dato, 'linea': linea, 'valor': None, 'tamano': None}
        if '[' in tipo_dato:
            m = re.search(r'\[(\d+)\]', tipo_dato)
            if m:
                entrada['tamano'] = int(m.group(1))
        self.simbolos[nombre] = entrada
        self.lista_simbolos.append(entrada)
        return (True, f"Variable '{nombre}' de tipo '{tipo_dato}' registrada")

    def existe(self, nombre):
        return nombre in self.simbolos

    def obtener(self, nombre):
        return self.simbolos.get(nombre)

    def asignar_valor(self, nombre, valor):
        if nombre in self.simbolos:
            self.simbolos[nombre]['valor'] = valor
            return True
        return False

    def __str__(self):
        if not self.lista_simbolos:
            return "  (Tabla de símbolos vacía)"
        lineas = []
        lineas.append("  ┌─────────────┬──────────────┬────────┬──────────┬────────┐")
        lineas.append("  │  Variable   │  Tipo        │  Línea │  Valor   │ Tamano │")
        lineas.append("  ├─────────────┼──────────────┼────────┼──────────┼────────┤")
        for s in self.lista_simbolos:
            nombre = s['nombre'].ljust(11)
            tipo = s['tipo'].ljust(12)
            linea = str(s['linea']).center(6)
            valor = str(s['valor'] if s['valor'] is not None else '-').ljust(8)
            tamano = str(s.get('tamano') or '-').center(6)
            lineas.append(f"  │ {nombre} │ {tipo} │ {linea} │ {valor} │ {tamano} │")
        lineas.append("  └─────────────┴──────────────┴────────┴──────────┴────────┘")
        return '\n'.join(lineas)
