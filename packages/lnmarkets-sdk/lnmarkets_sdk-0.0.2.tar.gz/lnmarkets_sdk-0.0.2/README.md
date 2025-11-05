# LN Markets SDK v3

This is the Python version of the LN Markets API SDK. It provides a client-based interface for interacting with the LN Markets API.

## Usage

For public endpoints, you can just do this:

```python
from lnmarkets_sdk.client import LNMClient
import asyncio

async with LNMClient() as client:
  ticker = await client.futures.get_ticker()
  await asyncio.sleep(1)
  leaderboard = await client.futures.get_leaderboard()
```

Remember to sleep between requests, as the rate limit is 1 requests per second for public endpoints.

For endpoints that need authentication, you need to create an instance of the `LNMClient` class and provide your API credentials:

```python
from lnmarkets_sdk.client import APIAuthContext, APIClientConfig, LNMClient

config = APIClientConfig(
    authentication=APIAuthContext(
        key=your_key,
        secret=your_secret,
        passphrase=your_passphrase,
    ),
    network="mainnet",
    timeout=60.0,  # 60 second timeout (default is 30s)
    )

async with LNMClient(config) as client:
  account = await client.account.get_account()
```

or let playwright create it for you by typing the following command in your terminal at the project root
(assuming you have `make` installed on your machine):

```bash
make create-api-key
```

This will create a new API key for you and write it to the `.env` file at the project root.

```txt
# LN Markets API V3 Credentials
LNM_API_KEY_V3=<your_api_key>
LNM_API_SECRET_V3=<your_api_secret>
LNM_API_PASSPHRASE_V3=<your_api_passphrase>
LNM_API_NAME_V3=<your_api_keyname>
```

After that, you can use the client to make API requests to the LN Markets API:

```python
async with LNMClient(config) as client:
  account = await client.account.get_account()
  btc_address = await client.account.get_bitcoin_address()
```

For endpoints that requires input parameters, you can find the corresponding models in the `lnmarkets_sdk.models` module.

```python

from lnmarkets_sdk.client import APIAuthContext, APIClientConfig, LNMClient
from lnmarkets_sdk.models.account import GetLightningDepositsParams

config = APIClientConfig(
    authentication=APIAuthContext(
        key=your_key,
        secret=your_secret,
        passphrase=your_passphrase,
    ),
    network="mainnet",
    timeout=60.0,  # 60 second timeout (default is 30s)
    )

async with LNMClient(config) as client:
    deposits = await client.account.get_lightning_deposits(
        GetLightningDepositsParams(limit=5)
    )
```

Check our [example](./examples/basic.py) for more details.

## API Reference

For full API documentation, see: [LNM API Documentation](https://docs.lnmarkets.com/)

## Examples

Run:

```bash
make example
```

after you generated your API key using `make create-api-key` or setup `.env` file yourself.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
