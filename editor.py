import re
import sre_constants
import sys
import cgi
from PySide import QtCore, QtGui

def escape(text):
    return cgi.escape(text).replace('\n', '<br />')

class WindowPane(QtGui.QFrame):
    def __init__(self, title, widget):
        super(WindowPane, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        
        self.label = QtGui.QLabel(title)
        self.widget = widget
        
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.widget)
        self.setLayout(self.layout)
        
class MatchView(QtGui.QTreeView):
    def __init__(self):
        super(MatchView, self).__init__()
        
        #self.setUniformRowHeights(True)
        
        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)
        
        # Call clear so the model initially has labels 
        self.clear()
        
        self.row_count = 0
        
    def clear(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Group', 'Span', 'Contents'])
    
    def add_match(self, match):
        self.model.appendRow([QtGui.QStandardItem(text) for text in ('Match %i' % self.model.rowCount(), '%i-%i' % match.span(), match.group(0))])
        
        # There should be a better way to get the last row
        row = self.model.invisibleRootItem().child(self.model.rowCount() - 1)
            
        if match.groups():
            start = match.start()
            for i, group in enumerate(match.groups()):
                row.appendRow([QtGui.QStandardItem(text) for text in ('Group %i' % i, '%i-%i' % (start, start + len(group)), group)])
                start += len(group)
                
        self.setExpanded(row.index(), True)

class MainWindow(QtGui.QMainWindow):
    HTML_OPEN = '<!DOCTYPE html><html><body><div style="font-size:10pt;font-family:Courier, monospace">'
    HTML_CLOSE = '</div></body></html>'
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        #create the top toolbar
        self.toolbar = QtGui.QToolBar()
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        
        self.button_group = QtGui.QButtonGroup()
        
        def create_button(name):
            b = QtGui.QPushButton(name)
            b.setCheckable(True)
            self.button_group.addButton(b)
            self.toolbar.addWidget(b)
            return b
        
        self.match_button = create_button('Match')
        self.match_all_button = create_button('Match All')
        
        self.match_button.setChecked(True)
        self.button_group.buttonClicked.connect(lambda id: self.highlight_search_text())
        
        self.addToolBar(self.toolbar)
        
        self.central_widget = QtGui.QSplitter(QtCore.Qt.Vertical)
        
        def create_edit(title):
            e = QtGui.QTextEdit()
            e.setAcceptRichText(False)
            e.textChanged.connect(self.highlight_search_text)
            e.setLineWrapMode(QtGui.QTextEdit.NoWrap)
            p = WindowPane(title, e)
            self.central_widget.addWidget(p)
            
            return e, p
        
        self.expression_edit, self.expression_pane = create_edit('Pattern')
        self.expression_edit.textChanged.connect(self.highlight_expression)
        self.search_text_edit, self.search_text_pane = create_edit('Search Text')
        
        self.match_view = MatchView()
        self.match_pane = WindowPane('Match results', self.match_view)
        self.central_widget.addWidget(self.match_pane)
        
        self.central_widget.setSizes([100, 400, 200])
        self.setCentralWidget(self.central_widget)
        
        self.setWindowTitle('Regex Editor')
        
    def sizeHint(self):
        return QtCore.QSize(550, 675)
        
    def highlight_search_text(self):
        self.match_view.clear()
        
        text = self.search_text_edit.document().toPlainText()
        pattern = self.expression_edit.document().toPlainText()
        
        if not pattern:
            return
        
        html = self.HTML_OPEN
        index = 0
        
        # Save the cursor position, which will get reset after we change the html
        cursor_position = self.search_text_edit.textCursor().position()
        
        try:
            for match in re.finditer(pattern, text):
                self.match_view.add_match(match)
                
                html += escape(text[index:match.start()])
                html += '<span style="background-color:#ade7a5;">' + text[match.start():match.end()] + '</span>'
                index = match.end()
                if self.button_group.checkedButton() is self.match_button:
                    break
                
            html += escape(text[index:]) + self.HTML_CLOSE
            
            # disconnect signals before we setHtml so that this function isn't called recursively
            self.search_text_edit.textChanged.disconnect(self.highlight_search_text)
            self.search_text_edit.document().setHtml(html)
            self.search_text_edit.textChanged.connect(self.highlight_search_text)
            
            cursor = self.search_text_edit.textCursor()
            cursor.setPosition(cursor_position)
            self.search_text_edit.setTextCursor(cursor)
            
        except sre_constants.error as err:
            print err
            
    def highlight_expression(self):
        parens = '()'
        braces = '{}[]'
        operators = '?:.|+*'
        character_classes = 'wWbdDsSAZ'
        
        styles = {
            'cc':'color:#b22222;',
            'esc':'color:#008b8b;',
            'paren':'color:#c54b78;',
            'brace':'color:#871f78;',
            'operator':'color:#0000ff;'
        }
        
        # Save the cursor position, which will get reset after we change the html
        cursor_position = self.expression_edit.textCursor().position()
        
        def style_text(style, text):
            return '<span style="%s">%s</span>' % (styles[style], escape(text))
        
        escaped = False
        trailing_slash = False
        html = self.HTML_OPEN
        for char in self.expression_edit.toPlainText():
            if char == '\\':
                if escaped:
                    html += style_text('esc', '\\\\')
                    escaped = False
                else:
                    escaped = True
            else:
                if escaped:
                    if char in character_classes:
                        html += style_text('cc', '\\' + char)
                    else:
                        html += style_text('esc', '\\' + char)
                    escaped = False
                else:
                    if char in parens:
                        html += style_text('paren', char)
                    elif char in braces:
                        html += style_text('brace', char)
                    elif char in operators:
                        html += style_text('operator', char)
                    else:
                        html += escape(char)
                trailing_slash = False
        # handle a \ being entered at the end of a line
        if escaped:
            html += style_text('esc', char)
            trailing_slash = True
                        
        html += self.HTML_CLOSE
        
        # disconnect signals before we setHtml so that this function isn't called recursively
        self.expression_edit.textChanged.disconnect(self.highlight_search_text)
        self.expression_edit.textChanged.disconnect(self.highlight_expression)
        self.expression_edit.document().setHtml(html)
        self.expression_edit.textChanged.connect(self.highlight_search_text)
        self.expression_edit.textChanged.connect(self.highlight_expression)
            
        cursor = self.expression_edit.textCursor()
        cursor.setPosition(cursor_position)
        self.expression_edit.setTextCursor(cursor)
        
        
            
app = QtGui.QApplication(sys.argv)

window = MainWindow()

window.show()
app.exec_()

