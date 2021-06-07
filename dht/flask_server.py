from configparser import ConfigParser
import flask
from flask.wrappers import Request
from blockchain.blockchain import accounts, Blockchain, Block
from flask import Flask, Response, render_template, jsonify, request, redirect
from flask_cors import CORS, cross_origin
import shutil
import asyncio
from DataController import *
from blockchain.dns_utils import domain_find
import json

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
   if request.args.get('empty') is not None:
      value = flask_variables.dht.chain.create_block(True)
   else:
      value = flask_variables.dht.chain.create_block()
   return jsonify({"data": value })

@app.route('/bootstrap')
def bootstrap():
   asyncio.run_coroutine_threadsafe(flask_variables.dht.node.bootstrap(flask_variables.send_nodes), flask_variables.dht.loop)
   return jsonify({"data": "Done"})

@app.route('/reset')
def reset():
   db.execute("drop table blockchain")
   db.execute("delete from dht_data")
   db.execute("delete from transactions")
   db.execute("delete from accounts")
   db.execute("delete from blocks")
   # db.execute("delete from network_nodes_list")
   db.execute("""
         CREATE TABLE IF NOT EXISTS transactions 
         (sender CHAR(460), receiver CHAR(460),
         private_key CHAR(1732), signature TEXT,
         extra TEXT, amount REAL, fee REAL,
         category CHAR(16))
   """)
   db.execute("""
      insert into transactions (amount, fee, category, sender, receiver, private_key, extra) values 
      (1,0,'domain',
      '-----BEGIN PUBLIC KEY-----$$MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1UN6XU6w6k7Rikx/4XIr$$MkzBpAVKPchHIrbrQ0BGoxznFL2NiFm60e5eo/a6DXlY9/H72N2A9/RohKf+5sVI$$AnnNkCl3Z+junWbUpUSEQgP7HU8lcenVZTYxPjzy8WlceM79Z719bPNjemBrqLvC$$aR0ZOgH6kyHUVh+LudPMsiTyeWdZB3UA1pvUqQvkfRrXW2NOsdejON+4GK2KTgOi$$nvL/L29cS6htRSrm2JASdU0awPqifwGiQbT1NE6ZFhPcY0UXBkJOK8hO0uOJcnzx$$6oyL3SwOO54/dRkm7y+9W7LuUy6s0765NWRAR4FN4BqGXAsQTk1CPfkdSyY4Axip$$awIDAQAB$$-----END PUBLIC KEY-----$$',
      '0','-----BEGIN PRIVATE KEY-----$$MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDVQ3pdTrDqTtGK$$TH/hcisyTMGkBUo9yEcitutDQEajHOcUvY2IWbrR7l6j9roNeVj38fvY3YD39GiE$$p/7mxUgCec2QKXdn6O6dZtSlRIRCA/sdTyVx6dVlNjE+PPLxaVx4zv1nvX1s82N6$$YGuou8JpHRk6AfqTIdRWH4u508yyJPJ5Z1kHdQDWm9SpC+R9GtdbY06x16M437gY$$rYpOA6Ke8v8vb1xLqG1FKubYkBJ1TRrA+qJ/AaJBtPU0TpkWE9xjRRcGQk4ryE7S$$44lyfPHqjIvdLA47nj91GSbvL71bsu5TLqzTvrk1ZEBHgU3gGoZcCxBOTUI9+R1L$$JjgDGKlrAgMBAAECggEAOP4Bc3IWIWfS46yx+CO0m4qbrSOkxYICUKqlkKFavzh4$$ILjPXALuxC95p0PGUNd/CTPn4/q9/oWYcOscWbubFN5MKxyJxoEfU30pkskOtz2t$$HBYMobalypiC7GkJW66Wgcp/OfwPys/4Y7nky4Dx4XlfRntE5ZEC18kyZATQDUMJ$$g2/Mr0o8OEeGJG2VuPXuE8QB2mJ0gJ9MoD6Y57eX2gIdQv8/i/hwWNlWJf3TjML8$$bc6/gpoHSKAjbKHtnSFpGAqvFyhvBeVwrn84vrm3JzUKKMr9ARTmGkqHeX1HQTuQ$$/j+j14nZtNPuNTDAQcrowLRlerKp4OaHKqfpBSl0UQKBgQDv9/eL9o5ENDGdIyAX$$1G3whAOqFA9qKgvp7yQvi9e1B0AdkzwljHv4/ZDUShGyb+39O1kosFOBCb26WlqJ$$0MJPGLgf4W81RJMqa279Wu1tfHAayKQt3iYEteYbgNIkJhiowWk2s3UWDrTMw5qo$$rZbggcBT/vUMo8UKVShvztIVTQKBgQDjgsqg6DlFWmp5TL5tLGhkUSkCvkkZ/vTS$$O39W+5RUARZB60yUr64ScdloTx2ASVUKoBluj9WY1WXhATlIFfHlUnJvECJRb7jy$$4hAj7tTNlrbGplx3npqXUBKZPmlH9hhLkKa0yTvokkVYx3my/NpvVl9XutXCi282$$hWV6miX9lwKBgQCuqDiQsn+RvLtvt6UgMwlhyXQxUjB2AOxy9A/OW2ZA6GoOHJ/m$$ZH3HGCdVnCONUFJTweJ+7veYL9Lb0++Z50vF7iP1cEtU5fiHI3LBDHFLAwtFM0vr$$5oidXReCZRyOGvxPt5YwriVGTKXjc2sZ4l6yQT4O5L7O2FQN1TV9S3c08QKBgQDH$$82UecboTx9kX7mjWDldZAzNl49LfdAG62uuZiNXd1m63VJMjghscvs5yLEYjP0/s$$XLS9RNBW2AYH8Elln1PPVdyY27ctl2EWpbPFwNtqLHFKuV8/CjeXkJon8IAa7KCB$$mQnKjamHRzaHRhkhQ7S+cUyuD9haeK0vX6HGVL/a1QKBgDgD9Bx68aTEeHajgv01$$pa8n123ffbPIJxepPDN1UvhTbh9MtMOFzsPOzA4M2E9imwLUZItF2zfNZh7RXu1G$$00V9gbsNvu6bwPKoMNIlWgr/seJ6pc5id0jhKAkSNmVRC+FF3NM1qBxBlYXZTvzy$$87DuSYxAg5oXK8X06+t+WYtN$$-----END PRIVATE KEY-----$$',
      'helloworld.iki:172.25.48.135:80')
   """)
   db.execute("""
      insert into accounts (key, value) values ('-----BEGIN PUBLIC KEY-----$$MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1UN6XU6w6k7Rikx/4XIr$$MkzBpAVKPchHIrbrQ0BGoxznFL2NiFm60e5eo/a6DXlY9/H72N2A9/RohKf+5sVI$$AnnNkCl3Z+junWbUpUSEQgP7HU8lcenVZTYxPjzy8WlceM79Z719bPNjemBrqLvC$$aR0ZOgH6kyHUVh+LudPMsiTyeWdZB3UA1pvUqQvkfRrXW2NOsdejON+4GK2KTgOi$$nvL/L29cS6htRSrm2JASdU0awPqifwGiQbT1NE6ZFhPcY0UXBkJOK8hO0uOJcnzx$$6oyL3SwOO54/dRkm7y+9W7LuUy6s0765NWRAR4FN4BqGXAsQTk1CPfkdSyY4Axip$$awIDAQAB$$-----END PUBLIC KEY-----$$', 20)
   """)
   flask_variables.dht.chain = Blockchain(flask_variables.dht, config.getboolean('blockchain', 'miner'))
   asyncio.run_coroutine_threadsafe(flask_variables.dht.node.bootstrap(flask_variables.send_nodes), flask_variables.dht.loop)

   return jsonify({"data": "OK, lol"})

