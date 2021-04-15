import sys
import threading
import logging
import asyncio
import os
from configparser import ConfigParser
import json
from .filestorage import FileStorage
from kademlia.network import Server
from blockchain.blockchain import Blockchain, Block

class DHT:

    config = ConfigParser()
    config.read('config.ini')

    def __init__(self, storage_file):
        # Logging
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.log = logging.getLogger('kademlia')
        self.log.addHandler(self.handler)
        self.log.setLevel(logging.DEBUG)
        self.port = DHT.config.getint('server', 'port')

        # Blockchain 
        self.chain = Blockchain(self, Block(0, None))

        # Set loop
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

        self.node = Server(storage=FileStorage(storage_file))
        # asyncio.run(self.bootstrapper())
        self.loop.create_task(self.node.listen(self.port, self.storage))

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
        send_node = (DHT.config.get('test', 'address'), DHT.config.getint('test', 'port'))
        # TODO SET/REQUEST LAST BLOCK OF BLOCKCHAIN

        while True:
            # block = chain.create_block()

            data = input()
            split_data = data.split(',')

            if len(split_data) == 2:
                asyncio.run_coroutine_threadsafe(self.node.bootstrap([send_node]), self.loop)
                asyncio.run_coroutine_threadsafe(self.node.set(split_data[0], split_data[1]), self.loop)

            elif data == 'send':
                asyncio.run_coroutine_threadsafe(self.node.bootstrap([send_node]), self.loop)
    
                block = Block(0, None)
                key = block.id
                value = {
                    'type': 'block',
                    'data': block.serialize()
                }
                value_encoded = json.dumps(value)

                asyncio.run_coroutine_threadsafe(self.node.set(key, value_encoded), self.loop)

            elif data == 'get':
                asyncio.run_coroutine_threadsafe(self.node.bootstrap([send_node]), self.loop)
                block = Block(0, None)
                key = block.id
                future = asyncio.run_coroutine_threadsafe(self.node.get(key), self.loop)
                result = future.result(3)
                print(result)

    def run(self):
        server_thread = threading.Thread(target=self.server)
        set_thread = threading.Thread(target=self.reader)

        server_thread.start()
        set_thread.start()

        server_thread.join()
        set_thread.join()