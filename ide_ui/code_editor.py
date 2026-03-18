"""
Editor de código con números de línea, resaltado de línea actual,
y decoraciones visuales modernas.
"""

from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtCore import Qt, QRect, QSize, QTimer
from PySide6.QtGui import (QFont, QPainter, QColor, QTextFormat, 
                           QTextCharFormat, QSyntaxHighlighter, QTextCursor)

from ide_ui.theme import COLORS


# ═══════════════════════════════════════════════
# RESALTADOR DE SINTAXIS BÁSICO
# ═══════════════════════════════════════════════

class BasicSyntaxHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis simple para el lenguaje del compilador."""
    
    def __init__(self, document):
        super().__init__(document)
        self._rules = []
        self._setup_rules()
    
    def _setup_rules(self):
        import re
        
        # Palabras clave de tipos de dato
        kw_format = QTextCharFormat()
        kw_format.setForeground(QColor(COLORS['syn_keyword']))
        kw_format.setFontWeight(QFont.Bold)
        keywords = ['int', 'double', 'float', 'char', 'string', 'bool', 'void',
                     'main', 'if', 'else', 'while', 'for', 'do', 'switch', 'case',
                     'break', 'continue', 'return', 'cout', 'cin', 'endl',
                     'include', 'using', 'namespace', 'std', 'true', 'false']
        for kw in keywords:
            pattern = re.compile(r'\b' + kw + r'\b')
            self._rules.append((pattern, kw_format))
        
        # Números
        num_format = QTextCharFormat()
        num_format.setForeground(QColor(COLORS['syn_number']))
        self._rules.append((re.compile(r'\b\d+(\.\d+)?\b'), num_format))
        
        # Strings
        str_format = QTextCharFormat()
        str_format.setForeground(QColor(COLORS['syn_string']))
        self._rules.append((re.compile(r'"[^"]*"'), str_format))
        self._rules.append((re.compile(r"'[^']*'"), str_format))
        
        # Operadores
        op_format = QTextCharFormat()
        op_format.setForeground(QColor(COLORS['accent_orange']))
        op_format.setFontWeight(QFont.Bold)
        self._rules.append((re.compile(r'[+\-*/=<>!&|^%]'), op_format))
        
        # Paréntesis y llaves
        paren_format = QTextCharFormat()
        paren_format.setForeground(QColor(COLORS['accent_cyan']))
        self._rules.append((re.compile(r'[(){}\[\]]'), paren_format))
        
        # Comentarios (// ...)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(COLORS['syn_comment']))
        comment_format.setFontItalic(True)
        self._rules.append((re.compile(r'//.*$'), comment_format))
    
    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


# ═══════════════════════════════════════════════
# ÁREA DE NÚMEROS DE LÍNEA
# ═══════════════════════════════════════════════

class LineNumberArea(QWidget):
    """Widget que muestra los números de línea al costado del editor."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor
    
    def sizeHint(self):
        return QSize(self.codeEditor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.codeEditor.line_number_area_paint_event(event)


# ═══════════════════════════════════════════════
# EDITOR DE CÓDIGO PRINCIPAL
# ═══════════════════════════════════════════════

class CodeEditor(QPlainTextEdit):
    """
    Editor de código completo con:
    - Números de línea
    - Resaltado de línea actual
    - Resaltado de sintaxis
    - Indicador de columna/línea
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Área de números de línea
        self.line_number_area = LineNumberArea(self)
        
        # Conectar señales
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        
        # Configurar fuente
        font = QFont("JetBrains Mono", 12)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        
        # Tab size
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        
        # Resaltador de sintaxis
        self.highlighter = BasicSyntaxHighlighter(self.document())
        
        # Inicializar
        self._update_line_number_area_width(0)
        self._highlight_current_line()
    
    def line_number_area_width(self):
        """Calcula el ancho necesario para el área de números de línea."""
        digits = 1
        max_val = max(1, self.blockCount())
        while max_val >= 10:
            max_val //= 10
            digits += 1
        digits = max(digits, 3)  # Mínimo 3 dígitos de ancho
        
        space = 16 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), 
                                         self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), 
                  self.line_number_area_width(), cr.height())
        )
    
    def _highlight_current_line(self):
        """Resalta la línea actual con un fondo sutil."""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(COLORS['bg_light'])
            line_color.setAlpha(100)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def line_number_area_paint_event(self, event):
        """Pinta los números de línea."""
        painter = QPainter(self.line_number_area)
        
        # Fondo del área de números
        bg_color = QColor(COLORS['bg_dark'])
        painter.fillRect(event.rect(), bg_color)
        
        # Línea separadora sutil
        painter.setPen(QColor(COLORS['border_subtle']))
        painter.drawLine(
            self.line_number_area.width() - 1, event.rect().top(),
            self.line_number_area.width() - 1, event.rect().bottom()
        )
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        
        # Línea actual
        current_line = self.textCursor().blockNumber()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                if block_number == current_line:
                    # Línea actual: color brillante
                    painter.setPen(QColor(COLORS['text_primary']))
                    # Fondo highlight para la línea actual en el gutter
                    highlight = QColor(COLORS['bg_lighter'])
                    painter.fillRect(0, top, self.line_number_area.width() - 2, 
                                     self.fontMetrics().height(), highlight)
                    painter.setPen(QColor(COLORS['text_primary']))
                else:
                    painter.setPen(QColor(COLORS['text_muted']))
                
                painter.drawText(0, top, self.line_number_area.width() - 10,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
    
    def get_cursor_position(self):
        """Retorna (línea, columna) actual del cursor."""
        cursor = self.textCursor()
        return cursor.blockNumber() + 1, cursor.columnNumber() + 1