@app.route('/reset_t')
def reset_t():
   db.execute("delete from transactions")
   db.execute("""
         CREATE TABLE IF NOT EXISTS transactions 
         (sender CHAR(460), receiver CHAR(460),
         private_key CHAR(1732), signature TEXT,
         extra TEXT, amount REAL, fee REAL,
         category CHAR(16))
   """)
   if request.args.get('add') is not None:
      db.execute("""
         insert into transactions (amount, fee, category, sender, receiver, private_key, extra) values 
         (1,0,'domain',
         '-----BEGIN PUBLIC KEY-----$$MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1UN6XU6w6k7Rikx/4XIr$$MkzBpAVKPchHIrbrQ0BGoxznFL2NiFm60e5eo/a6DXlY9/H72N2A9/RohKf+5sVI$$AnnNkCl3Z+junWbUpUSEQgP7HU8lcenVZTYxPjzy8WlceM79Z719bPNjemBrqLvC$$aR0ZOgH6kyHUVh+LudPMsiTyeWdZB3UA1pvUqQvkfRrXW2NOsdejON+4GK2KTgOi$$nvL/L29cS6htRSrm2JASdU0awPqifwGiQbT1NE6ZFhPcY0UXBkJOK8hO0uOJcnzx$$6oyL3SwOO54/dRkm7y+9W7LuUy6s0765NWRAR4FN4BqGXAsQTk1CPfkdSyY4Axip$$awIDAQAB$$-----END PUBLIC KEY-----$$',
         '0','-----BEGIN PRIVATE KEY-----$$MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDVQ3pdTrDqTtGK$$TH/hcisyTMGkBUo9yEcitutDQEajHOcUvY2IWbrR7l6j9roNeVj38fvY3YD39GiE$$p/7mxUgCec2QKXdn6O6dZtSlRIRCA/sdTyVx6dVlNjE+PPLxaVx4zv1nvX1s82N6$$YGuou8JpHRk6AfqTIdRWH4u508yyJPJ5Z1kHdQDWm9SpC+R9GtdbY06x16M437gY$$rYpOA6Ke8v8vb1xLqG1FKubYkBJ1TRrA+qJ/AaJBtPU0TpkWE9xjRRcGQk4ryE7S$$44lyfPHqjIvdLA47nj91GSbvL71bsu5TLqzTvrk1ZEBHgU3gGoZcCxBOTUI9+R1L$$JjgDGKlrAgMBAAECggEAOP4Bc3IWIWfS46yx+CO0m4qbrSOkxYICUKqlkKFavzh4$$ILjPXALuxC95p0PGUNd/CTPn4/q9/oWYcOscWbubFN5MKxyJxoEfU30pkskOtz2t$$HBYMobalypiC7GkJW66Wgcp/OfwPys/4Y7nky4Dx4XlfRntE5ZEC18kyZATQDUMJ$$g2/Mr0o8OEeGJG2VuPXuE8QB2mJ0gJ9MoD6Y57eX2gIdQv8/i/hwWNlWJf3TjML8$$bc6/gpoHSKAjbKHtnSFpGAqvFyhvBeVwrn84vrm3JzUKKMr9ARTmGkqHeX1HQTuQ$$/j+j14nZtNPuNTDAQcrowLRlerKp4OaHKqfpBSl0UQKBgQDv9/eL9o5ENDGdIyAX$$1G3whAOqFA9qKgvp7yQvi9e1B0AdkzwljHv4/ZDUShGyb+39O1kosFOBCb26WlqJ$$0MJPGLgf4W81RJMqa279Wu1tfHAayKQt3iYEteYbgNIkJhiowWk2s3UWDrTMw5qo$$rZbggcBT/vUMo8UKVShvztIVTQKBgQDjgsqg6DlFWmp5TL5tLGhkUSkCvkkZ/vTS$$O39W+5RUARZB60yUr64ScdloTx2ASVUKoBluj9WY1WXhATlIFfHlUnJvECJRb7jy$$4hAj7tTNlrbGplx3npqXUBKZPmlH9hhLkKa0yTvokkVYx3my/NpvVl9XutXCi282$$hWV6miX9lwKBgQCuqDiQsn+RvLtvt6UgMwlhyXQxUjB2AOxy9A/OW2ZA6GoOHJ/m$$ZH3HGCdVnCONUFJTweJ+7veYL9Lb0++Z50vF7iP1cEtU5fiHI3LBDHFLAwtFM0vr$$5oidXReCZRyOGvxPt5YwriVGTKXjc2sZ4l6yQT4O5L7O2FQN1TV9S3c08QKBgQDH$$82UecboTx9kX7mjWDldZAzNl49LfdAG62uuZiNXd1m63VJMjghscvs5yLEYjP0/s$$XLS9RNBW2AYH8Elln1PPVdyY27ctl2EWpbPFwNtqLHFKuV8/CjeXkJon8IAa7KCB$$mQnKjamHRzaHRhkhQ7S+cUyuD9haeK0vX6HGVL/a1QKBgDgD9Bx68aTEeHajgv01$$pa8n123ffbPIJxepPDN1UvhTbh9MtMOFzsPOzA4M2E9imwLUZItF2zfNZh7RXu1G$$00V9gbsNvu6bwPKoMNIlWgr/seJ6pc5id0jhKAkSNmVRC+FF3NM1qBxBlYXZTvzy$$87DuSYxAg5oXK8X06+t+WYtN$$-----END PRIVATE KEY-----$$',
         'helloworld.iki:172.25.48.135:80')
      """)
   return jsonify({"data": "OK, lol"}), 200, {'Content-Type': 'application/text'}

