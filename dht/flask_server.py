from configparser import ConfigParser
from flask.wrappers import Request
from blockchain.blockchain import Transaction, Blockchain, Block
from flask import Flask, Response, render_template, jsonify, request
from flask_cors import CORS, cross_origin
import shutil
import asyncio

config = ConfigParser()
config.read('config.ini')

class FlaskVariables:
   def set(self, dht, send_nodes):
      self.dht = dht
      self.send_nodes = send_nodes

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
flask_variables = FlaskVariables()

@app.route('/create')
def create():
   return str(flask_variables.dht.chain.create_block())

@app.route('/bootstrap')
def bootstrap():
   return str(flask_variables.dht.node.bootstrap(flask_variables.send_nodes))

@app.route('/reset')
def reset():
   shutil.copyfile('templates\\accounts_o.txt', 'accounts.txt')
   shutil.copyfile('templates\\blockchain_o.txt', 'blockchain.txt')
   shutil.copyfile('templates\\kademlia_o.csv', 'kademlia.csv')
   shutil.copyfile('templates\\transactions_o.txt', 'transactions.txt')
   open('network_nodes_list.txt', 'w').close()
   flask_variables.dht.chain = Blockchain(flask_variables.dht, Block(0, None), config.getboolean('blockchain', 'miner'))
   asyncio.run_coroutine_threadsafe(flask_variables.dht.node.bootstrap(flask_variables.send_nodes), flask_variables.dht.loop)
   return str("OK, lol")

@app.route('/reset_t')
def reset_t():
   shutil.copyfile('templates\\transactions_o.txt', 'transactions.txt')
   return jsonify({"data": "OK, lol"}), 200, {'Content-Type': 'application/text'}

@app.route('/get', methods=['GET', 'POST'])
@cross_origin()
def get():
   # if request.args.get('key') is None:
   #    return str("wth to get? stupid")

   if request.args.get('domain') is not None:
      domain = request.args.get('domain')
      print(" bondu///////////////////////////////////////////////////////")
      xml = '<?xml version="1.0" encoding="utf-8"?><domain><ip>172.25.48.135</ip></domain><!-- Not cached -->'
      return Response(xml, mimetype="application/xml")
   else:
      return str(flask_variables.dht.get(request.args.get('key')))

@app.route('/')
def index():
   return render_template('index.html')