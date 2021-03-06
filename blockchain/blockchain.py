import hashlib
import json
import os
import operator
import time
from datetime import datetime
from .encryption import Signatures
from DataController import SQLiteHashTable, db
from configparser import ConfigParser
from .dns_utils import *
from kademlia.utils import digest

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

accounts = SQLiteHashTable('accounts', 'float')

class Domain:

    def __init__(self):
        self.domain = None
        self.value = None
        self.port = None

    def to_object(self, extra):
        if len(extra.split(":")) == 3:
            self.domain, self.value, self.port = extra.split(":")
        else:
            self.domain = None
            self.value = None
            self.port = None

    def to_string(self):
        return self.domain + ":" + self.value + ":" + self.port

class Transaction:

    def __init__(self, amount, fee, category, sender, receiver, time = None, signature = None, extra = None):
        self.amount = amount
        self.fee = fee
        if time == None:
            self.time = int(datetime.now().timestamp() / 1000)
        else:
            self.time = time
        self.details =  {   'category': category, 
                            'sender': sender, 
                            'receiver': receiver, 
                            'extra': extra }
        self.signature = signature

    def validate(self, blockchain, new = False, block_id = None):
        # Check if the sender can send the money
        sender = self.details['sender'].replace('\n', '$$')
        if accounts[sender] is not None and accounts[sender] - self.fee - self.amount > 0:

            # DNS?
            if new == True and self.details['category'] == 'domain' and self.details['extra'] is not None:
                dmn = Domain()
                dmn.to_object(self.details['extra'])
                dmn_block = domain_find(blockchain, dmn.domain)
                if self.details['receiver'] == '0' and self.amount == 1 and dmn_block is None or dmn_block[0] == block_id:
                    # retry just for safety
                    if dmn_block == None:
                        time.sleep(1)
                        dmn_block = domain_find(blockchain, dmn.domain)
                    if dmn_block is None or dmn_block[0] == block_id:
                        return True
                return False
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
                    if 'extra' not in tx_data['details']:
                        tx_data['details']['extra'] = None

                    tx = Transaction(tx_data['amount'], tx_data['fee'], tx_data['details']['category'], tx_data['details']['sender'], tx_data['details']['receiver'], tx_data['time'], tx_data['signature'], tx_data['details']['extra'])

                if not tx.validate(self) or not tx.verify():
                    print('The block has an invalid transaction..')
                    return False

                self.data.append(tx)

    def add_transaction(self, tx):
        self.data.append(tx)

    def get_transactions(self):
        return self.data

    def find_transaction_by_extra(self, extra):
        for tx in self.data:
            if tx.details['extra'] == extra:
                return tx
        return None

    def serialize(self):
        return json.dumps(self.to_dict(), sort_keys=True)

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

        temp = self.nonce
        self.nonce = ononce
        return temp

    def validate_proof(self):
        block_hash = self.hash()
        return block_hash[:3] == "000"

    def hash(self):
        encoded_block = self.serialize().encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def hash_stored(self):
        if hasattr(self, 'stored_hash') and self.stored_hash is None:
            delattr(self, 'stored_hash')
        if hasattr(self, 'stored_hash'):
            return self.stored_hash            
        return self.hash()

    def demo_create(self):
        self.miner = key_string[1]
        self.nonce = self.proof_of_work()

    def to_dict(self):
        dict_form = {
            'id': self.id,
            'timestamp': self.timestamp,
            'prev_hash': self.prev_hash,
            'nonce': self.nonce,
            'miner': self.miner,
            'data': None
        }

        if self.data is not None:
            dict_form['data'] = []
            for data_part in self.data:
                sorted_data = dict(sorted(data_part.__dict__.items(), key=operator.itemgetter(0)))
                sorted_data['details'] = dict(sorted(sorted_data['details'].items(), key=operator.itemgetter(0)))
                sorted_data['signature'] = [int_val for int_val in sorted_data['signature']]
                dict_form['data'].append(sorted_data)
        if hasattr(self, 'stored_hash'):
            dict_form['stored_hash'] = self.stored_hash

        return dict_form

