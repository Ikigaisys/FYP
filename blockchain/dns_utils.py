import json

def domain_broadcast(dht, block):
    for tx in block.data:
        if tx.details['category'] == 'domain' and tx.details['extra'] != None:
            from .blockchain import Domain
            domain = Domain()
            domain.to_object(tx.details['extra'])
            value = {
                'type': 'domain',
                'block': block.serialize(),
                'domain': tx.details['extra']
            }
            value_encoded = json.dumps(value)
            dht.broadcast(domain.domain, value_encoded)

def domain_find(blockchain, domain):
    value = blockchain.dht.find(domain)
    if  (value is not None and value['type'] == 'domain'):

        block_id = value['block']
        # TODO: Cache
        if 'block_data' in value:
            1

        # Expired domain
        if block_id + 100 > blockchain.last_blocks[blockchain.id].id:
            return None

        block = blockchain.chain_find(block_id)
        if block is not None and block.data is not None:
            return domain_find_in_tx(domain, block_id, block.data)
        block = blockchain.find_block_network(block_id)
        if block is not None and block.data is not None:
            return domain_find_in_tx(domain, block_id, block.data)

    return None

def domain_find_in_tx(domain, block_id, txs):
    for tx in txs:
        if tx.details['category'] == 'domain' and tx.details['extra'] is not None:
            from .blockchain import Domain
            dmn = Domain()
            dmn.to_object(tx.details['extra'])
            if dmn.domain == domain:
                return [block_id, dmn.value, dmn.port]
    return None
