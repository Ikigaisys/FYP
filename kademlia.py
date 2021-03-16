import sys
import asyncio
from filestorage import FileStorage
from kademlia.network import Server

if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run():
    # Create a node and start listening on port 5678
    node = Server(storage=FileStorage("kademlia.csv"))
    await node.listen(5678)

    # Bootstrap the node by connecting to other known nodes, in this case
    # replace 123.123.123.123 with the IP of another node and optionally
    # give as many ip/port combos as you can for other nodes.
    await node.bootstrap([("192.168.18.3", 5678)])

    # set a value for the key "my-key" on the network
    await node.set("my-key", "my awesome value")

    # get the value associated with "my-key" from the network
    result = await node.get("my-key")
    print(result)

asyncio.run(run())
