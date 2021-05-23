import os

class FileHashTable:

    def __init__(self, filename):
        self.filename = filename
        self.dict = {}
        if(os.path.exists(self.filename)):
            with open(self.filename, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    key, value = line.split(',')
                    key = key.replace("$", "\n")
                    try:
                        self.dict[key] = int(value)
                    except:
                        self.dict[key] = value

    def __getitem__(self, key):
        if key in self.dict:
            return self.dict[key]
        return None

    def __setitem__(self, key, value):
        self.dict[key] = value
        with open(self.filename, 'w') as file:
            for key in self.dict:
                key = key.replace("\n", "$")
                file.write(key + ',' + str(value))
