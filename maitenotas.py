"""
Application: Maitenotas version 4
Made by Taksan Tong
https://github.com/maitelab/maitenotas_v4

Main launcher of the application
"""
from os import path
import os
import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QAction, QMessageBox,  QWidget, QHBoxLayout, QInputDialog, QLineEdit, QListWidgetItem,\
    QListWidget, QVBoxLayout
from PySide2.QtGui import QIcon

from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtCore import QUrl
from PySide2.QtCore import QObject, Slot
from PySide2.QtWebChannel import QWebChannel
import text_labels
from crypto import generateUserKey
from storage import verifyDatabasePassword, createDatabase, createBook,   getBooks, createPage,\
    getPagesOfBook, getBookText, getPageText, updatePageText, updateBookText, deleteBook, deletePage


class Handler(QObject):
    """Handler for JS-Python communication"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = "hello world"

    @Slot(str)
    def receiveTextFromWebGUI(self, inputText):
        """Receive data from Javascript"""
        self.text = inputText

    def getCurrentText(self):
        """Return current value of text"""
        return self.text


class MaiteListItem(QListWidgetItem):
    
    def __init__(self, itemId=0, itemText=''):
        super().__init__()
        self.itemId = itemId
        self.setText(itemText)


class MaiteBody(QWidget):
    """Main display body"""

    def __init__(self, userKey):
        super().__init__(None)
        self.userKey = userKey
      
        # get list of books
        listBooks = getBooks(self.userKey)
        listBooksWidget = QListWidget()
        listBooksWidget.setWindowTitle(text_labels.LIST_BOOKS_TITLE)
                
        for lbook in listBooks:
            bookId = lbook[0]
            bookName = lbook[1]
            listBooksWidget.addItem(MaiteListItem(bookId, bookName))

        self.selectedBookId = -1 # no book selected yet
        self.selectedPageId = -1 # none selected at the beginning

        self.listBooksWidget = listBooksWidget
        
        # get list of pages of the first book
        listPagesWidget = QListWidget()
        listPagesWidget.setWindowTitle(text_labels.LIST_BOOKS_TITLE)
                      
        self.listPagesWidget = listPagesWidget
        
        self.listPagesWidget.itemClicked.connect(self.listPagesClicked)
        self.listBooksWidget.itemClicked.connect(self.listBooksClicked)
        
        # left view has both lists
        self.vlay = QVBoxLayout()
        self.vlay.addWidget(self.listBooksWidget,40)
        self.vlay.addWidget(self.listPagesWidget,60)
        
        # main horizontal view
        hlay = QHBoxLayout()

        # left pane
        hlay.addLayout(self.vlay, 25)

        # right pane
        self.webEngineView = QWebEngineView()
        current_path = os.getcwd()
        fileLocation = current_path + "/codemirror_ui.html"
        print(fileLocation)
        url = QUrl.fromLocalFile(fileLocation)

        self.webPage = self.webEngineView.page()

        # Set up backend communication via web channel
        self.handler = Handler()
        self.channel = QWebChannel()
        self.channel.registerObject("handler", self.handler)

        self.webPage.setWebChannel(self.channel)

        self.webEngineView.load(url)
        self.webEngineView.show()
        hlay.addWidget(self.webEngineView, 75)

        self.setLayout(hlay)

    def loadBookAndChildren(self):
        self.selectedPageId = -1 # no page selected
        bookText = getBookText(self.userKey, self.selectedBookId)
        newText = bookText.replace("\n", "\\n").replace("\'","\\'")
        js = f"setText('{newText}');"      
        self.webPage.runJavaScript(js)        
        
        # reload pages list
        listPages = getPagesOfBook(self.userKey, self.selectedBookId)
        self.listPagesWidget.clear()
               
        for lp in listPages:
            pageId = lp[0]
            pageName = lp[1]
            self.listPagesWidget.addItem(MaiteListItem(pageId, pageName))

    def listBooksClicked(self, mitem):
        self.saveCurrentTextOnScreen()
        # load book text
        self.selectedBookId = mitem.itemId
        print(f"clicked book id = {self.selectedBookId}")
        self.loadBookAndChildren()

    def displayTextInEditor(self):
        pageText = getPageText(self.userKey, self.selectedPageId)
        newText = pageText.replace("\n", "\\n").replace("\'","\\'")
        js = f"setText('{newText}');"      
        self.webPage.runJavaScript(js)
                
    def listPagesClicked(self, mitem):
        self.saveCurrentTextOnScreen()
        self.selectedPageId = mitem.itemId
        self.displayTextInEditor()
        
    def saveCurrentTextOnScreen(self):
        # invoke javascript function to read text from web ui component
        currentTextOnScreen = self.handler.getCurrentText()
        # update the text in database
        if self.selectedPageId >= 1:
            # text belongs to a page
            updatePageText(self.userKey, self.selectedPageId, currentTextOnScreen)
        else:
            if self.selectedBookId >= 1:
                # text belongs to a book
                updateBookText(self.userKey, self.selectedBookId, currentTextOnScreen)
                
    def deleteBook(self):
        if self.selectedBookId >= 1:
            selectedBooks = self.listBooksWidget.selectedItems()
            bookIdToDelete = selectedBooks[0].itemId
            deleteBook(bookIdToDelete)
            rowId = self.listBooksWidget.row(selectedBooks[0]) 
            self.listBooksWidget.takeItem(rowId)
            selectedBooks = self.listBooksWidget.selectedItems()
            self.selectedBookId = selectedBooks[0].itemId 
            self.loadBookAndChildren()

    def addBook(self):
        text1, okPressed1 = QInputDialog.getText(self, text_labels.MESSAGE_BOX_TITLE,text_labels.NEW_BOOK_NAME, QLineEdit.Normal, "")
        if okPressed1 and len(text1) > 0:
            # add new book to database
            newBookId = createBook(self.userKey,text1,text_labels.SAMPLE_BOOK_TEXT)
            createPage(self.userKey, newBookId, text_labels.SAMPLE_PAGE_NAME, text_labels.SAMPLE_PAGE_TEXT)
            
            # add new book to UI
            self.listBooksWidget.addItem(MaiteListItem(newBookId, text1))
            
    def deletePage(self):
        if self.selectedPageId >= 1:
            selectedPages = self.listPagesWidget.selectedItems()
            pageIdToDelete = selectedPages[0].itemId
            deletePage(pageIdToDelete)
            rowId = self.listPagesWidget.row(selectedPages[0]) 
            self.listPagesWidget.takeItem(rowId)
            # redraw text editor because a new page got automatically selected in UI
            selectedPages = self.listPagesWidget.selectedItems()
            self.selectedPageId = selectedPages[0].itemId 
            self.displayTextInEditor()

    def addPage(self):
        if self.selectedBookId >= 1:
            text1, okPressed1 = QInputDialog.getText(self, text_labels.MESSAGE_BOX_TITLE,text_labels.NEW_PAGE_NAME, QLineEdit.Normal, "")
            if okPressed1 and len(text1) > 0:
                # add new page to database
                newPageId = createPage(self.userKey, self.selectedBookId, text1, text_labels.SAMPLE_PAGE_TEXT)
                # add new book to UI
                self.listPagesWidget.addItem(MaiteListItem(newPageId, text1))
            
class Notepad(QMainWindow):
    """Main Window to hold all other widgets and menu"""

    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 800)
        self.setWindowTitle('Maitenotas v4')

        # verify if database exists
        if path.exists("maitenotas.data"):
            # ask for diary password
            text1, okPressed1 = QInputDialog.getText(self, text_labels.OPENING_DIARY,text_labels.ENTER_PASSWORD, QLineEdit.Password, "")
            if okPressed1 and len(text1) > 0:
                # verify password
                self.userKey = generateUserKey(text1)
                databaseAccess = verifyDatabasePassword(self.userKey, text1)
                if databaseAccess == False:
                    QMessageBox.about(
                        self,
                        text_labels.ERROR_READING_DATA,
                        text_labels.INVALID_PASSWORD)                        
                    quit()                    
            else:
                quit()           
        else:
            # create new default database
            text1, okPressed1 = QInputDialog.getText(self, text_labels.CREATING_DIARY,text_labels.DEFINE_PASSWORD, QLineEdit.Password, "")
            if okPressed1 and len(text1) > 0:
                text2, okPressed2 = QInputDialog.getText(self, text_labels.CREATING_DIARY,text_labels.CONFIRM_PASSWORD, QLineEdit.Password, "")
                if okPressed2 and len(text2) > 0:
                    if text1 != text2:
                        QMessageBox.about(
                            self,
                            text_labels.ERROR_READING_DATA,
                            text_labels.PASSWORDS_DO_NOT_MATCH)                        
                        quit()
                    else:
                        # create new database
                        self.userKey = generateUserKey(text1)
                        databaseAccess = createDatabase(self.userKey, text1)
                        if databaseAccess == False:
                            QMessageBox.about(
                                self,
                                text_labels.ERROR_READING_DATA,
                                text_labels.ERROR_READING_DATA)                        
                            quit()
                            
                        # create initial sample data
                        
                        # create sample book 1
                        book1Name=text_labels.SAMPLE_BOOK_NAME+" 1"
                        book1Text=text_labels.SAMPLE_BOOK_TEXT+" (" + book1Name +")"
                        bookId1 = createBook(self.userKey, book1Name, book1Text)      
                        # create sample page 1 for book 1
                        p1Name = text_labels.SAMPLE_PAGE_NAME+" 1"
                        p1Text = text_labels.SAMPLE_PAGE_TEXT +" (" + p1Name +")"
                        createPage(self.userKey, bookId1, p1Name, p1Text)
                        # create sample page 2 for book 1
                        p2Name = text_labels.SAMPLE_PAGE_NAME+" 2"
                        p2Text = text_labels.SAMPLE_PAGE_TEXT +" (" + p2Name +")"
                        createPage(self.userKey, bookId1, p2Name, p2Text)

                        # create sample book 2
                        book2Name=text_labels.SAMPLE_BOOK_NAME+" 2"
                        book2Text=text_labels.SAMPLE_BOOK_TEXT+" (" + book2Name +")"
                        bookId2 = createBook(self.userKey, book2Name, book2Text)      
                        # create sample page 1 for book 2
                        p1Name = text_labels.SAMPLE_PAGE_NAME+" 1"
                        p1Text = text_labels.SAMPLE_PAGE_TEXT +" (" + p1Name +")"
                        createPage(self.userKey, bookId2, p1Name, p1Text)
                        # create sample page 2 for book 2
                        p2Name = text_labels.SAMPLE_PAGE_NAME+" 2"
                        p2Text = text_labels.SAMPLE_PAGE_TEXT +" (" + p2Name +")"
                        createPage(self.userKey, bookId2, p2Name, p2Text)
                        # create sample page 3 for book 2
                        p3Name = text_labels.SAMPLE_PAGE_NAME+" 3"
                        p3Text = text_labels.SAMPLE_PAGE_TEXT +" (" + p3Name +")"
                        createPage(self.userKey, bookId2, p3Name, p3Text)                                                                        
                else:
                    quit()
            else:
                quit()    

        # main view
        self.mainBody = MaiteBody(self.userKey)
        self.setCentralWidget(self.mainBody)

        self.setApplicationMenu()
        # self.showMaximized()             
        
        self.show()

    def setApplicationMenu(self):
        """
        Create menu for the application
        """
        # Create menubar
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)
                
        # menu file
        menuItem_addBook = QAction(QIcon('dot.png'), text_labels.MENU_TEXT_ADD_BOOK, self)
        menuItem_addBook.setShortcut('Ctrl+T')
        menuItem_addBook.triggered.connect(self.addBook)

        menuItem_deletebook = QAction(QIcon('dot.png'),text_labels.MENU_TEXT_DELETE_BOOK, self)
        menuItem_deletebook.setShortcut('Ctrl+G')
        menuItem_deletebook.triggered.connect(self.deleteBook)

        menuItem_exit = QAction(QIcon('dot.png'),text_labels.MENU_TEXT_EXIT, self)
        menuItem_exit.setShortcut('Ctrl+Q')
        menuItem_exit.triggered.connect(self.saveCurrentTextOnScreen)

        menuFile = menu_bar.addMenu(text_labels.MENU_TEXT_FILE)
        menuFile.addAction(menuItem_addBook)
        menuFile.addAction(menuItem_deletebook)
        menuFile.addAction(menuItem_exit)
        
        # menu Page
        menuItem_addPage = QAction(QIcon('dot.png'), text_labels.MENU_TEXT_ADD_PAGE, self)
        menuItem_addPage.setShortcut('Ctrl+Y')
        menuItem_addPage.triggered.connect(self.addPage)

        menuItem_deletePage = QAction(QIcon('dot.png'), text_labels.MENU_TEXT_DELETE_PAGE, self)
        menuItem_deletePage.setShortcut('Ctrl+H')
        menuItem_deletePage.triggered.connect(self.deletePage)
               
        menuPage = menu_bar.addMenu(text_labels.MENU_TEXT_PAGE)
        menuPage.addAction(menuItem_addPage)
        menuPage.addAction(menuItem_deletePage)
        
        # menu help
        about_act = QAction(text_labels.MENU_TEXT_ABOUT, self)
        about_act.triggered.connect(self.aboutDialog)

        menuSystem = menu_bar.addMenu(text_labels.MENU_TEXT_SYSTEM)
        menuSystem.addAction(about_act)

    def saveCurrentTextOnScreen(self):
        self.mainBody.saveCurrentTextOnScreen()
        quit()
        
    def addBook(self):
        self.mainBody.addBook()
    
    def deleteBook(self):
        self.mainBody.deleteBook()
         
    def addPage(self):
        self.mainBody.addPage()
    
    def deletePage(self):
        self.mainBody.deletePage()
               
    def aboutDialog(self):
        """
        Display information about program dialog box
        """
        QMessageBox.about(
            self,
            text_labels.MESSAGE_BOX_TITLE,
            text_labels.MESSAGE_BOX)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, text_labels.MESSAGE_BOX_TITLE, text_labels.ARE_YOU_SURE_YOU_WANT_TO_CLOSE,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            self.mainBody.saveCurrentTextOnScreen()
            print('Window closed')
        else:
            event.ignore()

# Run program
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Notepad()
    sys.exit(app.exec_())