@app.route('/get', methods=['GET', 'POST'])
@cross_origin()
def get():
   if request.args.get('domain') is not None:
      domain = request.args.get('domain')
      print("request " + domain)
      result = domain_find(flask_variables.dht.chain, domain)
      if result is None:
         print("domain request failed")
         ip = "0.0.0.0"
      else:
         ip = result[1]
         port = result[2]
      xml = '<?xml version="1.0" encoding="utf-8"?><domain><ip>' + ip + '</ip></domain><!-- Not cached -->'
      return Response(xml, mimetype="application/xml")

   elif request.args.get('key') is not None:
      return str(flask_variables.dht.get(request.args.get('key')))

   return "Invalid get request"

@app.route('/')
def index():
   data = {
      "node_id": config.get('node', 'id'),
      "public_key": config.get('keys', 'public_key').replace('$$', '\n'),
      "private_key": config.get('keys', 'private_key').replace('$$', '\n'),
      "server_port": config.get('server', 'port'),
      "chain_miner": config.get('blockchain', 'miner'),
      "flask_port": config.get('flask', 'port'),
      "public_copy": config.get('keys', 'public_key'),
      "balance": accounts[config.get('keys', 'public_key')]
   }
   return render_template('user_data.html', data=data, active="dashboard")

@app.route('/list_blockchains')
def list_blockchains():
   lb = flask_variables.dht.chain.last_blocks[flask_variables.dht.chain.id]
   blockchain = []
   for i in range(lb.id + 1):
      blk = flask_variables.dht.chain.chain_find(i)
      blk.hash = blk.hash()
      blockchain.append(blk)
   return render_template('blockchain.html', blockchain=blockchain, active="blockchain")

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
   if "receiver_id" in request.form and "category" in request.form and "amount" in request.form:
      sender = config.get('keys', 'public_key')
      private_key = config.get('keys', 'private_key')
      extras = None
      db.execute('insert into transactions (amount, fee, category, sender, receiver, private_key, extra) values(?,?,?,?,?,?,?)', (request.form['amount'], 0.0, request.form['category'], sender, request.form['receiver_id'], private_key, extras))
      return redirect('display_transactions')
   if "public_key" in request.form:
      public_key = request.form["public_key"]
      print(public_key)
      return render_template('add_transaction.html', public_key=public_key, active="transactions")
   else:
      return render_template('add_transaction.html', active="transactions")

