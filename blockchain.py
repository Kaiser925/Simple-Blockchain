# -*- coding: utf-8 -*-

import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse


# Fist block
block = {
    'index': 1,
    'timestamp': 1506057125.900785,
    'transcations': [
        {
            'sender': "8527147fe1f5426f9dd545de4b27ee00",
            'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
            'amount': 5,
        }
    ],
    'proof': 324984774000,
    'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
}


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # Creates the genesis block
        self.new_block(previous_hash=1, proof=100)
        self.nodes = set()

    def register_node(self, address):
        """Add a new node to the list of nodes.

        :param address: <str> Address of node. Eg. 'http://192.168.0.1:5000'
        :returns: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """Determine if a given blockchain is valid.

        :param chain: <list> A blockchain.
        :returns: <bool> True if valid, False if not.
        """
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n------------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Check that the proof of work is correct.
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """Consensus algorithm for conflict resolution. Use the longest
        chain in the network

        :returns: <bool> True if chain is replaced, False if not.
        """
        neighbours = self.nodes
        new_chain = None
        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        # Grap and verify the chains from all the nodes in our net work
        for node in neighbours:
            response = request.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True
        return False

    def new_block(self, proof, previous_hash=None):
        """Creates a new block and adds it to chain.

        :param proof: <int> The proof given by the Proof of Work algorithm.
        :param previous_hash: (Optional) <str> Hash of previous Block.
        :returns: <dict> New Block.
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """Adds a new transaction to the list of transactions.

        :param sender: <str> Address of the Sender.
        :param recipient: <str> Addressof the Recipient.
        :param amount: <int> Amount.
        :returns: <int> The index of the Block that will hold this transation.
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """Hashes a Block.

        :param block: <dict> Block
        :returns: <str>
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """Returns the last Block in the chain.

        :returns: <Block> The last Block in the chain.
        """
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """Simple PoW
            -Find p' witch makes hash(p') start with 4 zeros.
            -P is the proof of previous work, and p' is the proof of current work.

        :param last_proof: <int>
        :returns: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is True:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """Verifies hash(last_proof, proof) starts with 4 zeros.

        :param last_proof: <int> Previous proof.
        :param proof: <int> Current proof.
        :returns: <bool> True if correct, False is not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Depoleyment Block Chain
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
block_chain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = block_chain.last_block
    last_proof = last_block['proof']
    proof = block_chain.proof_of_work(last_proof)
    block_chain.new_transaction(
        sender='0',  # Means it's a new block.
        recipient=node_identifier,
        amount=1,
    )
    block = block_chain.new_block(proof)
    response = {
        'message': "New block forged",
        'index': block['index'],
        'transaction': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    index = block_chain.new_transaction(
        values['sender'], values['recipient'], values['amount'])
    response = {
        'message': f'Transaction will be added to Block {index}'
    }
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': block_chain.chain,
        'length': len(block_chain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid  list of nodes", 400
    for node in nodes:
        block_chain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(block_chain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = block_chain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'chain': block_chain.chain,
        }
    else:
        response = {
            'message': 'Our chain is autoritative',
            'chain': block_chain.chain
        }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
