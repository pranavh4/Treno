from .block import Block
from .mining_thread import MiningThread

def verifyHit(hitValue: int, wstBalance: int, previousBlock: Block, timestamp: int) -> bool:
    elapsedTime = timestamp - previousBlock.timestamp
    if elapsedTime < 0:
        return False
    newTarget = previousBlock.baseTarget*wstBalance*elapsedTime
    return hitValue < newTarget

def verifyGenerationSignature(block: Block, prevBlock: Block) -> bool:
    return MiningThread.getNextGenerationSignature(prevBlock, block.generatorPubKey) == block.generationSignature

def verifyCumulativeDifficulty(block: Block, prevBlock: Block) -> bool:
    return MiningThread.getNextCumulativeDifficulty(prevBlock.cumulativeDifficulty, block.baseTarget,block.generatorPubKey) == block.cumulativeDifficulty

def verifyBaseTarget(blocks: list[Block], newBlock: Block) -> bool:
    return MiningThread.getNextBaseTarget(blocks) == newBlock.baseTarget