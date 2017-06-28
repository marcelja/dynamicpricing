* Start pricewars platform
* Run `pip install -r merchant_sdk/requirements.txt`
* Register merchant in Management UI --> Deployment. (Merchant API: `http://127.0.0.1:5000`)
* Copy token
* CheapestMerchantApp.py: Add line `merchant_token = "<TOKEN>"` below line 14

```
export PRICEWARS_MARKETPLACE_URL="http://127.0.0.1:8080"
export PRICEWARS_PRODUCER_URL="http://127.0.0.1:3050"
export PRICEWARS_KAFKA_REVERSE_PROXY_URL="http://127.0.0.1:8001"
export API_TOKEN="11Eo7WEM3dE10DXXqNxMz3Q2SA8eJ6sK778EdNag0oh12FXscVFcYfe1pmg9sZTz"
```

* `python CheapestMerchantApp.py`
* Start merchant: `http://localhost/index.html#/config/merchant`
