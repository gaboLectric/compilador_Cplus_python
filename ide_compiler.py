#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          C++ Compiler IDE - Compilador Integrado                 ║
║          Gabriel Alcaraz Suárez - 8vo Semestre                   ║
╚══════════════════════════════════════════════════════════════════╝

Punto de entrada principal del IDE.
Ejecutar: python ide_compiler.py
"""

import sys
import os

# Asegurar que el directorio actual esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import Qt

from ide_ui.main_window import MainWindow
from ide_ui.theme import apply_global_theme


def main():
    # Habilitar High DPI scaling
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("C++ Compiler IDE")
    app.setApplicationVersion("1.0")

    # Cargar fuente preferida
    font_families = ["JetBrains Mono", "Fira Code", "FiraCode Nerd Font", "Cascadia Code", "Consolas", "Monospace"]
    app_font = None
    for family in font_families:
        test_font = QFont(family)
        if test_font.exactMatch():
            app_font = QFont(family, 10)
            break
    
    if app_font is None:
        app_font = QFont("Monospace", 10)
        app_font.setStyleHint(QFont.Monospace)

    app.setFont(app_font)

    # Aplicar tema global
    apply_global_theme(app)

    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
