import sys
sys.path.append('./backend')

from lib.transaction import Transaction
from lib.wallet import Wallet

keys = Wallet.generate_key()

t = Transaction(keys['public_key'],"hegde",10)
t.sign_transaction(keys['private_key'])
t.validate_signature()
str(t)

t.amount = 20
t.validate_signature()