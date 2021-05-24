import sys
import threading
import logging
import asyncio
import os
import random
from configparser import ConfigParser
import json
from .filestorage import FileStorage
from kademlia.network import Server
from blockchain.blockchain import Blockchain, Block
from FileController import FileHashTable
from kademlia.node import Node
from kademlia.utils import digest

class DHT:

    config = ConfigParser()
    config.read('config.ini')

    if not config.has_section('node'):
        config.add_section('node')
    if not config.has_option('node', 'id'):
        config['node']['id'] = digest(random.getrandbits(255)).hex()
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def __init__(self, storage_file):
        # Logging
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.log = logging.getLogger('kademlia')
        self.log.addHandler(self.handler)
        self.log.setLevel(logging.DEBUG)
        self.port = DHT.config.getint('server', 'port')
        self.all_ips_hashtable = FileHashTable('all_ips.txt')

        # Set loop
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

        self.node = Server(storage=FileStorage(storage_file), 
                           node_id=bytes.fromhex(DHT.config['node']['id']),
                           broadcast_table=self.all_ips_hashtable)
        # asyncio.run(self.bootstrapper())
        self.loop.create_task(self.node.listen(self.port, self.storage))

        # Blockchain
        self.chain = Blockchain(self, Block(0, None))

    def storage(self, sender, nodeid, key, value):
        data = json.loads(value)

        if data['type'] == 'block':
            block = json.loads(data['data'], object_hook=lambda args: Block(**args))
            if self.chain.accept_block(block):
                return True
            return False

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
        addresses = DHT.config.get('test', 'address').split(',')
        ports = map(int, DHT.config.get('test', 'port').split(','))

        send_nodes =  list(zip(addresses, ports))

        # TODO SET/REQUEST LAST BLOCK OF BLOCKCHAIN

        while True:
            # block = chain.create_block()

            data = input()
            split_data = data.split(',')

            """if len(split_data) == 2:
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

            el"""
            
            if data == 'create':
                self.chain.create_block()

            elif data == 'bootstrap':
                asyncio.run_coroutine_threadsafe(
                    self.node.bootstrap(send_nodes), self.loop)

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
        for node_id, value in self.all_ips_hashtable.dict.items():
            ip, port = value.split(":")
            asyncio.run_coroutine_threadsafe(
                self.chain.dht.node.protocol.call_store(Node(digest(int(node_id, 16)), ip, int(port)), digest(_key), _value), 
                self.loop)


    def run(self):
        server_thread = threading.Thread(target=self.server)
        set_thread = threading.Thread(target=self.reader)

        server_thread.start()
        set_thread.start()

        server_thread.join()
        set_thread.join()