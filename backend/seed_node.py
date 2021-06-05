from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import random

app = Flask(__name__)
CORS(app)

GENESIS_NODE_TIMESTAMP = -1

@app.route('/getNodes', methods=['GET'])
def getNodes():
    return jsonify({"activeNodes":nodes})

@app.route('/getRandomNode', methods = ['GET'])
def getRandomNode():
    node = random.choice(nodes)
    payload = {}
    payload["node"] = node
    return jsonify(payload)

@app.route('/registerNode',methods=['POST'])
def registerNode():
    requestData = request.json
    remote_addr = requestData["address"]
    print("Received request from: "+remote_addr)
    if remote_addr not in nodes:
        nodes.append(remote_addr)
    return jsonify({"status":"Success"})
    
@app.route('/deleteNode',methods=['POST'])
def deleteNode():
    requestData = request.json
    remote_addr = requestData["address"]
    print("Received request from: "+remote_addr)
    if remote_addr in nodes:
        nodes.remove(remote_addr)
    return jsonify({"status":"Success"})

@app.route("/printStatus",methods=['POST'])
def printStatus():
    requestData = request.json
    nodes = requestData["nodes"]
    resp = []
    for node in nodes:
        addr = "http://127.0.0.1:"+str(node) + "/getBlockChain"
        blockChain = requests.get(addr).json()
        blockChain["Node"]= str(node)
        resp.append(blockChain)
    return jsonify({"status":resp})

@app.route("/getGenesisNodeTimestamp")
def getGenesisNode():
    global GENESIS_NODE_TIMESTAMP
    return jsonify({"genesisNodeTimestamp":GENESIS_NODE_TIMESTAMP})

@app.route("/setGenesisNodeTimestamp",methods = ["POST"])
def setGenesisNode():
    global GENESIS_NODE_TIMESTAMP
    requestData = request.json
    print("Received request to add block timestamp")
    print(requestData)
    print("Inside set genesis Node")
    if GENESIS_NODE_TIMESTAMP != -1:
        print("Genesis Node Timestamp already Exists")
        return jsonify({"status":"Failure"})
    else:
        GENESIS_NODE_TIMESTAMP = requestData["genesisNodeTimestamp"]
    return jsonify({"status":"Success"})

if __name__ == "__main__":
    nodes=[]
    app.run(host='127.0.0.1', port=8001)