class Domain:

    def __init__(self):
        self.domain = ''
        self.value = ''


class Block:

    def __init__(self):
        self.timestamp = 1617367633 # in unix seconds
        self.prev_hash = 'uaNlxNJnXV/Y7HdnKivClHQYTDgFtVC5h7YwyDwgDJw='
        self.nonce = 1617367633
        self.data = []

if __name__ == '__main__':
    import pickle
    x = Block()

    f = open('p.txt', 'wb')
    pickle.dump(x, f)