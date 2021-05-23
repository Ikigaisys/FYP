
class FileHashTable:

    def __init__(self, filename):
        self.filename = filename
        self.dict = {}
        with open(self.filename, 'r') as file:
            lines = file.readlines()
            for line in lines:
                key, value = line.split(',')
                key = key.replace("$", "\n")
                self.dict[key] = int(value)

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value
        with open(self.filename, 'w') as file:
            for key in self.dict:
                key = key.replace("\n", "$")
                file.write(key + ',' + str(value))
