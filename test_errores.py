import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ide_ui.compiler_engine import CompilerEngine

def test_errores():
    engine = CompilerEngine()
    with open('burbuja_con_errores.txt', 'r') as f:
        codigo = f.read()
    
    print("--- Test Case: burbuja_con_errores.txt ---")
    res = engine.compilar_todo(codigo)
    print("\n--- RESUMEN ---")
    for line in res['resumen']:
        print(line)
        
    print("\n--- DETALLE DECLARACIONES ---")
    for line in res['declaraciones']['resultados']:
        print(line)

if __name__ == "__main__":
    test_errores()
