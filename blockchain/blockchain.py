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

if not os.path.exists('config.ini'):
    print('Please use templates/config_template.ini to create a config file.')
    os.abort()

config = ConfigParser()
config.read('config.ini')
if not config.has_section('keys') or not config.has_option('keys', 'public_key') or not config.has_option('keys', 'private_key'):
    pvt, pbk = Key().to_string()
    if not config.has_section('keys'):
        config.add_section('keys')
        
    config['keys']['private_key'] = pvt.replace('\n', '$$')
    config['keys']['public_key'] = pbk.replace('\n', '$$')
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

if config.has_section('keys') and config.has_option('keys', 'public_key') and config.has_option('keys', 'private_key'):
    k1 = config.get('keys', 'private_key').replace('$$', '\n')
    k2 = config.get('keys', 'public_key').replace('$$', '\n')
    key = Key(k1, k2)
    key_string = key.to_string()

accounts = FileHashTable('accounts.txt')
        
class Domain:

    def __init__(self):
        self.domain = ''
        self.value = ''


class Transaction:

    def __init__(self, amount, fee, category, sender, receiver, time = None, signature = None):
        self.amount = amount
        self.fee = fee
        if time == None:
            self.time = int(datetime.now().timestamp() / 1000)
        else:
            self.time = time
        self.details = { 'category': category, 'sender': sender, 'receiver': receiver }
        self.signature = signature

    def validate(self):
        # Check if the sender can send the money
        sender = self.details['sender'].replace('\n', '$$')
        if accounts[sender] is not None and accounts[sender] - self.fee - self.amount > 0:
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
        if data == None:
            self.data = None
        else:
            self.data = []
            for tx_data in data:
                if isinstance(tx_data, Transaction):
                    tx = tx_data
                else:
                    tx = Transaction(tx_data['amount'], tx_data['fee'], tx_data['details']['category'], tx_data['details']['sender'], tx_data['details']['receiver'], tx_data['time'], tx_data['signature'])
                if not tx.validate() or not tx.verify():
                    print('The block has invalid transaction..')
                    return False
                self.data.append(tx)

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
        return block_hash[:3] == "000"

    def hash(self):
        encoded_block = f'{todict(self)}'.encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def hash_stored(self):
        if hasattr(self, 'stored_hash'):
            return self.stored_hash
        return self.hash()

    def demo_create(self):
        self.miner = key_string[1]
        self.nonce = self.proof_of_work()