@app.route('/register_domain', methods=['GET','POST'])
def register_domain():
   if "domain_name" in request.form and "IP" in request.form:
      sender = config.get('keys', 'public_key')
      private_key = config.get('keys', 'private_key')
      extras = request.form['domain_name'] + ":" + request.form['IP'] + ":80"
      db.execute('insert into transactions (amount, fee, category, sender, receiver, private_key, extra) values(?,?,?,?,?,?,?)', (1.0, 0.0, 'domain', sender, '0', private_key, extras))
   return render_template('register_domain.html', active="register")   


@app.route('/register_contact', methods=['GET', 'POST'])
def register_contact():
   if "receiver_id" in request.form and "receiver_name" in request.form:
      id =  request.form["receiver_id"]
      name = request.form["receiver_name"]
      contact = SQLiteHashTable('contacts')
      contact[id] = name
      print(request.args.items())
      return redirect("all_contact")
   else:
      return render_template('register_contact.html', active="contacts")

@app.route('/all_contact', methods=['GET', 'POST'])
def all_contact():
   contact = SQLiteHashTable('contacts')
   data = []
   for id, name in contact.fetchall():
      person={
         "id": id,
         "name": name
      }
      data.append(person)
   return render_template('all_contacts.html', data=data, active="contacts")

@app.route('/delete_contact')
def delete_contact():
   if request.args.get("public_key"):
      public_key = request.args.get("public_key")
      contact = SQLiteHashTable('contacts')
      contact.delete_key(public_key)
   return redirect('all_contact')

@app.route('/display_transactions')
def display_transactions():
   cur = db.con.cursor()
   cur.execute("SELECT * from transactions")
   transactions = []
   for transaction in cur:
      row = {
         "amount": transaction['amount'],
         "fee": transaction['fee'],
         "category": transaction['category'],
         "sender": transaction['sender'],
         "receiver": transaction['receiver'],
         "private_key": transaction['private_key'],
         "extra": transaction['extra']
      }
      transactions.append(row)
   cur.close()
   return render_template('all_transactions.html', transactions=transactions, active="transactions")


@app.route('/fetch')
def fetch():
   if "block_id" in request.form:
      block_id = request.form["block_id"]
      value = flask_variables.dht.get(block_id)
      data = json.loads(value)
      blockchain = []
      if data['type'] == 'block':
         args = json.loads(data['data'])
         block = Block(args['id'], args['prev_hash'], args['miner'], args['timestamp'], args['nonce'], args['data'])
         if flask_variables.dht.chain.accept_block(block, data['store'] or None, False):
            blockchain.append(block)
      return render_template('blockchain.html', blockchain=blockchain, active="blockchain")
   return render_template('fetch_block.html')