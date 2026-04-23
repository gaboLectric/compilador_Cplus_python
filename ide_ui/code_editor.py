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
        self.cursorPositionChanged.connect(self._highlight_matching_brackets)
        
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
    
    def _highlight_matching_brackets(self):
        """Resalta el par de brackets/paréntesis/corchetes correspondiente."""
        extra_selections = []
        cursor = self.textCursor()
        if not cursor.isNull():
            pos = cursor.position()
            text = self.toPlainText()
            
            brackets = {
                '(': ')',
                ')': '(',
                '{': '}',
                '}': '{',
                '[': ']',
                ']': '['
            }
            
            found_bracket = None
            found_pos = None
            
            # Verificar carácter antes del cursor
            if pos > 0 and pos <= len(text):
                char_before = text[pos - 1]
                if char_before in brackets:
                    found_bracket = char_before
                    found_pos = pos - 1
            
            # Si no hay bracket antes, verificar carácter después
            if found_bracket is None and pos < len(text):
                char_after = text[pos]
                if char_after in brackets:
                    found_bracket = char_after
                    found_pos = pos
            
            if found_bracket is not None:
                matching_char = brackets[found_bracket]
                match_pos = self._find_matching_bracket(text, found_pos, found_bracket, matching_char)
                
                if match_pos is not None and match_pos != found_pos:
                    # Resaltar el bracket actual
                    selection1 = QTextEdit.ExtraSelection()
                    cursor1 = QTextCursor(self.document())
                    cursor1.setPosition(found_pos)
                    cursor1.setPosition(found_pos + 1, QTextCursor.KeepAnchor)
                    selection1.cursor = cursor1
                    bracket_color = QColor(COLORS['accent_cyan'])
                    bracket_color.setAlpha(150)
                    selection1.format.setBackground(bracket_color)
                    extra_selections.append(selection1)
                    
                    # Resaltar el bracket correspondiente
                    selection2 = QTextEdit.ExtraSelection()
                    cursor2 = QTextCursor(self.document())
                    cursor2.setPosition(match_pos)
                    cursor2.setPosition(match_pos + 1, QTextCursor.KeepAnchor)
                    selection2.cursor = cursor2
                    selection2.format.setBackground(bracket_color)
                    extra_selections.append(selection2)
        
        # Primero resaltar la línea actual
        self._highlight_current_line()
        
        # Agregar selecciones de brackets
        current_selections = self.extraSelections()
        extra_selections.extend(current_selections)
        self.setExtraSelections(extra_selections)
    
    def _find_matching_bracket(self, text, start_pos, open_char, close_char):
        """Encuentra la posición del bracket correspondiente."""
        is_opening = open_char in '({['
        stack = 0
        
        if is_opening:
            # Buscar hacia adelante para encontrar el bracket de cierre
            for i in range(start_pos + 1, len(text)):
                if text[i] == open_char:
                    stack += 1
                elif text[i] == close_char:
                    if stack == 0:
                        return i
                    stack -= 1
        else:
            # Buscar hacia atrás para encontrar el bracket de apertura
            for i in range(start_pos - 1, -1, -1):
                if text[i] == open_char:
                    if stack == 0:
                        return i
                    stack -= 1
                elif text[i] == close_char:
                    stack += 1
        
        return None