class Blockchain:

    def __init__(self, dht, last_block = None, is_miner = True):
        self.chain = []
        self.dht = dht
        self.is_miner = is_miner
        self.last_block = last_block
        if os.path.exists('blockchain.txt') and os.stat('blockchain.txt').st_size != 0:
            with open('blockchain.txt', 'r') as file:
                lines = file.readlines()
                i = 0
                for line in lines:
                    line = json.loads(line);
                    if i == 0:
                        self.last_block = Block(line['id'], line['prev_hash'], line['miner'], line['timestamp'], line['nonce'], line['data'])
                        if 'stored_hash' in line:
                            self.last_block.stored_hash = line['stored_hash'] 
                    else:
                        block = Block(line['id'], line['prev_hash'], line['miner'], line['timestamp'], line['nonce'], line['data'])
                        if 'stored_hash' in line:
                            block.stored_hash = line['stored_hash']
                        self.chain.append(block)
                    i = i + 1

    # Find the block on the network
    def find_block_network(self, id):
        key = str(id)

        result = self.dht.get(key)
        if result is None:
            print("Nothing received from network, no block")
            return None

        data = json.loads(result)
        print(data)
        if(data['type'] != 'block'):
            print("Oh no :( block lost, lolbye")
            return None
        
        args = json.loads(data['data']);
        block = Block(args['id'], args['prev_hash'], args['miner'], args['timestamp'], args['nonce'], args['data'])


        if not block.validate_proof():
            print("INVALID BLOCK HACKING ATTEMPTS REEEEEEEEEEEEEEEEEEEE")
            return None
        
        return block
        

    # Block received/created, update the account data for each person by
    # performing transactions
    # TODO: Rollback when a transaction is invalid...
    def tx_perform(self, block):
        txs = block.get_transactions()
        miner = block.miner.replace('\n', '$$')
        if accounts[miner] is None:
            accounts[miner] = 0

        for tx in txs:
            if not tx.validate() or not tx.verify():
                return False

            sender = tx.details['sender'].replace('\n', '$$')
            receiver = tx.details['receiver'].replace('\n', '$$')

            # If transaction type is domain, money should be burnt
            if tx.details['category'] == 'domain':
                if tx.details['receiver'] == '0' and tx.amount == 1:
                    accounts[sender] -= tx.amount + tx.fee
                    accounts[miner] += tx.fee
                else:
                    return False

            else:
                accounts[sender] -= tx.amount + tx.fee
                if accounts[receiver] is None:
                    accounts[receiver] = 0
                accounts[receiver] += tx.amount
                accounts[miner] += tx.fee

        accounts[miner] += 20
        return True 

    # Update the chain by performing missing/new transactions
    # Update last_block attribute
    def chain_update(self, block):
        # The block sent to me isnt the next block, eg: im at #3 and i get sent #6,
        # holes in-between 
        while self.last_block.id < block.id:
            # 3 attempts for finding new block
            found = False
            for i in range(3):
                _block = self.find_block_network(self.last_block.id + 1)
                # New block found, attempt to update my last block
                if _block is not None:
                    if self.last_block.id + 1 == _block.id and _block.prev_hash == self.last_block.hash_stored() and _block.validate_proof() and self.tx_perform(_block):
                        self.last_block = _block
                        self.chain_append(_block, False)
                        found = True
                        break
                time.sleep(1)
        
            # Holes in my chain that I'm unable to fill
            if not found and self.last_block.id + 1 < block.id:
                return False
            elif not found and self.last_block.id + 1 == block.id:
                break

        if self.last_block.id == block.id:

            if self.last_block.hash_stored() == block.hash():
                return True
            else:
                print("Network gave me a different last block, don't trust this new one")
                return False

        if self.last_block.id + 1 == block.id and block.prev_hash == self.last_block.hash_stored() and block.validate_proof() and self.tx_perform(block):
            self.last_block = block
            return True

        if self.last_block.id == block.id and self.last_block.hash_stored() == block.hash():
            return True

        return False

    # Add the block to the chain
    def chain_append(self, block, keep_data = True):
        # Strip data for mini-chain
        if not keep_data:
            block.stored_hash = block.hash()
            block.data = None

        # Handle append in array/replacement in array
        found = False
        for blk, i in enumerate(self.chain):
            if self.chain[blk].id == block.id:
                self.chain[blk] = block 
                found = True
        if not found:
            self.chain.append(block)

        with open('blockchain.txt', 'w') as file:
            file.write(json.dumps(todict(self.last_block), sort_keys = True) + '\n')
            for block in self.chain:
                file.write(json.dumps(todict(block), sort_keys = True) + '\n')

    # Try to accept a new incoming block
    def accept_block(self, block, keep_data = True):
        # Handle a newly created block
        if self.chain_update(block):
            self.chain_append(block, keep_data)
            return True

        # Handle older blocks (Don't perform transactions again, just store)
        if self.last_block.id > block.id:
            find_block = None
            find_prev_block = None
            # Find in mini-chain
            for blk in self.chain:
                if blk.id == block.id:
                    find_block = blk
                if blk.id == block.id - 1:
                    find_prev_block = blk

            # Is it valid?
            if (find_block is not None and find_prev_block is not None and 
                block.prev_hash == find_prev_block.hash_stored() and 
                block.hash() == find_block.hash_stored() and 
                block.validate_proof()):

                for ts in block.data:
                    if not ts.validate() or not ts.verify():
                        print('The old block has an invalid transaction..')

                self.chain_append(block, keep_data)
                return True
            else:
                print("Block store request ignored...")
        return False

    # Create a new block
    def create_block(self):
        if self.is_miner and os.path.exists('transactions.txt') and  os.stat('transactions.txt').st_size != 0:
            with open('transactions.txt', 'r') as file:
                lines = file.readlines()
                block = Block(self.last_block.id + 1, self.last_block.hash(), key_string[1])
                for line in lines:
                    if len(line.split(',')) < 5:
                        print('Invalid transaction split size')
                        continue
                    amount, fee, category, sender, receiver, private_key = line.split(',')
                    sender = sender.replace('$$', '\n')
                    receiver = receiver.replace('$$', '\n')

                    tx = Transaction(float(amount), float(fee), category, sender, receiver)
                    sig = Signatures()
                    private_key, tmp = sig.string_to_key(private_key.replace('$$', '\n').encode(), None)
                    tx.sign(private_key)

                    if tx.validate() and tx.verify():
                        block.add_transaction(tx)
                    else:
                        print("Invalid transaction detected, skipping!")

            block.miner = key_string[1]
            block.nonce = block.proof_of_work()
            
            # TODO: IF NONCE WAS FOUND AFTER A NEW BLOCK WAS RECEIVED,
            # UPDATE ID AND REPEAT PROCEDURE
            
            #block = Block(2, "000028d21dadaf9f7e1eb56ccc1a36346cb009b79cf733d03a484b9bd9b06c4f")
            #block.demo_create()
            print(block.hash() + " found for new block")
            key = block.id
            value = {
                'type': 'block',
                'store': True,
                'data': block.serialize()
            }
            value_encoded = json.dumps(value)
            print(value_encoded)

            # Request some people to permanantly store it
            value_encoded = json.dumps(value)
            self.dht.set(key, value_encoded)

            time.sleep(20)

            # This will try to set the block as a new block as if
            # someone sent the block => will try finding this block
            # on network and update self only when network has agreed 
            # on this block as the next
            blk = self.find_block_network(block.id)

            if(blk is not None and blk.hash() == block.hash()):
            # Notify everyone that I just made a block
                value['store'] = False
                self.dht.broadcast(key, value_encoded)
                self.tx_perform(block)
                self.last_block = block
                self.chain_append(block)
                open('transactions.txt', 'w').close()
            else:
                print("Discarding block, network did not accept")

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
