import hashlib
import json
import os
import time
from flask import Flask, jsonify
from datetime import datetime
from json import JSONEncoder
from .encryption import Signatures
from FileController import FileHashTable
from configparser import ConfigParser
import asyncio

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
        pvt, pb = sig.key_to_string(self.private_key, self.public_key)
        return pvt.decode('utf-8'), pb.decode('utf-8')

config = ConfigParser()
config.read('config.ini')
if not config.has_section('keys') or not config.has_option('keys', 'public_key') or not config.has_option('keys', 'private_key'):
    pvt, pbk = Key().to_string()
    if not config.has_section('keys'):
        config.add_section('keys')
        
    config['keys']['private_key'] = pvt.replace('\n', '$')
    config['keys']['public_key'] = pbk.replace('\n', '$')
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

if config.has_section('keys') and config.has_option('keys', 'public_key') and config.has_option('keys', 'private_key'):
    k1 = config.get('keys', 'private_key').replace('$', '\n')
    k2 = config.get('keys', 'public_key').replace('$', '\n')
    key = Key(k1, k2)
    key_string = key.to_string()

accounts = FileHashTable('accounts.txt')
        
class Domain:

    def __init__(self):
        self.domain = ''
        self.value = ''


class Transaction:

    def __init__(self, amount, fee, category, sender, receiver, time = None):
        self.amount = amount
        self.fee = fee
        if time == None:
            self.time = int(datetime.now().timestamp() / 1000)
        self.details = { 'category': category, 'sender': sender, 'receiver': receiver }
        self.signature = None

    def validate(self):
        # Check if the sender can send the money
        if accounts[self.details['sender']] is not None and accounts[self.details['sender']] - self.fee - self.amount > 0:
            return True
        return False

    def sign(self, private_key):
        # Sign using the private key
        sig = Signatures()
        self.signature = sig.sign(private_key, str.encode(json.dumps(self.__dict__, sort_keys=True)))

    def verify(self):
        # Verify this transaction true/false
        sig = Signatures()
        tmp, public_key = sig.string_to_key(None, self.details['sender'].encode())
        temp = self.signature
        self.signature = None
        temp2 = sig.verify(public_key, str.encode(json.dumps(self.__dict__, sort_keys=True)), temp)
        self.signature = temp
        return temp2

class Block:

    def __init__(self, id, prev_hash, miner=None, timestamp=None, nonce=None, data=[]):
        self.id = id
        if timestamp is None:
            self.timestamp = int(datetime.timestamp(datetime.now()) / 1000)  # in unix seconds
        else:
            self.timestamp = timestamp        
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.miner = miner
        self.data = data

    def add_transaction(self, tx):
        self.data.append(tx)

    def get_transactions(self):
        return self.data

    def find_transaction(self, key):
        pass

    def serialize(self):
        return json.dumps(todict(self), sort_keys=True)

    def proof_of_work(self):
        #previous_proof = last_block.proof
        #last_hash = last_block.hash()
        ononce = self.nonce
        self.nonce = 1
        check_proof = False

        while check_proof is False:
            check_proof = self.validate_proof()
            if check_proof is False:
                self.nonce += 1
                if self.nonce % (100000 * 60) == 0:
                    print(self.nonce)

        temp = self.nonce
        self.nonce = ononce
        return temp

    def validate_proof(self):
        block_hash = self.hash()
        return block_hash[:4] == "0000"

    def hash(self):
        encoded_block = f'{self.__dict__}'.encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def demo_create(self):
        self.miner = key_string[1]
        self.nonce = self.proof_of_work()


