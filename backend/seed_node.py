from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/getNodes', methods=['GET'])
def getNodes():
    return jsonify({"activeNodes":nodes})

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

if __name__ == "__main__":
    nodes=[]
    app.run(host='127.0.0.1', port=8001,debug=True)