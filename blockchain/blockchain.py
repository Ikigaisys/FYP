import hashlib
import json
import os
from flask import Flask, jsonify
from datetime import datetime
from json import JSONEncoder
from .encryption import Signatures

class Key:

    def __init__(self, private_key = None, public_key = None):
        sig = Signatures()
        if private_key is None or public_key is None:
            keys = sig.generate_key()
            self.private_key = keys[0]
            self.public_key = keys[1]
        else:
            keys = sig.string_to_key(private_key.encode(), public_key.encode())
            self.private_key = keys[0]
            self.public_key = keys[1]

    def to_string(self):
        sig = Signatures()
        return sig.key_to_string(self.private_key, self.public_key)

f1 = open('pvk.txt','r')
f2 = open('pbk.txt','r')
key = Key(f1.read(), f2.read())
key_string = key.to_string()
f1.close()
f2.close()

class Accounts:

    def __init__(self):
        self.dict = {}
        with open('accounts.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                key, value = line.split(',')
                key = key.replace("$", "\n").encode()
                self.dict[key] = int(value)

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value
        with open('accounts.txt', 'w') as file:
            for key in self.dict:
                key = key.decode('utf-8').replace("\n", "$")
                file.write(key + ',' + str(value))

accounts = Accounts()

class Domain:

    def __init__(self):
        self.domain = ''
        self.value = ''


class Transaction:

    def __init__(self, amount, fee, category, sender, receiver, time = None):
        self.amount = amount
        self.fee = fee
        if time == None:
            self.time = datetime.now() / 1000
        self.details = { 'category': category, 'sender': sender, 'receiver': receiver }
        self.signature = None

    def validate(self):
        if accounts[self.details['sender']] - self.fee - self.amount > 0:
            return True
        return False

    def sign(self, private_key):
        sig = Signatures()
        self.signature = sig.sign(private_key, json.dumps(self.__dict__, sort_keys=True))

    def verify(self):
        sig = Signatures()
        public_key = sig.string_to_key(None, self.details['sender'])
        temp = self.signature
        self.signature = None
        temp2 = sig.verify(public_key, json.dumps(self.__dict__, sort_keys=True), temp)
        self.signature = temp
        return temp2


class Block:

    def __init__(self, id, prev_hash, miner=None, timestamp=None, nonce=None):
        self.id = id
        if timestamp is None:
            self.timestamp = datetime.timestamp(datetime.now()) / 1000  # in unix seconds
        else:
            self.timestamp = timestamp        
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.miner = miner
        self.data = []

    def add_transaction(self, tx):
        self.data.append(tx)

    def get_transactions(self):
        return self.data

    def find_transaction(self, key):
        pass

    def hash(self):
        encoded_block = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def proof_of_work(self):
        #previous_proof = last_block.proof
        #last_hash = last_block.hash()
        ononce = self.nonce
        self.nonce = 1
        check_proof = False

        while check_proof is False:
            check_proof = self.validate_proof(self)
            if check_proof is False:
                self.nonce += 1
                if self.nonce % (100000 * 60) == 0:
                    print(self.nonce)

        temp = self.nonce
        self.nonce = ononce
        return temp

    def validate_proof(self, block):
        guess = f'{block.__dict__}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def hash_proof(self):
        guess = f'{self.__dict__}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash

class Blockchain:

    def __init__(self, dht, last_block = None, is_miner = True):
        self.chain = []
        self.dht = dht
        self.is_miner = is_miner
        self.last_block = last_block

    def find_block_network(self, id):
        1

    def accept_block(self, block):
        txs = block.get_transactions()
        for tx in txs:
            if not tx.validate() or not tx.verify():
                return
            accounts[tx.sender] -= tx.amount + tx.fee
            accounts[tx.receiver] += tx.amount
            accounts[block.miner] += tx.fee
        accounts[block.miner] += 20
        self.chain.append(block)

    def create_block(self):
        if self.is_miner and os.stat('transactions.txt').st_size == 0:
            with open('transactions.txt', 'r') as file:
                lines = file.readlines()
                block = Block(self.last_block.id + 1, self.last_block.prev_hash, key_string[1])
                for line in lines:
                    d = line.split(',')
                    if len(d) < 5:
                        continue
                    tx = Transaction(d[0], d[1], d[2], d[3], d[4])
                    tx.sign(d[5])
                    if tx.validate() and tx.verify():
                        block.add_transaction(tx)
                        accounts[d[3]] -= d[0] + d[1]
                        accounts[d[4]] += d[0]
                        accounts[key_string[1]] += d[1]
                        block.add_transaction(tx)
                accounts[key_string[1]] += 20

            block.nonce = block.proof_of_work()
            # TODO: SEND THIS BLOCK TO OTHERS
            open('transactions.txt', 'w').close()


"""if __name__ == '__main__':
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
#    pickle.dump(x, f)"""
