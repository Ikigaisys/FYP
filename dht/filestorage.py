from kademlia.storage import IStorage
from os import path
import csv
import time

class FileStorage(IStorage):
    def __init__(self, file="kademlia.csv"):
        if not path.exists(file):
            f = open(file, "w")
            f.close()
        self.file = file

    def cull(self):
        1

    def __setitem__(self, key, value):
        if self.get(key, None) is not None:
                """spamwriter = csv.writer('temp.txt', delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                for row in spamreader:
                        if row[0] == str(key):
                                spamwriter.writerow([key.decode('utf-8'), value, time.monotonic()])
                        else: """                               
                pass

        with open(self.file, 'a', newline='') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                spamwriter.writerow([key.decode('utf-8'), value, time.monotonic()])

    def get(self, key, default=None):
        with open(self.file, 'r', newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                for row in spamreader:
                        if row[0] == str(key):
                                return row[1]
        return default

    def __getitem__(self, key):
        with open(self.file, 'r', newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
                for row in spamreader:
                        if row[0] == str(key):
                                return row[1]

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
