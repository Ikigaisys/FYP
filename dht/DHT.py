import configparser
import threading
import logging
import asyncio
import time
import random
import shutil
import json
from .flask_server import app
from .flask_server import flask_variables
from configparser import ConfigParser
from .filestorage import FileStorage
from kademlia.network import Server
from blockchain.blockchain import Transaction, Blockchain, Block
from DataController import SQLiteHashTable
from kademlia.node import Node
from kademlia.utils import digest

class DHT:

    config = ConfigParser()
    config.read('config.ini')

    changes = None
    if not config.has_section('node'):
        config.add_section('node')
    if not config.has_option('node', 'id'):
        config['node']['id'] = digest(random.getrandbits(255)).hex()
        changes = True

    if not config.has_section('flask'):
        config.add_section('flask')
    if not config.has_option('flask', 'port'):
        config['flask']['port'] = '5000'
        changes = True

    if changes is not None:
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def __init__(self):

        # Logging
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.log = logging.getLogger('kademlia')
        self.log.addHandler(self.handler)
        self.log.setLevel(logging.DEBUG)
        self.port = DHT.config.getint('server', 'port')
        self.all_ips_hashtable = SQLiteHashTable('network_nodes_list')

        # Set loop
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

        self.node = Server(storage=FileStorage('dht_data'), 
                           node_id=bytes.fromhex(DHT.config['node']['id']),
                           broadcast_table=self.all_ips_hashtable)
        # asyncio.run(self.bootstrapper())
        self.loop.create_task(self.node.listen(self.port, self.receive_callback))

        # Blockchain
        self.chain = Blockchain(self, DHT.config.getboolean('blockchain', 'miner'))

    def callback_thread(self, sender, nodeid, key, value, storage):
        data = json.loads(value)

        if data['type'] == 'block':
            args = json.loads(data['data']);
            block = Block(args['id'], args['prev_hash'], args['miner'], args['timestamp'], args['nonce'], args['data'])

            if self.chain.accept_block(block, data['store'] or None):
                storage[key] = value
                return True
            return False

        if data['type'] == 'domain':
            bd = json.loads(data['block'])
            domain, ip, port = data['domain'].split(':')
            block = Block(bd['id'], bd['prev_hash'], bd['miner'], bd['timestamp'], bd['nonce'], bd['data'])
            if self.chain.validate_block(block):
                if block.find_transaction_by_extra(data['domain']):
                    storage[digest(domain)] = json.dumps({'type': 'domain', 'value': block.id})
                    return True
            return False

        return False # reject data insertion to DHT by default

    def receive_callback(self, sender, nodeid, key, value, storage):
        
        cb_thread = threading.Thread(target=self.callback_thread, args=(sender, nodeid, key, value, storage))

        cb_thread.start()

        return True


    def server(self):
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            print(self.node.protocol.router.buckets[0].get_nodes())
        finally:
            self.node.stop()
            self.loop.close()

    def reader(self):
        addresses = DHT.config.get('bootstrap', 'address').split(',')
        ports = map(int, DHT.config.get('bootstrap', 'port').split(','))
        self.send_nodes =  list(zip(addresses, ports))
        time.sleep(1)
        asyncio.run_coroutine_threadsafe(self.node.bootstrap(self.send_nodes), self.loop)

        flask_variables.set(self, self.send_nodes)
        app.run(port=DHT.config.getint('flask', 'port'))

        while True:
            # block = chain.create_block()

            data = input()
            split_data = data.split(' ')
            """split_data = data.split(',')

            if len(split_data) == 2:
                for key, value in self.all_ips_hashtable.dict.items():
                    v = value.split(":")
                    from kademlia.utils import digest
                    print(hashlib.sha1(str(int(v[0], 16)).encode('utf8')).digest())
                    asyncio.run_coroutine_threadsafe(
                        self.chain.dht.node.protocol.call_store(Node(digest(int(v[0], 16)), key, int(v[1])), digest(1), "2"), 
                        self.loop)

                asyncio.run_coroutine_threadsafe(
                    self.node.bootstrap(send_nodes), self.loop)
                asyncio.run_coroutine_threadsafe(self.node.set(
                    split_data[0], split_data[1]), self.loop)
            """
            
            if data == 'create':
                self.chain.create_block()

            elif data == 'bootstrap':
                asyncio.run_coroutine_threadsafe(self.node.bootstrap(self.send_nodes), self.loop)

            elif data == 'reset':
                shutil.copyfile('templates\\accounts_o.txt', 'accounts.txt')
                shutil.copyfile('templates\\blockchain_o.txt', 'blockchain.txt')
                shutil.copyfile('templates\\kademlia_o.csv', 'kademlia.csv')
                shutil.copyfile('templates\\transactions_o.txt', 'transactions.txt')
                open('network_nodes_list.txt', 'w').close()
                self.chain = Blockchain(self, Block(0, '0', timestamp=0), DHT.config.getboolean('blockchain', 'miner'))
                asyncio.run_coroutine_threadsafe(self.node.bootstrap(self.send_nodes), self.loop)

            elif data == 'reset_t':
                shutil.copyfile('templates\\transactions_o.txt', 'transactions.txt')

            elif len(split_data) >= 2 and split_data[0] == 'get':
                if len(split_data) >= 3 and split_data[1] == 'domain':
                    print("Not yet implemented") # Implement soon
                else:
                    print(self.get(split_data[1]))

            """elif data == 'send':
                asyncio.run_coroutine_threadsafe(
                    self.node.bootstrap(send_nodes), self.loop)

                #block = Block(2, "000028d21dadaf9f7e1eb56ccc1a36346cb009b79cf733d03a484b9bd9b06c4f")
                block.demo_create()
                print(block.hash())
                key = block.id
                value = {
                    'type': 'block',
                    'data': block.serialize()
                }
                value_encoded = json.dumps(value)
                self.storage(None, None, None, value_encoded)
                asyncio.run_coroutine_threadsafe(self.node.set(key, value_encoded), self.loop)

            elif data == 'get':
                asyncio.run_coroutine_threadsafe(self.node.bootstrap(send_nodes), self.loop)
                key = 2 # Test: get block # 2
                future = asyncio.run_coroutine_threadsafe(self.node.get(key), self.loop)
                result = future.result(3)
                print(result)"""

    def broadcast(self, _key, _value):
        for node_id, value in self.all_ips_hashtable.fetchall():
            ip, port = value.split(":")
            asyncio.run_coroutine_threadsafe(
                self.chain.dht.node.protocol.call_store(Node(digest(int(node_id, 16)), ip, int(port)), digest(_key), _value), 
                self.loop)

    def set(self, _key, _value):
        asyncio.run_coroutine_threadsafe(self.node.bootstrap(self.send_nodes), self.loop)
        asyncio.run_coroutine_threadsafe(self.node.set(_key, _value), self.loop)

    def get(self, _key):
        asyncio.run_coroutine_threadsafe(self.node.bootstrap(self.send_nodes), self.loop)
        future = asyncio.run_coroutine_threadsafe(self.node.get(_key), self.loop)
        try:
            result = future.result(5)
        except:
            return None
        return result

    def run(self):
        server_thread = threading.Thread(target=self.server)
        set_thread = threading.Thread(target=self.reader)

        server_thread.start()
        set_thread.start()

        server_thread.join()
        set_thread.join()