class Blockchain:

    def __init__(self, dht, is_miner = True):
        self.chains = {}
        self.dht = dht
        self.is_miner = is_miner
        self.last_blocks = {}
        self.fork_locations = {}
        self.id = None
        db.execute("""
            CREATE TABLE IF NOT EXISTS blockchain 
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            fork_location INTEGER, last_block INTEGER)
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS blocks 
            (id INTEGER, prev_hash CHAR(64), miner CHAR(460),
            timestamp INTEGER, nonce INTEGER, data TEXT, stored_hash CHAR(64),
            chain INTEGER, PRIMARY KEY (id, chain))
        """)
        cur = db.con.cursor()
        cur.execute("SELECT id, last_block, fork_location from blockchain")
        for blockchain in cur:
            self.chains[blockchain['id']] = blockchain['id']
            if self.id == None or blockchain['last_block'] > self.last_blocks[self.id].id:
                self.id = blockchain['id']
            self.fork_locations[blockchain['id']] = blockchain['fork_location']            
            block = db.fetchone("SELECT * from blocks where chain = ? and id = ?", (self.id, blockchain['last_block']))
            if block is not None:
                self.last_blocks[blockchain['id']] = Block(block['id'], block['prev_hash'], block['miner'], block['timestamp'], block['nonce'], json.loads(block['data']))
                if 'stored_hash' in block:
                    self.last_blocks[blockchain['id']].stored_hash = block['stored_hash']
        cur.close()
        if len(self.chains) == 0:
            self.id = db.execute('insert into blockchain (last_block, fork_location) values (?,?)', (0,0))
            self.chain_append(Block(0, '0', timestamp=0))

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
        
    def validate_block(self, block):
        if block.id - 1 < 0:
            return False
        local_block = self.chain_find(block.id)
        local_block_before = self.chain_find(block.id - 1)
        if (local_block is not None and
            local_block_before is not None and 
            local_block_before.hash_stored() == block.prev_hash and 
            local_block.hash_stored() == block.hash() and 
            local_block.nonce == block.nonce):
            return True
        return False

    # Always call before tx_perform
    def tx_validate(self, block, new = False):
        txs = block.get_transactions()
        for tx in txs:
            if not tx.validate(self, new, block.id) or not tx.verify():
                return False
        return True

    # Block received/created, update the account data for each person by
    # performing transactions
    # TODO: Rollback when a transaction is invalid...
    def tx_perform(self, block):
        txs = block.get_transactions()
        miner = block.miner.replace('\n', '$$')
        if accounts[miner] is None:
            accounts[miner] = 0

        for tx in txs:
            sender = tx.details['sender'].replace('\n', '$$')
            receiver = tx.details['receiver'].replace('\n', '$$')

            # If transaction type is domain, money should be burnt
            if tx.details['category'] == 'domain':
                accounts[sender] -= (tx.amount + tx.fee)
                accounts[miner] += tx.fee

            else:
                accounts[sender] -= (tx.amount + tx.fee)
                if accounts[receiver] is None:
                    accounts[receiver] = 0
                accounts[receiver] += tx.amount
                accounts[miner] += tx.fee

        accounts[miner] += 20

    # Update the chain by performing missing/new transactions
    # Update last_block attribute
    def chain_update(self, block, keep_data = True):
        # The block sent to me isn't the next block, eg: im at #3 and i get sent #6,
        # holes in-between 
        while self.last_blocks[self.id].id < block.id:
            # 3 attempts for finding new block
            found = False
            for i in range(3):
                _block = self.find_block_network(self.last_blocks[self.id].id + 1)
                # New block found, attempt to update my last block
                if _block is not None:
                    if self.last_blocks[self.id].id + 1 == _block.id and _block.prev_hash == self.last_blocks[self.id].hash_stored() and _block.validate_proof() and self.tx_validate(_block, True):
                        #self.last_block = _block
                        self.tx_perform(_block) 
                        self.chain_append(_block, False)
                        found = True
                        break
                time.sleep(1)
        
            # Holes in my chain that I'm unable to fill
            if not found and self.last_blocks[self.id].id + 1 < block.id:
                return False
            elif not found and self.last_blocks[self.id].id + 1 == block.id:
                break

        if self.last_blocks[self.id].id == block.id:

            if self.last_blocks[self.id].hash_stored() == block.hash():
                self.chain_append(block, keep_data)
                return True
            else:
                print("Network gave me a different last block, don't trust this new one")
                print("TODO: Fork and save both")
                return False

        if self.last_blocks[self.id].id + 1 == block.id and block.prev_hash == self.last_blocks[self.id].hash_stored() and block.validate_proof() and self.tx_validate(block, True):
            #self.last_block = block
            self.tx_perform(block)
            self.chain_append(block, keep_data)
            return True

        return False

    # Find from local chain
    def chain_find(self, id, chain = None):
        if chain is None:
            chain = self.id
        block = db.fetchone("SELECT * from blocks where chain = ? and id = ?", (chain, id))
        if block is not None:
            blk = Block(block['id'], block['prev_hash'], block['miner'], block['timestamp'], block['nonce'], json.loads(block['data']))
            if 'stored_hash' in block:
                blk.stored_hash = block['stored_hash']
            return blk
        return None

    # Add the block to the chain
    def chain_append(self, block, keep_data = True, chain = None):
        if chain is None:
            chain = self.id

        if chain not in self.last_blocks or self.last_blocks[chain].id < block.id:
            self.last_blocks[chain] = block
            db.execute("update blockchain set last_block = ? where id = ?", (block.id, chain))

        # Strip data for mini-chain
        if not keep_data:
            block.stored_hash = block.hash()
            block.data = None

        # Handle append in array/replacement in array
        tblock = db.fetchone("SELECT * from blocks where chain = ? and id = ?", (chain, block.id))
        blockstr = json.dumps(todict(block.data), sort_keys = True)
        stored_hash = None
        if hasattr(block, 'stored_hash'):
            stored_hash = block.hash_stored()

        if tblock is None:
            db.execute('insert into blocks (id, prev_hash, miner, timestamp, nonce, data, chain, stored_hash) values (?,?,?,?,?,?,?,?)',
                (block.id, block.prev_hash, block.miner, block.timestamp, block.nonce, blockstr, chain, stored_hash))
        else:
            db.execute('update blocks set prev_hash=?, miner=?, timestamp=?, nonce=?, data=?, chain=?, stored_hash=? where id=?',
                (block.prev_hash, block.miner, block.timestamp, block.nonce, blockstr, chain, stored_hash, block.id))
        
    # Try to accept a new incoming block
    def accept_block(self, block, keep_data = True):
        # Handle a newly created block
        if self.chain_update(block, keep_data):
            return True

        # Handle older blocks (Don't perform transactions again, just store)
        if self.last_blocks[self.id].id > block.id:
            find_block = self.chain_find(block.id)
            find_prev_block = self.chain_find(block.id - 1)

            # Is it valid?
            if (find_block is not None and find_prev_block is not None and 
                block.prev_hash == find_prev_block.hash_stored() and 
                block.hash() == find_block.hash_stored() and 
                block.validate_proof()):

                for ts in block.data:
                    if not ts.validate(self) or not ts.verify():
                        print('The old block has an invalid transaction..')

                self.chain_append(block, keep_data)
                return True
            else:
                print("Block store request ignored, a mini version does not exist of this/previous block...")
        return False

    # Create a new block
    def create_block(self, empty=False):
        if self.is_miner:
            db.execute("""
                CREATE TABLE IF NOT EXISTS transactions 
                (sender CHAR(460), receiver CHAR(460),
                private_key CHAR(1732), signature TEXT,
                extra TEXT, amount REAL, fee REAL,
                category CHAR(16))
            """)
            block = Block(self.last_blocks[self.id].id + 1, self.last_blocks[self.id].hash_stored(), key_string[1])
            cur = db.con.cursor()
            cur.execute("SELECT * from transactions")
            for trans in cur:
                sender = trans['sender'].replace('$$', '\n')
                receiver = trans['receiver'].replace('$$', '\n')
                extra = None
                if trans['extra'] is not None:
                    extra = trans['extra']

                tx = Transaction(float(trans['amount']), float(trans['fee']), trans['category'], sender, receiver, extra=extra)
                if trans['private_key'] is not None:
                    sig = Signatures()
                    private_key, tmp = sig.string_to_key(trans['private_key'].replace('$$', '\n').encode(), None)
                    tx.sign(private_key)
                else:
                    tx.signature = json.loads(trans['signature'])

                if tx.validate(self, True, self.last_blocks[self.id].id + 1) and tx.verify():
                    block.add_transaction(tx)
                else:
                    print("Invalid transaction detected, skipping!")
            cur.close()

            if len(block.data) == 0 and empty == False:
                return "No Transactions"

            block.miner = key_string[1]
            block.nonce = block.proof_of_work()
            
            # TODO: IF NONCE WAS FOUND AFTER A NEW BLOCK WAS RECEIVED,
            # UPDATE ID AND REPEAT PROCEDURE
            
            #block = Block(2, "000028d21dadaf9f7e1eb56ccc1a36346cb009b79cf733d03a484b9bd9b06c4f")
            #block.demo_create()
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

            time.sleep(30)

            # This will try to set the block as a new block as if
            # someone sent the block => will try finding this block
            # on network and update self only when network has agreed 
            # on this block as the next
            
            blk = self.find_block_network(block.id)

            if(blk is not None and blk.hash() == block.hash()):
            # Notify everyone that I just made a block
                value['store'] = False
                dht_set = db.fetchone("select * from dht_data where key=?", (digest(block.id),))
                if dht_set is None:
                    self.tx_perform(block)
                self.dht.broadcast(key, value_encoded)
                self.last_block = block
                self.chain_append(block)
                domain_broadcast(self.dht, block)
                for tx in block.data:
                    db.execute('delete from transactions where sender=? and receiver=? and amount=? and fee=?', (tx.details['sender'], tx.details['receiver'], tx.amount, tx.fee))
                return "Block Created"

            else:
                print("Discarding block, network did not accept")
                return "Discarding block, network did not accept"
        return "Not a miner"


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