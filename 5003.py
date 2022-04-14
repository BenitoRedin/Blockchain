# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 15:47:25 2022

@author: benit
"""

# Importar librerias
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Parte 1 - Crear una cadena de Bloques
class Blockchain:
    # Cadena iniciada
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        
    # Bloque creado(con sus datos)
    def create_block(self, proof, previous_hash):
        block = {'index' : len(self.chain)+1,
                 'timestamp' : str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    # Variable del bloque previo
    def get_previous_block(self):
        return self.chain[-1]
    # Proof of work
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else: 
                new_proof += 1
        return new_proof
    # Hash
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    # Validacion de la cadena
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    # Añadir transaccion    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender':sender,
                                  'receiver':receiver,
                                   'amount':amount})
        previous_block = self.get_previous_block()
        return previous_block['index']+1
    # Añadir nodo
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    
    
    # Reemplazar la cadena por la mas larga
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_lenght = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')            
            if response.status_code == 200:
                 length = response.json()['length']
                 chain = response.json()['chain']
                 if length > max_lenght and self.is_chain_valid(chain):
                     max_lenght = length
                     longest_chain = chain
            if longest_chain: 
                self.chain = longest_chain
                return True
            return False
# Parte 2 - Minar un Bloque de la Cadena

# Crear web
app = Flask(__name__)

# Direccion de nodos
node_address = str(uuid4()).replace('-','')

# Crear  Blockchain
blockchain = Blockchain()

# Minar
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # Recompensa
    blockchain.add_transaction(sender = node_address, receiver = "Hadelin", amount = 5)
    # Crear Nuevo Bloque
    block = blockchain.create_block(proof, previous_hash)
    response = {'message' : '¡Enhorabuena, has minado un nuevo bloque!', 
                'index': block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200
# Obtener cadena completa
@app.route('/get_chain',methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'lenght': len(blockchain.chain)}
    return jsonify(response), 200
# Comprobar si es valido
@app.route('/is_valid', methods=['GET'])
def is_valid():
    if blockchain.is_chain_valid(blockchain.chain)==True:
        response = {'message' :'La cadena es valida'}
    else:
        response = {'message' :'La cadena NO es valida'}
    
    return jsonify(response), 200

# Añadir Transaccion
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all(key in json for key in transaction_keys):
        return 'Faltan elementos de la transaccion', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])  
    response = {'message': f'Transaccion añadida al bloque {index}'} 
    return jsonify(response),201     

# Parte 3 - Descentralizar la cadena de bloques

# Conectar nuevos nodos
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No hay nodos', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'Nodo/s conectados. Actualmente estan conectados los siguientes nodos: ',
                'total_nodes' : list(blockchain.nodes)}
    
    return jsonify(response),201     

# Reemplazo de la cadena por la mas larga
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced():
        response = {'message' :'La cadena ha sido reemplazada por la más larga',
                    'new_chain': blockchain.chain}
    else:
        response = {'message' :'Todo igual, la cadena actual sigue siendo la más larga',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Ejecutar
app.run(host = '0.0.0.0', port = 5003)

