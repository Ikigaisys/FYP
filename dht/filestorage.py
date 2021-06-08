from kademlia.storage import IStorage
from os import path
import os
import csv
import time
from DataController import SQLiteHashTable

class FileStorage(IStorage):
    def __init__(self, file="dht_data"):
        self.data = SQLiteHashTable(file)

    def cull(self):
        1

    def __setitem__(self, key, value):
        try:
            key = key.decode('utf-8')
        except:
            pass
        self.data[key] = value

    def get(self, key, default=None):
        try:
            key = key.decode('utf-8')
        except:
            pass
        val = self.data[key]
        if val is not None:
            return val
        return default

    def __getitem__(self, key):
        try:
            key = key.decode('utf-8')
        except:
            pass
        val = self.data[key]
        if val is not None:
            return val

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
