import os
import sqlite3
from sqlite3 import Error

class SQLite:
    def __init__(self):
        1

    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        self.con = None
        self.db_file = db_file
        try:
            self.con = sqlite3.connect(db_file, check_same_thread=False)
        except Error as e:
            print(e)
        finally:
            1

    def close_connection(self):
        if self.con:
            self.con.close()

    def execute(self, sql, params = None):
        cur = self.con.cursor()
        try:
            if params is None:
                cur.execute(sql)
            else:
                cur.execute(sql, params)
            self.con.commit()
        except sqlite3.OperationalError as msg:
            print(msg)
        val = cur.lastrowid  
        cur.close()
        return val   

    def fetchone(self, sql, params=()):
        cur = db.con.cursor()
        val = db.con.execute(sql, params).fetchone()
        cur.close()
        return val

db = SQLite()
db.create_connection('DB.db')
db.con.row_factory = sqlite3.Row

class SQLiteHashTable:
    def __init__(self, tablename, type = 'str'):
        self.tablename = tablename
        self.type = type
        db.execute("CREATE TABLE IF NOT EXISTS " + tablename + " (key TEXT PRIMARY KEY, value TEXT);")
    
    def __getitem__(self, key):
        cursor = db.con.cursor()
        value = cursor.execute("SELECT value from " + self.tablename + " where key = ?", (key,)).fetchone()
        if value is not None:
            value = value['value']
            if self.type == 'float':
                value = float(value)
            elif self.type == 'int':
                value = int(value)
        cursor.close()
        return value

    def __setitem__(self, key, value):
        if self.__getitem__(key) is None:
            db.execute("insert into " + self.tablename + " (key, value) values (?, ?)", (key, value))
        else:
            db.execute("update " + self.tablename + " set value=? where key=?", (key, value))
    
    def fetchall(self):
        cursor = db.con.cursor()
        result = []
        values = cursor.execute("SELECT key,value from " + self.tablename)
        for value in values:
            key = value['key']
            value = value['value']
            if self.type == 'float':
                value = float(value)
            elif self.type == 'int':
                value = int(value)
            result.append(key,value)
        cursor.close()
        return result

class FileHashTable:

    def __init__(self, filename):
        self.filename = filename
        self.dict = {}
        if(os.path.exists(self.filename)):
            with open(self.filename, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    key, value = line.split(',')
                    value = value.replace("\n", "")
                    try:
                        self.dict[key] = float(value)
                    except:
                        self.dict[key] = value

    def __getitem__(self, key):
        if key in self.dict:
            return self.dict[key]
        return None

    def __setitem__(self, key, value):
        self.dict[key] = value
        with open(self.filename, 'w') as file:
            for _key, _value in self.dict.items():
                file.write(_key + ',' + str(_value) + "\n")
