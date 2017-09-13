# Data-Driven Demand Learning and Dynamic Pricing Strategies in Competitive Markets

### Setup

* Install Python 3.6 or create virtual environment (e.g. `virtualenv -p python3.6 env` and `source env/bin/activate`)
* `pip install -r requirements.txt`
* `cd merchant`
* Run tests: `python -m unittest`

### Start merchant on platform

* Go to `http://vm-mpws2016hp1-02.eaalab.hpi.uni-potsdam.de/#/deployment`
* Merchant API: `http://vm-dynpricing-team-8.eaalab.hpi.uni-potsdam.de:<PORT>`
```
export PRICEWARS_MARKETPLACE_URL="vm-mpws2016hp1-04.eaalab.hpi.uni-potsdam.de:8080/marketplace"
export PRICEWARS_PRODUCER_URL="vm-mpws2016hp1-03.eaalab.hpi.uni-potsdam.de"
export PRICEWARS_KAFKA_REVERSE_PROXY_URL="vm-mpws2016hp1-05.eaalab.hpi.uni-potsdam.de:8001"
export API_TOKEN="JqyBUpOIU2hHHd1u1Ek5eOnCoULkpFr96rKahjsClaT3EUxFiiKN78ZvdvgTAYcG"
```
* `python rand_for.py --port <PORT>`

### CSV interface

TODO
