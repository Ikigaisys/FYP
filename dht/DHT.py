import sys
import logging
import asyncio
from .filestorage import FileStorage
from kademlia.network import Server

class DHT:
    def __init__(self, storage_file, port):
        #if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        #    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Logging
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.log = logging.getLogger('kademlia')
        self.log.addHandler(self.handler)
        self.log.setLevel(logging.DEBUG)

        # Set loop
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

        self.node = Server(storage=FileStorage(storage_file))
        self.loop.run_until_complete(self.node.listen(port))

    def run(self):
        try:
            self.loop.run_forever()
            print("F")
        except KeyboardInterrupt:
            print(self.node.protocol.router.buckets[0].get_nodes())
            pass
        finally:
            self.node.stop()
            self.loop.close()