from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
def validateSignature(input, signer, signature) -> bool:
    public_key = RSA.importKey(binascii.unhexlify(signer))
    verifier = PKCS1_v1_5.new(public_key)
    # txId = transaction.getHash()
    h = SHA.new(input.encode('utf8'))
    return verifier.verify(h, binascii.unhexlify(signature))

def generateSignature(input, privateKey) -> str:
    privateKey = RSA.importKey(binascii.unhexlify(privateKey))
    signer = PKCS1_v1_5.new(privateKey)
    h = SHA.new(input.encode('utf8'))
    return binascii.hexlify(signer.sign(h)).decode('ascii')