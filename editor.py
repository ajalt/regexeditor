import re
import sre_constants
import sys 
from PySide import QtCore, QtGui


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
        
        self.central_widget = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.expression_edit = QtGui.QTextEdit()
        self.expression_edit.setAcceptRichText(False)
        self.expression_edit.textChanged.connect(self.highlight)
        self.expression_pane = WindowPane('Pattern', self.expression_edit)
        self.search_text_edit = QtGui.QTextEdit()
        self.search_text_edit.setAcceptRichText(False)
        self.search_text_edit.textChanged.connect(self.highlight)
        self.search_text_pane = WindowPane('Search Text', self.search_text_edit)
        
        self.central_widget.addWidget(self.expression_pane)
        self.central_widget.addWidget(self.search_text_pane)
        
        
        self.setCentralWidget(self.central_widget)

    def highlight(self):
        #for match in re.finditer(self.expression_edit.toPlainText(), self.search_text_edit.toPlainText()):
        
        pattern = self.expression_edit.document().toPlainText()
        text = self.search_text_edit.document().toPlainText()
        try:
            match = re.search(pattern, text)
        except sre_constants.error as err:
            pass
        else:
            if match:
                self.search_text_edit.document().setHtml(self.highlight_range(text, match.start(), match.end()))
            
    def highlight_range(self, html, start, stop):
        return html[:start] + '<span style="background-color:#62e55f;">' + html[start:stop] + "</span>" + html[stop:]
        
app = QtGui.QApplication(sys.argv)

window = MainWindow()

window.show()
app.exec_()

