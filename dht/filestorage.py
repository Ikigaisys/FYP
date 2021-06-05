from kademlia.storage import IStorage
from os import path
import os
import csv
import time
from DataController import SQLiteHashTable

class FileStorage(IStorage):
    def __init__(self, file="kademlia"):
#        if not path.exists(file):
#            f = open(file, "w")
#            f.close()
#        self.file = file
        self.data = SQLiteHashTable(file)

    def cull(self):
        1

    def __setitem__(self, key, value):
        try:
            key = key.decode('utf-8')
        except:
            pass
        self.data[key] = value
        """if self.get(key, None) is not None:
                with open(self.file+'temp.txt', 'w', newline='') as abc:
                    spamwriter = csv.writer(abc, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                    with open(self.file, 'r', newline='') as original:
                        spamreader = csv.reader(original, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                        for row in spamreader:
                                if row[0] == str(key):
                                        try:
                                            key = key.decode('utf-8')
                                        except:
                                            pass
                                        spamwriter.writerow([key, value, time.monotonic()])
                                else:
                                        spamwriter.writerow(row)
                os.remove(self.file)
                os.rename(self.file+'temp.txt', self.file)
                return
                
        with open(self.file, 'a', newline='') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                try:
                    key = key.decode('utf-8')
                except:
                    pass
                spamwriter.writerow([key, value, time.monotonic()])"""

    def get(self, key, default=None):
        try:
            key = key.decode('utf-8')
        except:
            pass
        val = self.data[key]
        if val is not None:
            return val
        """with open(self.file, 'r', newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                for row in spamreader:
                        if row[0] == str(key):
                                return row[1]"""
        return default

    def __getitem__(self, key):
        try:
            key = key.decode('utf-8')
        except:
            pass
        val = self.data[key]
        if val is not None:
            return val
        """with open(self.file, 'r', newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                for row in spamreader:
                        if row[0] == str(key):
                                return row[1]"""

    def iter_older_than(self, seconds_old):
        min_birthday = time.monotonic() - seconds_old
        ikeys = list()
        ivalues = list()
        #with open(self.file, 'r', newline='') as csvfile:
        #        spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        #        for row in spamreader:
        #                if min_birthday >= row[2]:
        #                        ikeys.append(row[0].encode())
        #                        ivalues.append(row[1])
        return zip(ikeys, ivalues)

    def __iter__(self):
        self.cull()
        ikeys = list()
        ivalues = list()
        #with open(self.file, 'r', newline='') as csvfile:
        #        spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        #        for row in spamreader:
        #                ikeys.append(row[0].encode())
        #                ivalues.append(row[1])
        return zip(ikeys, ivalues)
