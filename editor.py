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
        

class MainWindow(QtGui.QMainWindow):
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
        self.button_group.buttonClicked.connect(lambda id: self.highlight())
        
        self.addToolBar(self.toolbar)
        
        self.central_widget = QtGui.QSplitter(QtCore.Qt.Vertical)
        
        def create_edit(title):
            e = QtGui.QTextEdit()
            e.setAcceptRichText(False)
            e.textChanged.connect(self.highlight)
            e.setLineWrapMode(QtGui.QTextEdit.NoWrap)
            p = WindowPane(title, e)
            self.central_widget.addWidget(p)
            
            return e, p
        
        self.expression_edit, self.expression_pane = create_edit('Pattern')
        self.expression_edit.setFontPointSize(11)
        self.search_text_edit, self.search_text_pane = create_edit('Search Text')
        
        self.central_widget.setSizes([100, 400])
        
        self.setCentralWidget(self.central_widget)
        
        self.highlight_enabled = True
        
    def sizeHint(self):
        return QtCore.QSize(550, 675)
        
    def set_document_html(self, html):
        self.expression_edit.textChanged.disconnect(self.highlight)
        self.search_text_edit.document().setHtml(html)
        self.expression_edit.textChanged.connect(self.highlight)
        
    def highlight(self):
        text = self.search_text_edit.document().toPlainText()
        pattern = self.expression_edit.document().toPlainText()
        
        if not pattern or not self.highlight_enabled:
            return
        
        html = '<!DOCTYPE html><html><body><div style="font-size:11pt;">'
        index = 0
        
        # Disable highlighting so that this function isn't called recursively
        # when it sets the document html
        self.highlight_enabled = False
        
        # Save the cursor position, which will get reset after we change the html
        cursor_position = self.search_text_edit.textCursor().position()
        
        try:
            for match in re.finditer(pattern, text):
                html += escape(text[index:match.start()])
                html += '<span style="background-color:#ade7a5;">' + text[match.start():match.end()] + '</span>'
                index = match.end()
                if self.button_group.checkedButton() is self.match_button:
                    break
                
            html += escape(text[index:]) + '</div></body></html>'
            self.set_document_html(html)
            
            
            cursor = self.search_text_edit.textCursor()
            cursor.setPosition(cursor_position)
            self.search_text_edit.setTextCursor(cursor)
            
        except sre_constants.error as err:
            print err
        finally:
            self.highlight_enabled = True
            
app = QtGui.QApplication(sys.argv)

window = MainWindow()

window.show()
app.exec_()

