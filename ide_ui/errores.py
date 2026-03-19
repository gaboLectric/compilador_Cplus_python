def obtener_error_sintactico(codigo):
    mensajes = {
        1: "ESPERABA UN ;",
        2: "ESPERABA UNA }",
        3: "ESPERABA UN =",
        4: "ESPERABA UN )",
        5: "ESPERABA UN IDENTIFICADOR",
        6: "INSTRUCCION DESCONOCIDA",
        7: "ESPERABA UNA CONSTANTE",
        8: "ESPERABA MAIN",
        9: "ESPERABA UNA {",
        10: "ORDEN INCORRECTO O TIPO SIN VARIABLE",
        11: "TIPO SIN VARIABLE"
    }
    return f"ERROR SINTÁCTICO {codigo}: {mensajes.get(codigo, 'NO DOCUMENTADO')}"

def obtener_error_semantico(codigo, extra=""):
    mensajes = {
        1: "VARIABLE NO DECLARADA",
        2: "VARIABLE YA DECLARADA",
        3: "AMBIGÜEDAD",
        4: "INCOMPATIBILIDAD DE TIPOS",
        5: "USO INCORRECTO DE CONTROL DE FLUJO",
        6: "ESTRUCTURA DE CICLO NO COHERENTE"
    }
    base = f"ERROR SEMÁNTICO {codigo}: {mensajes.get(codigo, 'NO DOCUMENTADO')}"
    if extra:
        base += f" ({extra})"
    return base
