from lib.transaction import TransactionInput,Transaction, TransactionOutput
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from lib.blockchain import Blockchain

app = Flask(__name__)
CORS(app)

blockhain = Blockchain()
blockhain.createGenesisBlock()

@app.route("/getUtxo", methods = ['POST'])
def getUtxo():
    sender = request.json["sender"]
    return jsonify({"utxo": blockhain.utxoPool[sender]})

@app.route("/transactions/add", methods = ['POST'])
def addTransaction():
    reqData = request.json
    txIn, txOut = [],[]
    for iTx in reqData["txIn"]:
        txIn.append(TransactionInput(iTx["txId"],iTx["outputIndex"],iTx["signature"]))
    for oTx in reqData["txOut"]:
        txOut.append(TransactionOutput(oTx["amount"],oTx["receiver"]))
    transaction = Transaction(txIn,txOut)
    print(blockhain.verifyTransaction(transaction))
    return jsonify({"status":"Success"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)