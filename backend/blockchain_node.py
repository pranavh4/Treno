import sys
sys.path.append('./backend')

from lib.transaction import Transaction
from lib.wallet import Wallet

keys = Wallet.generate_key()

t = Transaction(keys['public_key'],"hegde",10)
t.signTransaction(keys['private_key'])
t.validateSignature()
str(t)

t.amount = 20
t.validateSignature()


from lib.block import Block
block = Block([t],t)
str(block)