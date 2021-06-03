import requests
import json
import random
from flask import jsonify
import math
from lib.block import Block
class P2P:

    seed_url='http://localhost:8001'

    @staticmethod
    def registerNode(port):
        payload = {"address" : '127.0.0.1:'+str(port)}
        response = requests.post(url=P2P.seed_url+'/registerNode',json=payload)
        return json.loads(response.text)

    @staticmethod
    def deleteNode(port):
        payload = {"address" : '127.0.0.1:'+str(port)}
        response = requests.post(url=P2P.seed_url+'/deleteNode',json=payload)
        return json.loads(response.text)
    
    @staticmethod
    def fetchNodes():
        response = requests.get(url=P2P.seed_url + "/getNodes")
        nodes = response.json()["activeNodes"]
        return nodes

    @staticmethod
    def fetchBlocks(blockChain,blockHash,limit):
        blocks = []
        index = blockChain.mainChain.index(blockHash)
        for blockHash in blockChain.mainChain[index:index+limit]:
            blocks.append(blockChain.blocks[blockChain.mainChain[blockHash]])
        return blocks
    
    @staticmethod
    def getGenesisNodeTimestamp():
        response = requests.get(f"{P2P.seed_url}/getGenesisNodeTimestamp").json()
        return response["genesisNodeTimestamp"]
    
    @staticmethod
    def setGenesisNodeTimestamp(timestamp):
        print(f"Sending Genesis Node timestamp to Seed Node {timestamp}")
        response = requests.post(url=f"{P2P.seed_url}/setGenesisNodeTimestamp",json={"genesisNodeTimestamp":timestamp}).json()
        if response["status"]=="Success":
            print("Set genesis node timestamp successfully")
            return 1
        else:
            print("Error occurred in setting timestamp")
            return 0

    @staticmethod
    def syncNode(blockChain,limit,nodes):
        payload = {}
        lastBlockHash = blockChain.mainChain[-1]
        payload["blockHash"] = lastBlockHash
        payload["limit"] = limit

        chosenNode = random.choice(nodes)
        fetchBlockHeightURL = f"http://{chosenNode}/fetchBlockHeight"

        blockHeight = requests.get(fetchBlockHeightURL).json()["blockHeight"]
        
        fetchBlocksUrl = f"http://{chosenNode}/fetchBlocks"
        blocksFetched = 0

        while blocksFetched < blockHeight:
            if limit+blocksFetched <= blockHeight:
                payloadLimit=limit
            else:
                payloadLimit = blockHeight - blocksFetched
            payload["limit"] = payloadLimit
            payload["blockHash"] = blockChain.mainChain[-1]
            blocks = requests.post(fetchBlocksUrl,data=payload).json()["blocks"]
            for block in blocks:
                blockChain.addBlock(block)
            blocksFetched+=payloadLimit

        print("Sync Node completed")
        