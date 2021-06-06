from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from .task import TaskSolution,Task
    from .transaction import Transaction
    from .blockchain import Blockchain

import requests
import json
import random
from flask import jsonify
import math
from .utils import bcolors
from threading import get_ident
from werkzeug import exceptions
from lib.block import Block
class P2P:

    seed_url='http://localhost:8001'
    port = 5000

    @staticmethod
    def setP2PPort(port):
        P2P.port = port
    
    @staticmethod
    def registerNode():
        payload = {"address" : '127.0.0.1:'+str(P2P.port)}
        response = requests.post(url=P2P.seed_url+'/registerNode',json=payload)
        return json.loads(response.text)

    @staticmethod
    def deleteNode():
        payload = {"address" : '127.0.0.1:'+str(P2P.port)}
        response = requests.post(url=P2P.seed_url+'/deleteNode',json=payload)
        return json.loads(response.text)
    
    @staticmethod
    def fetchNodes():
        response = requests.get(url=P2P.seed_url + "/getNodes")
        nodes = response.json()["activeNodes"]
        if f"127.0.0.1:{P2P.port}" in nodes:
            nodes.remove(f"127.0.0.1:{P2P.port}")
        print(f"({P2P.port}) Fetched Nodes from Seed Node")
        return nodes

    @staticmethod
    def fetchBlocks(blockChain:Blockchain,blockHash,limit):
        blocks = []
        index = blockChain.mainChain.index(blockHash)
        for blockHash in blockChain.mainChain[index+1:index+limit+1]:
            blocks.append(blockChain.blocks[blockHash].toDict())
        # print(f"({P2P.port})Added blocks of index {index+1}, {index+limit}")
        return blocks
    
    @staticmethod
    def getGenesisNodeTimestamp():
        try:
            response = requests.get(f"{P2P.seed_url}/getGenesisNodeTimestamp").json()
        except (requests.exceptions.ConnectionError):
            print("Please run python seed_node.py first")
            exit(1)
        return response["genesisNodeTimestamp"]
    
    @staticmethod
    def setGenesisNodeTimestamp(timestamp):
        print(f"Sending Genesis Node timestamp to Seed Node {timestamp}")
        try:
            response = requests.post(url=f"{P2P.seed_url}/setGenesisNodeTimestamp",json={"genesisNodeTimestamp":timestamp}).json()
        except (requests.exceptions.ConnectionError):
            print("Please run python seed_node.py first")
            exit(1)
        if response["status"]=="Success":
            print("Set genesis node timestamp successfully")
            return 1
        else:
            print("Error occurred in setting timestamp")
            return 0

    @staticmethod
    def syncNode(blockChain: Blockchain,limit,nodes:list):
        payload = {}
        lastBlockHash = blockChain.mainChain[-1]
        payload["blockHash"] = lastBlockHash
        payload["limit"] = limit

        chosenNode = random.choice(nodes)
        fetchBlockHeightURL = f"http://{chosenNode}/fetchBlockHeight"
        blockHeight = requests.get(fetchBlockHeightURL).json()["blockHeight"] -1
        print("Height: ",fetchBlockHeightURL,blockHeight)
        fetchBlocksUrl = f"http://{chosenNode}/fetchBlocks"
        blocksFetched = 0

        if blockHeight==len(blockChain.mainChain):
            print(f"Blocks same height as remote node {chosenNode}. Aborting Sync Node")
            return
        
        while blocksFetched < blockHeight:
            if limit+blocksFetched <= blockHeight:
                payloadLimit=limit
            else:
                payloadLimit = blockHeight - blocksFetched
            payload["limit"] = payloadLimit
            payload["blockHash"] = blockChain.mainChain[-1]
            print(payload)
            blocks = requests.post(fetchBlocksUrl,json=payload).json()["blocks"]
            for block in blocks:
                remoteBlock = Block.fromDict(block)
                print(f"Received remote block {remoteBlock.getHash()}")
                added = blockChain.addBlock(remoteBlock)
                if added:
                    print(f"{bcolors.OKGREEN}({P2P.port}) Added remote block {remoteBlock.getHash()} received from {chosenNode}{bcolors.ENDC}")
            blocksFetched+=payloadLimit

        print(f"({P2P.port}) Sync Node with ({chosenNode}) completed. Fetched {blocksFetched} blocks. ")
        
    @staticmethod
    def broadcastBlock(block:Block):
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC}({P2P.port}) Broadcasting Block")
        nodes = P2P.fetchNodes()
        payload={}
        payload["block"]=block.toDict()
        payload["sender"] = P2P.port
        for node in nodes:
            try:
                response = requests.post(url=f"http://{node}/receiveBlock", json = payload)
                if response.json()["status"] == "Success":
                    print(f"{bcolors.OKGREEN}({P2P.port})[broadcastBlock] Received response: Success from {node}{bcolors.ENDC}")
                else:
                    print(f"{bcolors.FAIL}({P2P.port})[broadcastBlock] Received response: Failure from {node}{bcolors.ENDC}")
            except ConnectionError:
                print(f"Node {node} does not exist")
    
    @staticmethod
    def broadcastTransaction(transaction:Transaction,sender):
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC}({P2P.port}) Broadcasting Transaction")
        nodes = P2P.fetchNodes()
        payload = {}
        payload["sender"] = sender
        payload["transaction"] = transaction.toDict()
        payload["from"] = "node"
        for node in nodes:
            try:
                response = requests.post(url=f"http://{node}/transactions/add",json=payload)
                if response.json()["status"] == "Success":
                    print(f"{bcolors.OKGREEN}({P2P.port})[broadcastTransaction] Received response: Success from {node}{bcolors.ENDC}")
                else:
                    print(f"{bcolors.FAIL}({P2P.port})[broadcastTransaction] Received response: Failure from {node}{bcolors.ENDC}")
            except:
                print(f"Node {node} does not exist")
    
    @staticmethod
    def broadcastTask(task:Task):
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC}({P2P.port}) Broadcasting Task")
        nodes = P2P.fetchNodes()
        payload = {}
        payload["task"] = task.toDict()
        payload["from"] = "node"
        for node in nodes:
            try:
                response = requests.post(url=f"http://{node}/tasks/add",json=payload)
                if response.json()["status"] == "Success":
                    print(f"{bcolors.OKGREEN}({P2P.port})[broadcastTask] Received response: Success from {node}{bcolors.ENDC}")
                else:
                    print(f"{bcolors.FAIL}({P2P.port})[broadcastTask] Received response: Failure from {node}{bcolors.ENDC}")
            except ConnectionError:
                print(f"Node {node} does not exist")
    
    @staticmethod
    def broadcastTaskSolution(taskSolution:TaskSolution):
        print(f"{bcolors.WARNING}[ThreadID: {get_ident()}]{bcolors.ENDC}({P2P.port}) Broadcasting Task Solution")
        nodes = P2P.fetchNodes()
        payload = {}
        payload["taskSolution"] = taskSolution.toDict()
        payload["source"] = P2P.port
        for node in nodes:
            try:
                response = requests.post(url=f"http://{node}/taskSolutions/add", json=payload)
                if response.json()["status"] == "Success":
                    print(f"{bcolors.OKGREEN}({P2P.port})[broadcastTaskSolution] Received response: Success from {node}{bcolors.ENDC}")
                else:
                    print(f"{bcolors.FAIL}({P2P.port})[broadcastTaskSolution] Received response: Failure from {node}{bcolors.ENDC}")
            except ConnectionError:
                print(f"Node {node} does not exist")