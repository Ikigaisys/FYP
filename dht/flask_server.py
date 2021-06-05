from configparser import ConfigParser
import flask
from flask.wrappers import Request
from blockchain.blockchain import Transaction, Blockchain, Block
from flask import Flask, Response, render_template, jsonify, request
from flask_cors import CORS, cross_origin
import shutil
import asyncio
from DataController import *
from blockchain.dns_utils import domain_find

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
   value = flask_variables.dht.chain.create_block()
   return jsonify({"data": value if value != None else "Didn't succeed" })

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
   shutil.copyfile('templates\\kademlia_o.csv', 'kademlia.csv')
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
      print("request " + request.args.get('domain'))
      result = domain_find(flask_variables.dht.chain, request.args.get('domain'))
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
      "public_copy": config.get('keys', 'public_key')
   }
   return render_template('user_data.html', data = data)

@app.route('/list_blockchains')
def list_blockchains():
   lb = flask_variables.dht.chain.last_blocks[flask_variables.dht.chain.id]
   blockchain = []
   blockchain.append(flask_variables.dht.chain.chain_find(0))
   for i in range(lb.id):
      blockchain.append(flask_variables.dht.chain.chain_find(i))
   """   blockchain = [
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
   ]"""
   return render_template('blockchain.html', blockchain = blockchain)

@app.route('/add_transaction')
def add_transaction():
   if request.args.get("public_key"):
      public_key = request.args.get("public_key")
      return render_template('add_transaction.html', public_key=public_key)
   else:
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

@app.route('/register_contact', methods=['GET', 'POST'])
def register_contact():
   if "receiver_id" in request.form and "receiver_name" in request.form:
      id =  request.form["receiver_id"]
      name = request.form["receiver_name"]
      contact = SQLiteHashTable('contacts')
      contact[id] = name
   print(request.args.items())
   return render_template('register_contact.html')

@app.route('/all_contact', methods=['GET', 'POST'])
def all_contact():
   contact = SQLiteHashTable('contacts')
   data = []
   for id, name in contact.fetchall():
      person={
         "id":id,
         "name":name
      }
      data.append(person)
   for i in range(10):
      persons={
         "id": "12345",
         "name": "hashir"
      }
      data.append(persons)
   return render_template('all_contacts.html', data = data)

@app.route('/delete_contact')
def delete_contact():
   if request.args.get("public_key"):
      public_key = request.args.get("public_key")
      contact = SQLiteHashTable('contacts')
      contact.delete_contact(public_key)
   data = []
   contact = SQLiteHashTable('contacts')
   for id, name in contact.fetchall():
      person={
         "id":id,
         "name":name
      }
      data.append(person)
   for i in range(10):
      persons={
         "id": "12345",
         "name": "hashir"
      }
      data.append(persons)
   return render_template('all_contacts.html', data = data)