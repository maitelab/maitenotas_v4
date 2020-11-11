"""
Application: Maitenotas
Made by Taksan Tong
https://github.com/maitelab/maitenotas_v4

Functions related to read/write data """
import sqlite3
from typing import Optional
from cryptography.fernet import Fernet
from crypto import encryptTextToData, decryptDataToText
import traceback
import text_labels

# ***************** SQL
SQL_CREATE_BOOK_TABLE = """
CREATE TABLE IF NOT EXISTS book (
    id integer PRIMARY KEY AUTOINCREMENT,
    book_name blob NOT NULL,
    book_text blob NOT NULL
); """

SQL_CREATE_PAGE_TABLE = """
CREATE TABLE IF NOT EXISTS page (
    book_id integer,
    id integer PRIMARY KEY AUTOINCREMENT,
    page_name blob NOT NULL,
    page_text blob NOT NULL
); """

SQL_INSERT_BOOK = """
INSERT INTO book(book_name, book_text)
VALUES(?,?)"""
    

# ****************** DATABASE NAME and main operations
DATABASE_NAME = r"maitenotas.data"

def createConnection(dbfile) -> Optional[sqlite3.Connection]:
    """ create a database connection to the SQLite database
        specified by dbfile
    :param dbfile: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(dbfile)
        return conn
    except:
        traceback.print_exc()
    return conn


def createTable(conn: sqlite3.Connection, create_tablesql: str) -> None:
    """ create a table from the create_tablesql statement"""
    try:
        cursor = conn.cursor()
        cursor.execute(create_tablesql)
    except:
        traceback.print_exc()

def updatePageText(user_key: Fernet, page_id: int, new_text: str) -> None:
    """update text of page row"""
    SQL_UPDATE_PAGE_TEXT = """
    update page
    set page_text=?
    where id=?
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encryptTextToData(new_text, user_key)
            datas = (encrypted_data, page_id,)
            cur.execute(SQL_UPDATE_PAGE_TEXT, datas)
            conn.commit()
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def updateBookText(user_key: Fernet, book_id: int, new_text: str) -> None:
    """update text of book row"""
    SQL_UPDATE_BOOK_TEXT = """
    update book
    set book_text=?
    where id=?
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encryptTextToData(new_text, user_key)
            datas = (encrypted_data, book_id,)
            cur.execute(SQL_UPDATE_BOOK_TEXT, datas)
            conn.commit()
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


def updatePageName(user_key: Fernet, page_id: int, new_name: str) -> None:
    """update book name"""
    sql = """
    update page set page_name=? where id=?
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encryptTextToData(new_name, user_key)
            data_forsql = (encrypted_data, page_id)
            cur.execute(sql, data_forsql)
            conn.commit()
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            
def updateBookName(user_key: Fernet, book_id: int, new_name: str) -> None:
    """update book name"""
    sql = """
    update book set book_name=? where id=?
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encryptTextToData(new_name, user_key)
            data_forsql = (encrypted_data, book_id)
            cur.execute(sql, data_forsql)
            conn.commit()
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


def deletePage(page_id: int) -> None:
    """delete page"""
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute("delete from page where id=?", (page_id,))
            conn.commit()
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def deleteBook(book_id: int) -> None:
    """delete book"""
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            # we need to first delete the pages of the book
            cur.execute("delete from page where book_id=?", (book_id,))
            # now delete the book
            cur.execute("delete from book where id=?", (book_id,))
            conn.commit()
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def getBookName(user_key: Fernet, book_id: int) -> str:
    """read book name"""
    SQL_READ_BOOK_NAME = """
    select book_name
    from book
    where id=?
    """
    book_name = ""
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_BOOK_NAME, (book_id,))
            record = cur.fetchall()
            for row in record:
                # read columns
                book_name = decryptDataToText(row[0], user_key)
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    return book_name


def getBookText(user_key: Fernet, book_id) -> str:
    """get book text"""
    result_text = ""
    SQL_READ_BOOK_TEXT = """
    select book_text from book where id=?
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_BOOK_TEXT, (book_id,))
            record = cur.fetchall()
            for row in record:
                # read columns
                result_text = decryptDataToText(row[0], user_key)
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    return result_text

