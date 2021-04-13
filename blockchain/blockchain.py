import hashlib
import json
from flask import Flask, jsonify
from datetime import datetime
from json import JSONEncoder

class Domain:

    def __init__(self):
        self.domain = ''
        self.value = ''


class Transaction:

   def __init__(self, amount, fee, category, sender, receiver, last_proof, time = None):
       self.amount = amount
       self.fee = fee
       if time == None:
           self.time = datetime.now() / 1000
       self.details = { category, sender, receiver }


class Block:

    def __init__(self, id, prev_hash, nonce=None, timestamp=None):
        self.id = id
        if timestamp is None:
            self.timestamp = 1 #datetime.timestamp(datetime.now()) / 1000  # in unix seconds
        else:
            self.timestamp = timestamp        
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.data = []

    def add_in_data(self, domain):

        if type(domain) == Domain:
            self.data.append(domain)
        else:
            exit()

    def set_data(self, data):
        self.data = data

    def get_data(self, data):
        return self.data

    def find(self, key):
        1

    def hash(self):
        encoded_block = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def proof_of_work(self):
        #previous_proof = last_block.proof
        #last_hash = last_block.hash()
        ononce = self.nonce
        self.nonce = 5982000000
        check_proof = False

        while check_proof is False:
            check_proof = self.valid_proof(self)
            if check_proof is False:
                self.nonce += 1
                if self.nonce % (100000 * 60) == 0:
                    print(self.nonce)

        temp = self.nonce
        self.nonce = ononce
        return temp

    def valid_proof(self, block):
        guess = f'{block.__dict__}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:10] == "0000000000"
        #return guess_hash[:4] == "0000"

    def hash_proof(self):
        guess = f'{self.__dict__}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash

class Blockchain:

    def __init__(self):
        self.chain = []

    def find_block(self, id):
        1


if __name__ == '__main__':
    #    import pickle
    x = Block(1, 0)
    x.nonce = x.proof_of_work()
    print(x.nonce)
    print(x.hash_proof())

    #x1 = Block(2, x.hash_proof())
    #x1.nonce = x1.proof_of_work()
    #print(x1.nonce)
    #print(x1.hash_proof())


#    f = open('p.txt', 'wb')
#    pickle.dump(x, f)