class Blockchain:

    def __init__(self, dht, last_block = None, is_miner = True):
        self.chain = []
        self.dht = dht
        self.is_miner = is_miner
        self.last_block = last_block
        if os.stat('blockchain.txt').st_size != 0:
            with open('blockchain.txt', 'r') as file:
                lines = file.readlines()
                i = 0
                for line in lines:
                    if i == 0:
                        self.is_miner = bool(line)
                    elif i == 1:
                        self.last_block = json.loads(line, object_hook=lambda args: Block(**args))
                    else:
                        self.chain.append(json.loads(line, object_hook=lambda args: Block(**args)))
                    i = i + 1

    # Find the block on the network
    def find_block_network(self, id):
        key = id
        future = asyncio.run_coroutine_threadsafe(self.dht.node.get(key), self.dht.loop)

        try:
            result = future.result()
            if(result is None):
                print("Weird none result, quitting")
                return None
        except:
            print("No response received")
            return None

        data = json.loads(result)
        print(data)
        if(data['type'] != 'block'):
            print("Oh no :( block lost, lolbye")
            return None
        
        data = data['data']
        block = Block(data['id'], data['prev_hash'], data['miner'], data['timestamp'], data['nonce'], None)
        block.data = list()
        for tx in data['data']:
            t = Transaction(tx['amount'], tx['fee'], tx['category'], tx['sender'], tx['receiver'], tx['time'])
            t.signature = tx['signature']
            if not tx.validate() or not tx.verify():
                print('The block has invalid transaction..')
                return False
            block.data.append(t)

        print(block.data)
        if not block.validate_proof():
            print("INVALID BLOCK HACKING ATTEMPTS REEEEEEEEEEEEEEEEEEEE")
            return None
        
        return block
        

    # Block received/created, update the account data for each person by
    # performing transactions
    # TODO: Rollback when a transaction is invalid...
    def tx_perform(self, block):
        txs = block.get_transactions()
        for tx in txs:
            if not tx.validate() or not tx.verify():
                return False

            # If transaction type is domain, money should be burnt
            if tx.details.category == 'domain':
                if tx.receiver == 0 and tx.amount == 1:
                    accounts[tx.sender] -= tx.amount + tx.fee
                    accounts[block.miner] += tx.fee
                else:
                    return False

            else:
                accounts[tx.sender] -= tx.amount + tx.fee
                if accounts[tx.receiver] is None:
                    accounts[tx.receiver] = 0
                accounts[tx.receiver] += tx.amount
                accounts[block.miner] += tx.fee

        accounts[block.miner] += 20
        return True 

    # Block received, update the chain by performing transactions
    def set_last_block(self, block):
        # The block sent to me isnt the next block, eg: im at #3 and i get sent #6,
        # holes in-between 
        while self.last_block.id < block.id:
            # 3 attempts for finding new block
            found = False
            for i in range(3):
                block = self.find_block_network(self.last_block.id + 1)
                # New block found, attempt to update my last block
                print(block)
                if block is not None:
                    if self.last_block.id + 1 == block.id and block.prev_hash == self.last_block.hash() and block.validate_proof() and self.tx_perform(block):
                        self.last_block = block
                        found = True
                        break
                time.sleep(3)
            if not found:
                return False

        if self.last_block.id == block.id:

            if self.last_block.hash() == block.hash():
                return True

            print("Network gave me last block, don't trust this new one")
            return False

        print(block.prev_hash)
        print(self.last_block.hash())
        if self.last_block.id + 1 == block.id and block.prev_hash == self.last_block.hash() and block.validate_proof() and self.tx_perform(block):
            self.last_block = block
            return True

        if self.last_block.id == block.id and self.last_block.hash() == block.hash():
            return True

        return False

    # Add the block to the chain
    def chain_append(self, block):
        self.chain.append(block)
        with open('blockchain.txt', 'w') as file:
            file.write(str(self.is_miner) + '\n')
            file.write(json.dumps(self.last_block.__dict__, sort_keys = True) + '\n')
            for block in self.chain:
                file.write(json.dumps(block.__dict__, sort_keys = True) + '\n')

    # Try to accept a new incoming block
    def accept_block(self, block):
        # Handle newer blocks
        if self.set_last_block(block):
            self.chain_append(block)
            return True
        # Handle older blocks (Don't do transactions again)
        if self.last_block.id > block.id:
            self.chain_append(block)
            return True
        return False

    # Create a new block
    def create_block(self):
        if self.is_miner and os.stat('transactions.txt').st_size != 0:
            with open('transactions.txt', 'r') as file:
                lines = file.readlines()
                block = Block(self.last_block.id + 1, self.last_block.prev_hash, key_string[1])
                for line in lines:
                    if len(line.split(',')) < 5:
                        continue
                    amount, fee, category, sender, receiver, private_key = line.split(',')
                    sender = sender.replace('$', '\n')
                    receiver = receiver.replace('$', '\n')

                    tx = Transaction(float(amount), float(fee), category, sender, receiver)
                    sig = Signatures()
                    private_key, tmp = sig.string_to_key(private_key.replace('$', '\n').encode(), None)
                    tx.sign(private_key)

                    if tx.validate() and tx.verify():
                        block.add_transaction(tx)

            block.miner = key_string[1]
            block.nonce = block.proof_of_work()
            
            # TODO: IF NONCE WAS FOUND AFTER A NEW BLOCK WAS RECEIVED,
            # UPDATE ID AND REPEAT PROCEDURE
            
            #block = Block(2, "000028d21dadaf9f7e1eb56ccc1a36346cb009b79cf733d03a484b9bd9b06c4f")
            #block.demo_create()
            print(block.hash())
            key = block.id
            value = {
                'type': 'block',
                'data': block.serialize()
            }
            value_encoded = json.dumps(value)
            print(value_encoded)
            #self.dht.storage(None, None, None, value_encoded)
            self.dht.broadcast(key, value_encoded)
            time.sleep(3)

            if(self.set_last_block(block)):
                #self.tx_perform(block)
                open('transactions.txt', 'w').close()
            return block

def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey)) 
            for key, value in obj.__dict__.items() 
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj

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
