from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii

def validateSignature(transaction, signer, signature) -> bool:
    public_key = RSA.importKey(binascii.unhexlify(signer))
    verifier = PKCS1_v1_5.new(public_key)
    txId = transaction.getHash()
    h = SHA.new(txId.encode('utf8'))
    return verifier.verify(h, binascii.unhexlify(signature))