def getPageText(user_key: Fernet, page_id) -> str:
    """get page text"""
    result_text = ""
    SQL_READ_PAGE_TEXT = """
    select page_text from page where id=?
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_PAGE_TEXT, (page_id,))
            record = cur.fetchall()
            for row in record:
                # read columns
                result_text = decryptDataToText(row[0], user_key)
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    return result_text

# take the second element for sort
def take_second(elem):
    return elem[1]

def getBooks(user_key: Fernet) -> list:
    """read books from database"""
    leaf_list = []
    SQL_READ_ALL_JOURNAL = """
    select id, book_name 
    from book
    where id >= 2
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_ALL_JOURNAL)
            record = cur.fetchall()
            for row in record:
                # read columns
                book_id = row[0]
                book_name = decryptDataToText(row[1], user_key)
                leaf_element = book_id, book_name
                leaf_list.append(leaf_element)
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    return sorted(leaf_list, key=take_second) # sort by the second element (book name)

def getPagesOfBook(user_key: Fernet, bookId: int) -> list:
    """read pages of a book"""
    leaf_list = []
    SQL_READ_ALL_JOURNAL = """
    select id, page_name
    from page
    where book_id = ?
    """
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_ALL_JOURNAL, (bookId,))
            record = cur.fetchall()
            for row in record:
                # read columns
                page_id = row[0]
                page_name = decryptDataToText(row[1], user_key)
                leaf_element = page_id, page_name
                leaf_list.append(leaf_element)
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    return sorted(leaf_list, key=take_second) # sort by the second element (page name)


def createBook(user_key: Fernet, book_name: str, book_text) -> int:
    """create book"""
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encryptTextToData(book_name, user_key)
            encrypted_data2 = encryptTextToData(book_text, user_key)
            data_tobe_inserted = (encrypted_data, encrypted_data2,)
            cur.execute(SQL_INSERT_BOOK, data_tobe_inserted)
            conn.commit()
            last_row_id = cur.lastrowid
            return last_row_id
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    return 0


def createPage(user_key: Fernet, book_id: int, page_name: str, page_text: str) -> int:
    """create journal"""
    SQL_INSERT_PAGE = """
    INSERT INTO page(book_id,page_name,page_text)
    VALUES(?,?,?)"""
    try:
        conn = createConnection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data_journal_name = encryptTextToData(page_name, user_key)
            encrypted_data_journal_text = encryptTextToData(page_text, user_key)
            data_tobe_inserted = (book_id, encrypted_data_journal_name,
                                  encrypted_data_journal_text,)
            cur.execute(SQL_INSERT_PAGE, data_tobe_inserted)
            conn.commit()
            last_row_id = cur.lastrowid
            return last_row_id
    except:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    return 0


def createDatabase(user_key: Fernet, user_password: str) -> bool:
    """create database"""
    try:
        # create a database connection
        conn = createConnection(DATABASE_NAME)
        # create tables
        if conn is not None:
            # create tables
            createTable(conn, SQL_CREATE_BOOK_TABLE)
            createTable(conn, SQL_CREATE_PAGE_TABLE)
            # insert first book (this is a special book not visible to the user)
            cur = conn.cursor()
            encrypted_data = encryptTextToData(user_password, user_key)
            data_tobe_inserted = (encrypted_data, "",)
            cur.execute(SQL_INSERT_BOOK, data_tobe_inserted)
            conn.commit()
        else:
            return False
    except:
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()
    return True


def verifyDatabasePassword(user_key: Fernet, user_password: str) -> bool:
    """verify db pass"""
    try:
        # create a database connection
        conn = createConnection(DATABASE_NAME)
        # create tables
        if conn is not None:
            # read book name from the first record
            cur = conn.cursor()
            cur.execute("SELECT book_name from book where id = ?", (1,))
            record = cur.fetchall()
            for row in record:
                # get encrypted blob
                encrypted_data = row[0]
                # do decrypt and validate
                decrypted_text = decryptDataToText(encrypted_data, user_key)
                if decrypted_text != user_password:
                    print("stored password does not match with provided pass")
                    return False
        else:
            return False
    except:
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()
    return True
