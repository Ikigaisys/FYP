import sys
import threading
import logging
import asyncio
from .filestorage import FileStorage
from kademlia.network import Server

class DHT:

    def __init__(self, storage_file, port):
        # Logging
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.log = logging.getLogger('kademlia')
        self.log.addHandler(self.handler)
        self.log.setLevel(logging.DEBUG)
        self.port = port

        # Set loop
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

        self.node = Server(storage=FileStorage(storage_file))
        # asyncio.run(self.bootstrapper())
        self.loop.create_task(self.node.listen(port))

    async def bootstrapper(self):
        await self.node.listen(self.port)
        await self.node.bootstrap([('172.25.48.135', 5678)])

    def server(self):
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            print(self.node.protocol.router.buckets[0].get_nodes())
        finally:
            self.node.stop()
            self.loop.close()

    def set_server(self):
        while True:
            data = input()
            split_data = data.split(',')
            if len(split_data) == 2:
                asyncio.run_coroutine_threadsafe(self.node.bootstrap([('172.25.48.135', 5678)]), self.loop)
                asyncio.run_coroutine_threadsafe(self.node.set(split_data[0], split_data[1]), self.loop)

    def run(self):
        server_thread = threading.Thread(target=self.server)
        set_thread = threading.Thread(target=self.set_server)

        server_thread.start()
        set_thread.start()

        server_thread.join()
        set_thread.join()