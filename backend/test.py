from hashlib import sha256
import time, math

def getHitValue(generationSignature: str, publicKey: str) -> int:
    hashValue = sha256(bytes(generationSignature + publicKey, encoding='utf-8')).hexdigest()
    hitValue = int(hashValue[:8],16)
    return hitValue

def getHitTime(effectiveBalance: int, hitValue: int) -> int:
    global timestamp, baseTarget
    hitTime = timestamp + (hitValue / (effectiveBalance * baseTarget))
    return int(math.floor(hitTime))

index = 0
slist = [60]
baseTarget = 153722867
generationSignature = "0000000000000000000000000000000000000000000000000000000000000000"
pubKey = "30819f300d06092a864886f70d010101050003818d0030818902818100cb8d1b8ae3f9e568284f181f3c5fc2cf98c2e13a9f21734fa41a33bed6745e93f95c6f44e27a5f9992981c3d1bd613166f8bbf9a2245f576deb91049354635887c62eeb22969ef63a7b5fc2c53701b067dcc9425e11dac183f3328c4b64dd6493b454b09b9d24e228acd8f8795ce673b4804549a4c9de6dca9511252bb5e97530203010001"
MAXRATIO = 67
MINRATIO = 53
GAMMA = 0.64
timestamp = int(time.time())
while index<20:
    s = 0
    temp = slist[index:index+3]
    for t in temp:
        s+=t
    s/=(len(temp))
    print("s:" + str(s))
    if s > 60:
        baseTarget = int((baseTarget * min(s, MAXRATIO))/60)
    else:
        baseTarget =  int(baseTarget - (baseTarget * GAMMA*(60 - max(s, MINRATIO)))/60)
    print("baseTarget: " + str(baseTarget))
    index+=1
    hit = getHitValue(generationSignature, pubKey)
    print("Hit: " + str(hit))
    hitTime = getHitTime(1,hit)
    print("timetamp: " + str(timestamp) + " hit time: " + str(hitTime) + "diff: " + str(hitTime - timestamp))
    slist.append(hitTime - timestamp)
    timestamp = hitTime

