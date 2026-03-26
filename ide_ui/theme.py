"""
Tema visual oscuro premium con transparencias y gradientes para el IDE.
Inspirado en diseño glassmorphism moderno.
"""


# ═══════════════════════════════════════════════
# PALETA DE COLORES
# ═══════════════════════════════════════════════

COLORS = {
    # Fondos principales
    "bg_darkest":       "#0d1117",
    "bg_dark":          "#161b22",
    "bg_medium":        "#1c2128",
    "bg_light":         "#21262d",
    "bg_lighter":       "#2d333b",
    "bg_hover":         "#363d47",

    # Bordes
    "border_subtle":    "#30363d",
    "border_medium":    "#444c56",
    "border_accent":    "#3b82f6",

    # Texto
    "text_primary":     "#e6edf3",
    "text_secondary":   "#8b949e",
    "text_muted":       "#6e7681",
    "text_accent":      "#58a6ff",

    # Acentos
    "accent_blue":      "#3b82f6",
    "accent_blue_glow": "#2563eb",
    "accent_purple":    "#8b5cf6",
    "accent_green":     "#22c55e",
    "accent_green_dark":"#16a34a",
    "accent_orange":    "#f59e0b",
    "accent_red":       "#ef4444",
    "accent_cyan":      "#06b6d4",

    # Syntax highlighting preview colors
    "syn_keyword":      "#ff7b72",
    "syn_string":       "#a5d6ff",
    "syn_number":       "#79c0ff",
    "syn_comment":      "#8b949e",
    "syn_type":         "#d2a8ff",
    "syn_function":     "#d2a8ff",

    # Status bar
    "status_bg":        "#1a1e2e",
    "status_accent":    "#3b82f6",

    # Tab
    "tab_active_border":"#3b82f6",
    "tab_inactive":     "#1c2128",

    # Selection
    "selection":        "rgba(56, 130, 246, 0.25)",
}


