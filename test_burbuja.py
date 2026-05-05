import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ide_ui.compiler_engine import CompilerEngine

def test_burbuja():
    engine = CompilerEngine()
    with open('burbuja.txt', 'r') as f:
        codigo = f.read()
    
    print("--- Test Case: burbuja.txt ---")
    res = engine.compilar_todo(codigo)
    for err in res['resumen']:
        print(err)

if __name__ == "__main__":
    test_burbuja()
