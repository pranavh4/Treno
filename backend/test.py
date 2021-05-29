from lib.mining_thread import MiningThread

t = MiningThread("thread1")
t2 = MiningThread("thread2")
t.start()
t2.start()