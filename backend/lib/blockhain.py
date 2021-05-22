class Blockhain:
    def __init__(self):
        self.chain = {}
        self.transactionPool = {}
        
    
    def addBlock(self, block) -> bool:
        