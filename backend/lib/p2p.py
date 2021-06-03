import requests
import json
import random
import math
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
        