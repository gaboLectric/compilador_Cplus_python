"""
Ventana principal del IDE del compilador.
Diseño moderno con paneles, pestañas de salida diferenciadas por fase,
explorador de archivos, y barra de estado informativa.
"""

import sys
import os
import json
import time

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPlainTextEdit, QTabWidget, QToolBar, QPushButton, QLabel,
    QFileDialog, QMessageBox, QDockWidget, QTreeView,
    QFileSystemModel, QFrame, QStatusBar, QSizePolicy,
    QApplication
)
from PySide6.QtCore import Qt, QDir, QRect, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QAction, QColor, QIcon, QKeySequence, QShortcut

from ide_ui.code_editor import CodeEditor
from ide_ui.compiler_engine import CompilerEngine
from ide_ui.theme import COLORS


class MainWindow(QMainWindow):
    """
    Ventana principal del IDE - MiPython Compiler.
    
    Layout:
    ┌──────────────────────────────────────────────┐
    │  Menu Bar                                    │
    ├──────────────────────────────────────────────┤
    │  Toolbar                                     │
    ├────────┬─────────────────────────────────────┤
    │        │                                     │
    │ Explor │   Editor de Código                  │
    │  ador  │                                     │
    │        │                                     │
    │        ├─────────────────────────────────────┤
    │        │   Tabs de Salida                    │
    │        │   [Consola][Decl.][Tokens][Árbol]   │
    ├────────┴─────────────────────────────────────┤
    │  Status Bar                                  │
    └──────────────────────────────────────────────┘
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("C++ Compiler IDE")
        self.resize(1400, 900)
        self.setMinimumSize(900, 600)
        
        # Transparencia sutil de la ventana
        self.setWindowOpacity(0.97)
        
        # Estado
        self.current_file = None
        self.is_modified = False
        self.state_path = os.path.join(
            os.path.expanduser("~"), ".cpp_compiler_ide_state.json"
        )
        
        # Motor del compilador
        self.compiler = CompilerEngine()
        
        # Construir UI
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central_area()
        self._setup_file_explorer()
        self._setup_status_bar()
        self._setup_shortcuts()
        
        # Conectar modificación del editor
        self.editor.textChanged.connect(self._on_text_changed)
        
        # Cargar estado previo
        self._load_state()
        
        # Timer para auto-save del estado
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._save_state)
        self.auto_save_timer.start(30000)  # Cada 30 segundos
    
    # ═══════════════════════════════════════════════
    # SETUP DE LA INTERFAZ
    # ═══════════════════════════════════════════════
    
    def _setup_menu(self):
        """Configura la barra de menú."""
        menubar = self.menuBar()
        
        # ── Archivo ──
        file_menu = menubar.addMenu("  Archivo  ")
        
        action_new = file_menu.addAction("Nuevo")
        action_new.setShortcut(QKeySequence.New)
        action_new.triggered.connect(self.new_file)
        
        action_open = file_menu.addAction("Abrir...")
        action_open.setShortcut(QKeySequence.Open)
        action_open.triggered.connect(self.open_file)
        
        file_menu.addSeparator()
        
        action_save = file_menu.addAction("Guardar")
        action_save.setShortcut(QKeySequence.Save)
        action_save.triggered.connect(self.save_file)
        
        action_save_as = file_menu.addAction("Guardar como...")
        action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        action_save_as.triggered.connect(self.save_file_as)
        
        file_menu.addSeparator()
        
        action_exit = file_menu.addAction("Salir")
        action_exit.setShortcut(QKeySequence.Quit)
        action_exit.triggered.connect(self.close)
        
        # ── Edición ──
        edit_menu = menubar.addMenu("  Edición  ")
        
        action_undo = edit_menu.addAction("Deshacer")
        action_undo.setShortcut(QKeySequence.Undo)
        action_undo.triggered.connect(lambda: self.editor.undo())
        
        action_redo = edit_menu.addAction("Rehacer")
        action_redo.setShortcut(QKeySequence.Redo)
        action_redo.triggered.connect(lambda: self.editor.redo())
        
        edit_menu.addSeparator()
        
        action_cut = edit_menu.addAction("Cortar")
        action_cut.setShortcut(QKeySequence.Cut)
        action_cut.triggered.connect(lambda: self.editor.cut())
        
        action_copy = edit_menu.addAction("Copiar")
        action_copy.setShortcut(QKeySequence.Copy)
        action_copy.triggered.connect(lambda: self.editor.copy())
        
        action_paste = edit_menu.addAction("Pegar")
        action_paste.setShortcut(QKeySequence.Paste)
        action_paste.triggered.connect(lambda: self.editor.paste())
        
        edit_menu.addSeparator()
        
        action_select_all = edit_menu.addAction("Seleccionar todo")
        action_select_all.setShortcut(QKeySequence.SelectAll)
        action_select_all.triggered.connect(lambda: self.editor.selectAll())
        
        # ── Compilar ──
        compile_menu = menubar.addMenu("  Compilar  ")
        
        action_compile = compile_menu.addAction("Compilar todo")
        action_compile.setShortcut(QKeySequence("F6"))
        action_compile.triggered.connect(self.compile_all)
        
        action_decl = compile_menu.addAction("Solo Declaraciones")
        action_decl.setShortcut(QKeySequence("F7"))
        action_decl.triggered.connect(self.compile_declarations)
        
        action_tokens = compile_menu.addAction("Solo Tokens")
        action_tokens.setShortcut(QKeySequence("F8"))
        action_tokens.triggered.connect(self.compile_tokens)
        
        action_tree = compile_menu.addAction("Solo Árbol Sintáctico")
        action_tree.setShortcut(QKeySequence("F9"))
        action_tree.triggered.connect(self.compile_tree)
        
        # ── Ver ──
        view_menu = menubar.addMenu("  Ver  ")
        
        action_clear = view_menu.addAction("Limpiar salida")
        action_clear.triggered.connect(self.clear_output)
        
        action_zoom_in = view_menu.addAction("Acercar")
        action_zoom_in.setShortcut(QKeySequence("Ctrl+="))
        action_zoom_in.triggered.connect(lambda: self.editor.zoomIn(1))
        
        action_zoom_out = view_menu.addAction("Alejar")
        action_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        action_zoom_out.triggered.connect(lambda: self.editor.zoomOut(1))
        
        # ── Ayuda ──
        help_menu = menubar.addMenu("  Ayuda  ")
        
        action_about = help_menu.addAction("Acerca de")
        action_about.triggered.connect(self._show_about)
    
    def _setup_toolbar(self):
        """Configura la barra de herramientas superior."""
        self.toolbar = QToolBar("Herramientas")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(self.toolbar)
        
        # ── Botones de archivo ──
        btn_new = QPushButton("  ✦  Nuevo")
        btn_new.setToolTip("Crear nuevo archivo (Ctrl+N)")
        btn_new.clicked.connect(self.new_file)
        self.toolbar.addWidget(btn_new)
        
        btn_open = QPushButton("  📂  Abrir")
        btn_open.setToolTip("Abrir archivo (Ctrl+O)")
        btn_open.clicked.connect(self.open_file)
        self.toolbar.addWidget(btn_open)
        
        btn_save = QPushButton("  💾  Guardar")
        btn_save.setToolTip("Guardar archivo (Ctrl+S)")
        btn_save.clicked.connect(self.save_file)
        self.toolbar.addWidget(btn_save)
        
        self.toolbar.addSeparator()
        
        # ── Botones de compilación ──
        btn_compile = QPushButton("  ▶  COMPILAR  (F6)")
        btn_compile.setObjectName("btnCompile")
        btn_compile.setToolTip("Ejecutar todas las fases del compilador (F6)")
        btn_compile.clicked.connect(self.compile_all)
        self.toolbar.addWidget(btn_compile)
        
        btn_run = QPushButton("  ⚡  EJECUTAR  (F5)")
        btn_run.setObjectName("btnRun")
        btn_run.setToolTip("Ejecutar el programa (F5)")
        btn_run.clicked.connect(self.run_code)
        self.toolbar.addWidget(btn_run)
        
        self.toolbar.addSeparator()
        
        btn_tree = QPushButton("  🌳  ÁRBOL  (F9)")
        btn_tree.setObjectName("btnTree")
        btn_tree.setToolTip("Generar árbol sintáctico (F9)")
        btn_tree.clicked.connect(self.compile_tree)
        self.toolbar.addWidget(btn_tree)
        
        btn_clear = QPushButton("  🗑  LIMPIAR")
        btn_clear.setObjectName("btnClear")
        btn_clear.setToolTip("Limpiar todos los paneles de salida")
        btn_clear.clicked.connect(self.clear_output)
        self.toolbar.addWidget(btn_clear)
        
        # Espaciador flexible
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Indicador de posición del cursor
        self.cursor_label = QLabel("  Ln 1, Col 1  ")
        self.cursor_label.setObjectName("statusInfo")
        self.cursor_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 11px;
            padding: 4px 12px;
            background-color: {COLORS['bg_lighter']};
            border-radius: 4px;
        """)
        self.toolbar.addWidget(self.cursor_label)
    
    def _setup_central_area(self):
        """Configura el área central con el editor y los paneles de salida."""
        
        # Splitter vertical: Editor arriba, Output abajo
        central_splitter = QSplitter(Qt.Vertical)
        central_splitter.setHandleWidth(3)
        
        # ── Editor de código ──
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        # Tabs del editor
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setDocumentMode(True)
        self.editor_tabs.setTabsClosable(False)
        
        self.editor = CodeEditor()
        self.editor.setPlaceholderText(
            "// Escribe tu código C++ aquí...\n"
            "// Ejemplo:\n"
            "//   int main() {\n"
            "//     int x;\n"
            "//     double y;\n"
            "//     string nombre;\n"
            "//     x = 10;\n"
            "//   }\n"
            "//\n"
            "// Presiona F6 para compilar"
        )
        self.editor.cursorPositionChanged.connect(self._update_cursor_position)
        
        self.editor_tabs.addTab(self.editor, "  Sin título  ")
        editor_layout.addWidget(self.editor_tabs)
        
        # ── Panel de salida (tabs) ──
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)
        
        # Barra de título para el panel de output
        output_header = QFrame()
        output_header.setFixedHeight(28)
        output_header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border-top: 2px solid {COLORS['accent_blue']};
                border-bottom: 1px solid {COLORS['border_subtle']};
            }}
        """)
        header_layout = QHBoxLayout(output_header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        output_title = QLabel("SALIDA DEL COMPILADOR")
        output_title.setObjectName("sectionLabel")
        output_title.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        header_layout.addWidget(output_title)
        header_layout.addStretch()
        
        self.error_indicator = QLabel("")
        self.error_indicator.setObjectName("statusOk")
        header_layout.addWidget(self.error_indicator)
        
        output_layout.addWidget(output_header)
        
        # Tabs de salida
        self.output_tabs = QTabWidget()
        self.output_tabs.setDocumentMode(True)
        
        # Consola general
        self.console = QPlainTextEdit()
        self.console.setObjectName("outputConsole")
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("La salida del compilador aparecerá aquí...")
        self.output_tabs.addTab(self.console, "  📋  Consola  ")
        
        # Declaraciones
        self.output_declarations = QPlainTextEdit()
        self.output_declarations.setObjectName("outputDeclarations")
        self.output_declarations.setReadOnly(True)
        self.output_declarations.setPlaceholderText("Análisis de declaraciones...")
        self.output_tabs.addTab(self.output_declarations, "  📝  Declaraciones  ")
        
        # Tokens
        self.output_tokens = QPlainTextEdit()
        self.output_tokens.setObjectName("outputTokens")
        self.output_tokens.setReadOnly(True)
        self.output_tokens.setPlaceholderText("Tokenización de expresiones...")
        self.output_tabs.addTab(self.output_tokens, "  🔤  Tokens  ")
        
        # Árbol sintáctico
        self.output_tree = QPlainTextEdit()
        self.output_tree.setObjectName("outputTree")
        self.output_tree.setReadOnly(True)
        self.output_tree.setPlaceholderText("Árboles sintácticos...")
        self.output_tabs.addTab(self.output_tree, "  🌳  Árbol  ")
        
        # Errores
        self.output_errors = QPlainTextEdit()
        self.output_errors.setObjectName("outputErrors")
        self.output_errors.setReadOnly(True)
        self.output_errors.setPlaceholderText("Sin errores")
        self.output_tabs.addTab(self.output_errors, "  ⚠  Errores  ")
        
        output_layout.addWidget(self.output_tabs)
        
        # Configurar el splitter
        central_splitter.addWidget(editor_container)
        central_splitter.addWidget(output_container)
        central_splitter.setSizes([550, 350])
        central_splitter.setStretchFactor(0, 3)
        central_splitter.setStretchFactor(1, 1)
        
        self.setCentralWidget(central_splitter)
    
    def _setup_file_explorer(self):
        """Configura el panel de explorador de archivos."""
        dock = QDockWidget("  📁  EXPLORADOR", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        explorer_widget = QWidget()
        explorer_layout = QVBoxLayout(explorer_widget)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        explorer_layout.setSpacing(0)
        
        # Modelo de sistema de archivos
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.currentPath())
        self.file_model.setNameFilters(["*.txt", "*.py", "*.cpp", "*.h", "*.c", "*.go"])
        self.file_model.setNameFilterDisables(False)
        
        # TreeView
        self.tree = QTreeView()
        self.tree.setModel(self.file_model)
        
        # Usar el directorio del proyecto como raíz
        project_dir = os.path.dirname(os.path.abspath(__file__))
        self.tree.setRootIndex(self.file_model.index(project_dir))
        
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        
        # Ocultar columnas extra
        for i in range(1, 4):
            self.tree.hideColumn(i)
        
        # Conectar doble click para abrir archivo
        self.tree.doubleClicked.connect(self._on_tree_double_click)
        
        explorer_layout.addWidget(self.tree)
        
        dock.setWidget(explorer_widget)
        dock.setMinimumWidth(200)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
    
    def _setup_status_bar(self):
        """Configura la barra de estado inferior."""
        status = QStatusBar(self)
        self.setStatusBar(status)
        
        # Indicadores permanentes
        self.status_file_label = QLabel("  Sin archivo  ")
        self.status_file_label.setObjectName("statusFile")
        
        self.status_lang_label = QLabel("  C++  ")
        self.status_lang_label.setObjectName("statusInfo")
        
        self.status_encoding = QLabel("  UTF-8  ")
        self.status_encoding.setObjectName("statusInfo")
        
        self.status_compile_label = QLabel("  Listo  ")
        self.status_compile_label.setObjectName("statusOk")
        
        status.addPermanentWidget(self.status_file_label)
        status.addPermanentWidget(self._create_separator())
        status.addPermanentWidget(self.status_lang_label)
        status.addPermanentWidget(self._create_separator())
        status.addPermanentWidget(self.status_encoding)
        status.addPermanentWidget(self._create_separator())
        status.addPermanentWidget(self.status_compile_label)
        
        status.showMessage("C++ Compiler IDE — Listo")
    
    def _create_separator(self):
        """Crea un separador vertical para la barra de estado."""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {COLORS['border_subtle']};")
        sep.setFixedWidth(1)
        sep.setFixedHeight(16)
        return sep
    
    def _setup_shortcuts(self):
        """Configura atajos de teclado adicionales."""
        # F5 para ejecutar
        shortcut_run = QShortcut(QKeySequence("F5"), self)
        shortcut_run.activated.connect(self.run_code)
    
    # ═══════════════════════════════════════════════
    # ACCIONES DE COMPILACIÓN
    # ═══════════════════════════════════════════════
    
    def compile_all(self):
        """Ejecuta todas las fases del compilador."""
        codigo = self.editor.toPlainText()
        
        if not codigo.strip():
            self._show_in_console("⚠ El editor está vacío. Escribe código para compilar.")
            return
        
        start_time = time.time()
        
        self._show_in_console("Compilando todas las fases...")
        self._show_in_console("")
        
        resultado = self.compiler.compilar_todo(codigo)
        
        elapsed = time.time() - start_time
        
        # Mostrar declaraciones
        self.output_declarations.setPlainText(
            '\n'.join(resultado['declaraciones']['resultados'])
        )
        
        # Mostrar tokens
        self.output_tokens.setPlainText(
            '\n'.join(resultado['expresiones']['resultados'])
        )
        
        # Mostrar árbol
        self.output_tree.setPlainText(
            '\n'.join(resultado['arboles']['resultados'])
        )
        
        # Mostrar resumen en consola
        resumen_lines = resultado['resumen']
        all_output = []
        all_output.append(f"Compilación completada en {elapsed*1000:.1f}ms")
        all_output.append("")
        all_output.extend(resumen_lines)
        
        self._show_in_console('\n'.join(all_output))
        
        # Errores
        total_err = resultado['total_errores']
        total_warn = resultado['total_warnings']
        
        if total_err > 0 or total_warn > 0:
            error_lines = []
            for err in self.compiler.last_errors:
                error_lines.append(f"✗ ERROR: {err}")
            for warn in self.compiler.last_warnings:
                error_lines.append(f"⚠ ADVERTENCIA: {warn}")
            self.output_errors.setPlainText('\n'.join(error_lines))
            self.error_indicator.setText(f"  ✗ {total_err} errores, {total_warn} advertencias  ")
            self.error_indicator.setObjectName("statusError")
            self.error_indicator.setStyleSheet(f"color: {COLORS['accent_red']}; font-weight: bold; font-size: 11px;")
            self.status_compile_label.setText(f"  ✗ {total_err} error(es)  ")
            self.status_compile_label.setStyleSheet(f"color: {COLORS['accent_red']}; font-weight: bold;")
        else:
            self.output_errors.setPlainText("✓ Sin errores")
            self.error_indicator.setText("  ✓ Sin errores  ")
            self.error_indicator.setObjectName("statusOk")
            self.error_indicator.setStyleSheet(f"color: {COLORS['accent_green']}; font-weight: bold; font-size: 11px;")
            self.status_compile_label.setText("  ✓ OK  ")
            self.status_compile_label.setStyleSheet(f"color: {COLORS['accent_green']}; font-weight: bold;")
        
        self.statusBar().showMessage(f"Compilación completada — {elapsed*1000:.1f}ms")
    
    def compile_declarations(self):
        """Solo ejecuta el análisis de declaraciones."""
        codigo = self.editor.toPlainText()
        if not codigo.strip():
            self._show_in_console("⚠ El editor está vacío.")
            return
        
        self.compiler.reset()
        resultado = self.compiler.analizar_declaraciones(codigo)
        self.output_declarations.setPlainText('\n'.join(resultado['resultados']))
        self.output_tabs.setCurrentIndex(1)  # Ir a pestaña Declaraciones
        self.statusBar().showMessage("Análisis de declaraciones completado")
    
    def compile_tokens(self):
        """Solo ejecuta el análisis léxico de expresiones."""
        codigo = self.editor.toPlainText()
        if not codigo.strip():
            self._show_in_console("⚠ El editor está vacío.")
            return
        
        self.compiler.reset()
        resultado = self.compiler.analizar_expresiones(codigo)
        self.output_tokens.setPlainText('\n'.join(resultado['resultados']))
        self.output_tabs.setCurrentIndex(2)  # Ir a pestaña Tokens
        self.statusBar().showMessage("Análisis léxico completado")
    
    def compile_tree(self):
        """Solo genera los árboles sintácticos."""
        codigo = self.editor.toPlainText()
        if not codigo.strip():
            self._show_in_console("⚠ El editor está vacío.")
            return
        
        self.compiler.reset()
        resultado = self.compiler.generar_arboles(codigo)
        self.output_tree.setPlainText('\n'.join(resultado['resultados']))
        self.output_tabs.setCurrentIndex(3)  # Ir a pestaña Árbol
        self.statusBar().showMessage("Árboles sintácticos generados")
    
    def run_code(self):
        """Simula la ejecución del código."""
        self._show_in_console("⚡ Ejecutando programa...")
        self._show_in_console("   (Funcionalidad de ejecución en desarrollo)")
        self.statusBar().showMessage("Ejecución simulada")
    
    def clear_output(self):
        """Limpia todos los paneles de salida."""
        self.console.clear()
        self.output_declarations.clear()
        self.output_tokens.clear()
        self.output_tree.clear()
        self.output_errors.clear()
        self.error_indicator.setText("")
        self.status_compile_label.setText("  Listo  ")
        self.status_compile_label.setStyleSheet(f"color: {COLORS['accent_green']}; font-weight: bold;")
        self.statusBar().showMessage("Salida limpiada")
    
    # ═══════════════════════════════════════════════
    # MANEJO DE ARCHIVOS
    # ═══════════════════════════════════════════════
    
    def new_file(self):
        """Crea un nuevo archivo."""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Guardar cambios",
                "¿Deseas guardar los cambios antes de crear un nuevo archivo?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        
        self.editor.clear()
        self.current_file = None
        self.is_modified = False
        self.setWindowTitle("C++ Compiler IDE")
        self.editor_tabs.setTabText(0, "  Sin título  ")
        self.status_file_label.setText("  Sin archivo  ")
        self.clear_output()
        self._save_state()
    
    def open_file(self):
        """Abre un archivo desde disco."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo", "",
            "Archivos de código (*.txt *.py *.cpp *.h *.c *.go);;"
            "Todos los archivos (*)"
        )
        if file_path:
            self._load_file(file_path, remember=True)
    
    def save_file(self):
        """Guarda el archivo actual."""
        if not self.current_file:
            self.save_file_as()
        else:
            self._write_to_file(self.current_file)
    
    def save_file_as(self):
        """Guarda como un nuevo archivo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo como", "",
            "Archivos de texto (*.txt);;Archivos Python (*.py);;"
            "Archivos C++ (*.cpp);;Todos los archivos (*)"
        )
        if file_path:
            self._write_to_file(file_path)
    
    def _load_file(self, file_path, remember=False):
        """Carga un archivo en el editor."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.editor.setPlainText(content)
            self.current_file = file_path
            self.is_modified = False
            
            nombre = os.path.basename(file_path)
            self.setWindowTitle(f"C++ Compiler IDE — {nombre}")
            self.editor_tabs.setTabText(0, f"  {nombre}  ")
            self.status_file_label.setText(f"  {nombre}  ")
            self.statusBar().showMessage(f"Abierto: {file_path}")
            
            if remember:
                self._save_state()
                
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo.\n{exc}")
    
    def _write_to_file(self, file_path):
        """Escribe el contenido del editor a disco."""
        try:
            content = self.editor.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.current_file = file_path
            self.is_modified = False
            
            nombre = os.path.basename(file_path)
            self.setWindowTitle(f"C++ Compiler IDE — {nombre}")
            self.editor_tabs.setTabText(0, f"  {nombre}  ")
            self.status_file_label.setText(f"  {nombre}  ")
            self.statusBar().showMessage(f"Guardado: {file_path}")
            
            self._save_state()
            
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"No se pudo guardar.\n{exc}")
    
    # ═══════════════════════════════════════════════
    # ESTADO PERSISTENTE
    # ═══════════════════════════════════════════════
    
    def _save_state(self):
        """Guarda el estado para la próxima sesión."""
        try:
            state = {
                "last_file": self.current_file,
                "window_geometry": {
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.width(),
                    "height": self.height(),
                },
            }
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except OSError:
            pass
    
    def _load_state(self):
        """Restaura el estado de la sesión anterior."""
        if not os.path.exists(self.state_path):
            return
        
        try:
            with open(self.state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Restaurar archivo
            last_file = state.get("last_file")
            if last_file and os.path.exists(last_file):
                self._load_file(last_file, remember=False)
            
            # Restaurar geometría
            geo = state.get("window_geometry", {})
            if geo:
                self.setGeometry(
                    geo.get("x", 100), geo.get("y", 100),
                    geo.get("width", 1400), geo.get("height", 900)
                )
                
        except (OSError, json.JSONDecodeError):
            pass
    
    # ═══════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════
    
    def _show_in_console(self, text):
        """Agrega texto a la consola de salida."""
        self.console.appendPlainText(text)
    
    def _on_text_changed(self):
        """Llamado cuando el texto del editor cambia."""
        self.is_modified = True
        current_title = self.windowTitle()
        if not current_title.endswith(" •"):
            self.setWindowTitle(current_title + " •")
    
    def _update_cursor_position(self):
        """Actualiza el indicador de posición del cursor."""
        line, col = self.editor.get_cursor_position()
        self.cursor_label.setText(f"  Ln {line}, Col {col}  ")
    
    def _on_tree_double_click(self, index):
        """Maneja el doble click en el explorador de archivos."""
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self._load_file(file_path, remember=True)
    
    def _show_about(self):
        """Muestra el diálogo 'Acerca de'."""
        QMessageBox.about(
            self,
            "Acerca de C++ Compiler IDE",
            "<h2>C++ Compiler IDE</h2>"
            "<p><b>Compilador de C++ Integrado</b></p>"
            "<p>Versión 1.0</p>"
            "<hr>"
            "<p>Tipos soportados: int, double, float, char, string, bool</p>"
            "<p>Fases implementadas:</p>"
            "<ul>"
            "<li>Autómata para identificadores</li>"
            "<li>Tokenizador léxico C++</li>"
            "<li>Análisis de declaraciones (con ;)</li>"
            "<li>Tabla de símbolos</li>"
            "<li>Análisis de expresiones</li>"
            "<li>Árbol sintáctico</li>"
            "</ul>"
            "<hr>"
            "<p>Gabriel Alcaraz Suárez<br>"
            "8vo Semestre — Compiladores</p>"
        )
    
    def closeEvent(self, event):
        """Intercepta el cierre para guardar estado."""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Guardar cambios",
                "Tienes cambios sin guardar. ¿Deseas guardar antes de salir?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        self._save_state()
        event.accept()