def apply_global_theme(app):
    """Aplica el stylesheet global premium a toda la aplicación."""
    
    c = COLORS
    
    qss = f"""
    /* ═══════════════════════════════════════════════ */
    /* RESET Y BASE GLOBAL                            */
    /* ═══════════════════════════════════════════════ */
    
    * {{
        outline: none;
    }}

    QMainWindow {{
        background-color: {c['bg_darkest']};
        color: {c['text_primary']};
    }}
    
    QMainWindow::separator {{
        background-color: {c['border_subtle']};
        width: 1px;
        height: 1px;
    }}
    
    QMainWindow::separator:hover {{
        background-color: {c['accent_blue']};
    }}

    /* ═══════════════════════════════════════════════ */
    /* BARRA DE MENÚ                                  */
    /* ═══════════════════════════════════════════════ */
    
    QMenuBar {{
        background-color: {c['bg_dark']};
        color: {c['text_secondary']};
        border-bottom: 1px solid {c['border_subtle']};
        padding: 2px 4px;
        font-size: 12px;
    }}
    
    QMenuBar::item {{
        padding: 5px 10px;
        border-radius: 4px;
        margin: 1px 2px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {c['bg_lighter']};
        color: {c['text_primary']};
    }}
    
    QMenu {{
        background-color: {c['bg_medium']};
        color: {c['text_primary']};
        border: 1px solid {c['border_medium']};
        border-radius: 8px;
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 6px 28px 6px 12px;
        border-radius: 4px;
        margin: 1px 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {c['accent_blue']};
        color: white;
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {c['border_subtle']};
        margin: 4px 8px;
    }}

    /* ═══════════════════════════════════════════════ */
    /* TOOLBAR PRINCIPAL                              */
    /* ═══════════════════════════════════════════════ */
    
    QToolBar {{
        background-color: {c['bg_dark']};
        border: none;
        border-bottom: 1px solid {c['border_subtle']};
        padding: 4px 8px;
        spacing: 6px;
    }}
    
    QToolBar::separator {{
        width: 1px;
        background-color: {c['border_subtle']};
        margin: 4px 6px;
    }}

    /* ═══════════════════════════════════════════════ */
    /* BOTONES                                        */
    /* ═══════════════════════════════════════════════ */
    
    QPushButton {{
        color: {c['text_primary']};
        background-color: {c['bg_lighter']};
        border: 1px solid {c['border_subtle']};
        padding: 6px 16px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 12px;
    }}
    
    QPushButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['border_medium']};
    }}
    
    QPushButton:pressed {{
        background-color: {c['bg_light']};
    }}
    
    /* Botón Compilar - Azul */
    QPushButton#btnCompile {{
        background-color: {c['accent_blue']};
        border: none;
        color: white;
        font-weight: bold;
    }}
    QPushButton#btnCompile:hover {{
        background-color: {c['accent_blue_glow']};
    }}
    
    /* Botón Ejecutar - Verde */
    QPushButton#btnRun {{
        background-color: {c['accent_green']};
        border: none;
        color: white;
        font-weight: bold;
    }}
    QPushButton#btnRun:hover {{
        background-color: {c['accent_green_dark']};
    }}
    
    /* Botón Limpiar - Naranja */
    QPushButton#btnClear {{
        background-color: {c['accent_orange']};
        border: none;
        color: white;
        font-weight: bold;
    }}
    QPushButton#btnClear:hover {{
        background-color: #d97706;
    }}

    /* Botón Árbol - Púrpura */
    QPushButton#btnTree {{
        background-color: {c['accent_purple']};
        border: none;
        color: white;
        font-weight: bold;
    }}
    QPushButton#btnTree:hover {{
        background-color: #7c3aed;
    }}

    /* ═══════════════════════════════════════════════ */
    /* EDITORES DE TEXTO                              */
    /* ═══════════════════════════════════════════════ */
    
    QPlainTextEdit {{
        background-color: {c['bg_darkest']};
        color: {c['text_primary']};
        border: none;
        selection-background-color: rgba(56, 130, 246, 0.3);
        selection-color: {c['text_primary']};
        padding: 4px;
    }}

    /* ═══════════════════════════════════════════════ */
    /* DOCK WIDGETS (Paneles laterales/inferiores)    */
    /* ═══════════════════════════════════════════════ */
    
    QDockWidget {{
        color: {c['text_secondary']};
        font-weight: bold;
        font-size: 11px;
        titlebar-close-icon: none;
    }}
    
    QDockWidget::title {{
        background-color: {c['bg_dark']};
        color: {c['text_secondary']};
        padding: 8px 12px;
        border-bottom: 1px solid {c['border_subtle']};
        font-size: 11px;
        text-transform: uppercase;
    }}

    /* ═══════════════════════════════════════════════ */
    /* TABS                                           */
    /* ═══════════════════════════════════════════════ */
    
    QTabWidget::pane {{
        border: none;
        background-color: {c['bg_darkest']};
    }}
    
    QTabBar {{
        background-color: {c['bg_dark']};
    }}
    
    QTabBar::tab {{
        background-color: {c['tab_inactive']};
        color: {c['text_muted']};
        padding: 8px 16px;
        border: none;
        border-right: 1px solid {c['border_subtle']};
        font-size: 12px;
        min-width: 100px;
    }}
    
    QTabBar::tab:hover {{
        background-color: {c['bg_light']};
        color: {c['text_secondary']};
    }}
    
    QTabBar::tab:selected {{
        background-color: {c['bg_darkest']};
        color: {c['text_primary']};
        border-top: 2px solid {c['tab_active_border']};
        border-right: 1px solid {c['border_subtle']};
    }}

    /* ═══════════════════════════════════════════════ */
    /* TREE VIEW (Explorador de archivos)             */
    /* ═══════════════════════════════════════════════ */
    
    QTreeView {{
        background-color: {c['bg_dark']};
        color: {c['text_secondary']};
        border: none;
        outline: none;
        font-size: 12px;
    }}
    
    QTreeView::item {{
        padding: 4px 6px;
        border-radius: 4px;
        margin: 1px 4px;
    }}
    
    QTreeView::item:hover {{
        background-color: {c['bg_lighter']};
        color: {c['text_primary']};
    }}
    
    QTreeView::item:selected {{
        background-color: rgba(56, 130, 246, 0.2);
        color: {c['text_primary']};
    }}
    
    QTreeView::branch {{
        background-color: {c['bg_dark']};
    }}
    
    QHeaderView::section {{
        background-color: {c['bg_dark']};
        color: {c['text_secondary']};
        border: none;
        padding: 4px;
    }}

    /* ═══════════════════════════════════════════════ */
    /* SCROLLBARS                                     */
    /* ═══════════════════════════════════════════════ */
    
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {c['bg_lighter']};
        border-radius: 5px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {c['border_medium']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {c['bg_lighter']};
        border-radius: 5px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {c['border_medium']};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}

    /* ═══════════════════════════════════════════════ */
    /* STATUS BAR                                     */
    /* ═══════════════════════════════════════════════ */
    
    QStatusBar {{
        background-color: {c['status_bg']};
        color: {c['text_secondary']};
        font-size: 11px;
        border-top: 1px solid {c['border_subtle']};
        padding: 2px 8px;
    }}
    
    QStatusBar QLabel {{
        color: {c['text_secondary']};
        padding: 0 8px;
    }}

    /* ═══════════════════════════════════════════════ */
    /* TOOLTIPS                                       */
    /* ═══════════════════════════════════════════════ */
    
    QToolTip {{
        background-color: {c['bg_medium']};
        color: {c['text_primary']};
        border: 1px solid {c['border_medium']};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 11px;
    }}

    /* ═══════════════════════════════════════════════ */
    /* SPLITTER                                       */
    /* ═══════════════════════════════════════════════ */
    
    QSplitter::handle {{
        background-color: {c['border_subtle']};
    }}
    
    QSplitter::handle:hover {{
        background-color: {c['accent_blue']};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}

    /* ═══════════════════════════════════════════════ */
    /* INPUT & DIALOG                                 */
    /* ═══════════════════════════════════════════════ */
    
    QLineEdit {{
        background-color: {c['bg_light']};
        color: {c['text_primary']};
        border: 1px solid {c['border_subtle']};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
        selection-background-color: rgba(56, 130, 246, 0.3);
    }}
    
    QLineEdit:focus {{
        border-color: {c['accent_blue']};
    }}
    
    QDialog {{
        background-color: {c['bg_dark']};
        color: {c['text_primary']};
    }}

    QMessageBox {{
        background-color: {c['bg_dark']};
        color: {c['text_primary']};
    }}
    
    QMessageBox QLabel {{
        color: {c['text_primary']};
    }}

    /* ═══════════════════════════════════════════════ */
    /* CLASES CUSTOM                                   */
    /* ═══════════════════════════════════════════════ */
    
    /* Panel de output con borde superior gradiente */
    QPlainTextEdit#outputConsole {{
        background-color: {c['bg_darkest']};
        color: {c['accent_green']};
        font-family: "JetBrains Mono", "Fira Code", Monospace;
        font-size: 14px;
        padding: 8px;
    }}
    
    QPlainTextEdit#outputDeclarations {{
        background-color: {c['bg_darkest']};
        color: {c['accent_cyan']};
        font-family: "JetBrains Mono", "Fira Code", Monospace;
        font-size: 14px;
        padding: 8px;
    }}
    
    QPlainTextEdit#outputTokens {{
        background-color: {c['bg_darkest']};
        color: {c['accent_orange']};
        font-family: "JetBrains Mono", "Fira Code", Monospace;
        font-size: 14px;
        padding: 8px;
    }}
    
    QPlainTextEdit#outputTree {{
        background-color: {c['bg_darkest']};
        color: {c['accent_purple']};
        font-family: "JetBrains Mono", "Fira Code", Monospace;
        font-size: 14px;
        padding: 8px;
    }}

    QPlainTextEdit#outputErrors {{
        background-color: {c['bg_darkest']};
        color: {c['accent_red']};
        font-family: "JetBrains Mono", "Fira Code", Monospace;
        font-size: 14px;
        padding: 8px;
    }}

    /* Etiquetas de sección */
    QLabel#sectionLabel {{
        color: {c['text_secondary']};
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 4px 8px;
    }}

    QLabel#statusFile {{
        color: {c['text_accent']};
        font-weight: bold;
    }}

    QLabel#statusInfo {{
        color: {c['text_secondary']};
    }}

    QLabel#statusError {{
        color: {c['accent_red']};
        font-weight: bold;
    }}

    QLabel#statusOk {{
        color: {c['accent_green']};
        font-weight: bold;
    }}
    """
    
    app.setStyleSheet(qss)
