from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii

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