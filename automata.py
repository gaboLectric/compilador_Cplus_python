class Automata:
    def __init__(self):
        self.estado = 'inicio' # Estado inicial 

    def transicion(self, caracter):
        # Lógica para el estado inicial (primer carácter)
        if self.estado == 'inicio':
            # No números ni símbolos al inicio, pero '_' sí es válido 
            if caracter.isalpha() or caracter == '_':
                self.estado = 'valido'
            else:
                self.estado = 'invalido'
        
        # Lógica para el resto de la cadena
        elif self.estado == 'valido':
            # Aceptamos letras, números y '_'. Rechaza símbolos como $, #, /, etc.
            if caracter.isalnum() or caracter == '_':
                self.estado = 'valido' # Permanece en estado válido
            else:
                self.estado = 'invalido' # Si encuentra carácter no válido (ej. $, -) pasa a inválido
        
        # Si ya está en estado inválido, se queda ahí
        elif self.estado == 'invalido':
            pass

    def procesar_cadena(self, cadena):
        # Reiniciar el autómata para cada nueva cadena
        self.estado = 'inicio'
        for caracter in cadena:
            self.transicion(caracter)
        return self.estado == 'valido'

if __name__ == "__main__":
    lista_pruebas = [
        "variable1",       
        "_variable",      
        "1variable",      
        "var-name",       
        "var_namees",     
        "var123",
        "varName",
        "varName2",        
        "variable$"      
    ]

    print("--- Resultados del Autómata ---")
    automata = Automata()
    
    for prueba in lista_pruebas:
        es_valido = automata.procesar_cadena(prueba)
        resultado = "es un identificador válido." if es_valido else "NO es un identificador válido."
        print(f"'{prueba}' {resultado}")