# Simple-Blockchain

## Intruduction

Simple-Blockchain is a simple blockchain program. It can help you understand the how block chain works. You can test it with your friends.

This code is written according to [Learn Blockchains by Building One](https://hackernoon.com/learn-blockchains-by-building-one-117428612f46). Thanks for the contribution he made, hopefully this will help more people.
## Requirements

* python3.5+
* flask
* requests

## Usage

* ### Start

~~~
python blockchain.py
~~~

* ### Create a new block

~~~
curl http://127.0.0.1:5000/mine
~~~

* ### Make a new transaction

~~~
curl -X POST -H "Content-Type: application/json" -d'{
 "sender": "sender-address",
 "recipient: "other-address",
 "amount": 1,
}' "http://127.0.0.1:5000/transcations/new"
~~~

* ### Get information of all block

~~~
curl http://127.0.0.1:500/chain
~~~

* ### Register new nodes

~~~
curl -X POST -H "Content-Type: application/json" -d'{
 "nodes": "node-address",
}' "http://127.0.0.1:5000/nodes/register"
~~~

* ### Resolve current nodes

~~~
curl http://127.0.0.1:500/nodes/resolve
~~~