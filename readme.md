# Treno
A cryptocurreny platform based on the Proof of Solution Algorithm. ([Research Paper](https://ieeexplore.ieee.org/document/9691673))

Proof of Solution aims to utilize the vast infrastructure of miners to train Machine Learning Models. It is also designed in such a way that it can be easily incorporated in any of the existing Proof of Stake Consensus Algorithms.

This work was undertaken as part of the Final Year Project during our undergrad at Ramaiah Institute of Technology, Bangalore

## How It Works

### Treno Cryptocurrency Platform
Treno runs on top of the Proof of Solution consensus algorithm. Proof of Solution requires miners to train Machine Learning Models instead of computing hashes, thus enabling us to build a platform where users can submit their models to be trained. Wasteful computations by miners are also reduced since they will be directing their resources to perform useful work i.e. the training of ML Models.

![image](https://github.com/pranavh4/Treno/assets/45517185/38765373-7315-48d0-aaa5-9a406e55240c)

The above figure shows the architecture of Treno. The primary users of the system include the Cryptocurrency transaction users and the Research community who wish to have their Machine Learning Models trained.  The blockchain used to store currency transactions is also used to store other types of transactions such as Tasks (requests to train models) and Task Solution (the trained models) transactions.  Transactions and Tasks are submitted to a multi-node blockchain client responsible for transmitting the same to random nodes in the blockchain network. Models that receive the Task and successfully validate it begin training the model to achieve the solution. Once the model is trained, it is uploaded to the cloud. The Task Solution, upon successful verification by peers, is recorded as a transaction in the blockchain. The research community can access this transaction to retrieve the trained model stored in the cloud.


### Proof of Solution
![image](https://github.com/pranavh4/Treno/assets/45517185/494aae7a-a11a-473b-80d7-d240b674f4eb)

The above figure shows our hybrid Proof of Solution Algorithm, which extends the Proof of Stake Algorithm by allowing the miner to stake Work Stake Tokens earned by training Machine Learning Models instead of staking currency from their wallet. Each row in the figure represents a process that is running parallelly independent of the other two rows. The first two rows describe how the Work Stake Tokens are being generated. The bottom row represents the Proof of Stake algorithm, where Work Stake Tokens have replaced currency staking.

The first row describes the process which validates user training requests and adds them to the network. A user creates a Task Transaction containing the URL holding the data and the model, the required accuracy, maximum epochs to be trained for, public key, and signature. This task transaction is sent to a blockchain node from the blockchain client which created the transaction. The node validates the Task Transaction and, on successful validation, adds it to the pool and broadcasts it to the other nodes which do the same.

The second row describes the process which trains the machine learning models based on the user request. The process chooses a random Task Transaction from the pool and downloads the data and model from the URL mentioned in the Task Transaction. It then begins training the model and stops once the stopping criteria of either threshold accuracy or maximum epochs are reached. The trained model is uploaded to the cloud. A Task Solution Transaction is created, which contains a reference to the initial Task Transaction, the URL where the trained model is stored, the achieved accuracy, the Work Stake Tokens earned for this particular task, public key, and signature. The node then broadcasts this transaction throughout the entire network. Each node validates the transaction by downloading the model and data and verifying that the required accuracy was reached and the Work Stake Amount is correct. On successful validation, the Task Solution Transaction is added to the pool and then added to the blockchain when a new block is created. On successful validation of the Task Solution for a particular Task, the node removes the associated Task from the pool in case it is present. This is done so that the node does not select an already trained Task for training in the future, which would be a waste of computation. If multiple nodes train the same task, then the Task Solution Transaction with the highest accuracy is added to the block, and only one node receives the Work Stake Tokens as a reward.

Once this Task Solution Transaction is recorded on the blockchain, the miner can use the earned Work Stake Tokens from the transaction as stake in the Proof of Stake Protocol depicted in the bottom row. Thus, Proof of Solution is designed in such a way that it can be easily incorporated in any of the currently existing Proof of Stake algorithms.
