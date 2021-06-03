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
   if request.args.get('domain') is not None:
      domain = request.args.get('domain')
      print("request " + request.args.get('domain'))
      result = flask_variables.dht.chain.domain_find(request.args.get('domain'))
      if result is None:
         print("domain request failed")
         ip = "0.0.0.0"
      else:
         ip = result[0]
         port = result[1]
      xml = '<?xml version="1.0" encoding="utf-8"?><domain><ip>' + ip + '</ip></domain><!-- Not cached -->'
      return Response(xml, mimetype="application/xml")

   elif request.args.get('key') is not None:
      return str(flask_variables.dht.get(request.args.get('key')))

   return "Invalid get request"

@app.route('/')
def index():
   data = {
      "node_id":"1234567890",
      "public_key":"vqon1h0gaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "private_key":"13hr0h1",
      "server_port":"5678",
      "chain_miner":"True",
      "flask_port":"500"
   }
   return render_template('user_data.html', data = data)

@app.route('/list_blockchains')
def list_blockchains():
   blockchain = [
      {
         'id':'9876543210',
         'prev_hash':'hash not found',
         'miner':'None',
         'timestramp':'03/06/2021',
         'nonce':'987789',
         'data':[
            {'amount':'1000',
             'fee':'Rs.2', 
             'category':'Islam',
             'sender':'Ammar',
             'receiver':'Hashir',
             'time':'14/01/1999',
             'signature':'xtz',
             'extra':'Fraz'
            }
         ]
      },
      {
         'id':'9876543210',
         'prev_hash':'hash not found',
         'miner':'None',
         'timestramp':'03/06/2021',
         'nonce':'987789',
         'data':[
            {'amount':'1000',
             'fee':'Rs.2', 
             'category':'Islam',
             'sender':'Ammar',
             'receiver':'Hashir',
             'time':'14/01/1999',
             'signature':'xtz',
             'extra':'Fraz'
            }
         ]
      }
   ]
   return render_template('blockchain.html', blockchain = blockchain)

@app.route('/add_transaction')
def add_transaction():
   return render_template('add_transaction.html')

@app.route('/transaction_inserted', methods=['GET', 'POST'])
def transaction_inserted():
   id = request.form['receiver_id']
   category = request.form['category']
   amount = request.form['amount']
   print(id)
   print(category)
   print(amount)
   return render_template('add_transaction.html')

@app.route('/register_domain')
def register_domain():
   return render_template('register_domain.html')   

@app.route('/domain_registered', methods=['GET','POST'])
def domain_registered():
   domain = request.form['domain_name']
   IP = request.form['IP']
   print(domain + " " + IP)
   return render_template('register_domain.html')

@app.route('/submit_button')
def submit_button():
   return render_template('index.html')
