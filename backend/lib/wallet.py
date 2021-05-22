from typing import Dict
import binascii
import Crypto
from Crypto.PublicKey import RSA

class Wallet:
    @staticmethod
    def generate_key() -> Dict:
        random_gen = Crypto.Random.new().read
        private_key = RSA.generate(1024, random_gen)
        public_key = private_key.publickey()
        keys = {
            'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
            'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
        }
        return keys
