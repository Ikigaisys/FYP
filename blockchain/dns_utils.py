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

def domain_find(self, domain):
    value = self.dht.find(domain)
    if  (value is not None and value['type'] == 'domain'):

        block_id = value['block']
        # TODO: Cache
        if 'block_data' in value:
            1

        # Expired domain
        if block_id + 100 > self.last_block.id:
            return None

        block = self.chain_find(block_id)
        if block is not None and block.data is not None:
            return self.domain_find_in_tx(domain, block.data)
        block = self.find_block_network(block_id)
        if block is not None and block.data is not None:
            return self.domain_find_in_tx(domain, block.data)

    return None

def domain_find_in_tx(domain, txs):
    for tx in txs:
        if tx.details['category'] == 'domain' and tx.details['extra'] is not None:
            from .blockchain import Domain
            dmn = Domain()
            dmn.to_object(tx.details['extra'])
            if dmn.domain == domain:
                return [dmn.value, dmn.port]
    return None
