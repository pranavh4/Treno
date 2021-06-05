from .blockchain import Blockchain

class BlockExplorer():
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain

    def getBlocks(self, endHeight: int, numBlocks: int):
        #endHeight - height of the block, if -1 it'll be most recent block height
        #startHeight will be endHeight - minBlocks
        if endHeight == -1:
            endHeight = len(self.blockchain.mainChain)
        startHeight = endHeight - numBlocks
        if startHeight < 0:
            startHeight = 0
        blocks = [self.blockchain.blocks[self.blockchain.mainChain[i]] for i in self.blockchain.mainChain[startHeight:endHeight]]
        return {"blocks": blocks}

        