# mcwebapi

# WARNING: This package is under active development.
## This package is not yet ready for production use! Many things and specifications may change



[![PyPI](https://img.shields.io/pypi/v/mcwebapi?style=for-the-badge&logo=pypi&labelColor=black&color=blue)](https://pypi.org/project/mcwebapi/)
[![Python](https://img.shields.io/pypi/pyversions/mcwebapi?style=for-the-badge&logo=python&labelColor=black)](https://pypi.org/project/mcwebapi/)
[![Downloads](https://img.shields.io/pypi/dm/mcwebapi?style=for-the-badge&labelColor=black&color=green)](https://pypi.org/project/mcwebapi/)

Python client library for the [Minecraft WebSocket API](https://github.com/addavriance/MinecraftWebsocketAPI) mod. Control your Minecraft server programmatically with a clean, async-ready API.

## Quick Start

```python
import math
import random

from mcwebapi import MinecraftAPI

with MinecraftAPI() as api:
    try:
        player = api.Player("Dev")

        while True:
            x, y, z = player.getPosition().wait().values()

            s_x, s_y, s_z = math.floor(x), y-0.5, math.floor(z)

            block_stands_on = api.Block('minecraft:overworld', s_x, s_y, s_z).getBlock().wait()

            available_blocks = ['minecraft:diamond_block', 'minecraft:gold_block', 'minecraft:iron_block']

            if block_stands_on['type'] == 'minecraft:air':
                api.Block('minecraft:overworld', s_x, s_y, s_z).setBlock(random.choice(available_blocks))

    except TimeoutError:
        print("Request timed out")
```

## Features

- **Clean API**: Intuitive method names matching the server mod
- **Promise-based**: Async-ready with `.wait()` for synchronous calls or `.then()` for callbacks
- **Type-safe**: Full typing support for better IDE autocomplete
- **Context manager**: Automatic connection management
- **Lightweight**: Minimal dependencies (just `websocket-client`)

## Usage Examples

### Player Operations

```python
from mcwebapi import MinecraftAPI

with MinecraftAPI() as api:
    # Health management
    player = api.Player("Steve")
    
    health = player.getHealth().then(print)
    player.setHealth(20.0)
    
    # Inventory
    inventory = player.getInventory().then(print)
    player.giveItem("minecraft:diamond", 64)
    player.clearInventory()
    
    # Effects
    player.addEffect("minecraft:speed", 200, 1)
    effects = player.getEffects().then(print)
    
    # Teleportation
    player.teleportToDim("minecraft:the_nether", 0, 64, 0)
    
    # Game mode
    player.setGameMode("creative")
```

### World Operations

```python
from mcwebapi import MinecraftAPI

with MinecraftAPI() as api:
    # Time control
    overworld = api.Level("minecraft:overworld")
    
    overworld.setDayTime("minecraft:overworld", 6000).wait()  # Noon
    is_day = overworld.isDay("minecraft:overworld").wait()
    
    # Weather
    overworld.setWeather("minecraft:overworld", True, False).wait()  # Rain, no thunder
    
    # Blocks
    block = overworld.getBlock("minecraft:overworld", 0, 64, 0).wait()
    overworld.setBlock("minecraft:overworld", "minecraft:stone", 0, 64, 0).wait()
    
    # World info
    levels = overworld.getAvailableLevels().wait()
    info = overworld.getLevelInfo().wait()
```

### Block Operations

```python
from mcwebapi import MinecraftAPI

with MinecraftAPI() as api:
    # Get block info
    block = api.Block("minecraft:overworld", 10, 64, 10).then(print)
    
    # Container inventory
    inventory = block.getInventory().wait()
    
    # Set items in containers
    block.setInventorySlot(
        slot=0,
        itemId="minecraft:diamond",
        count=64
    ).wait()
    
    furnace = block.getFurnaceInfo().wait() # but if not a furnace, you'll get null
```

### Async Patterns

#### Using Promises with Callbacks

```python
from mcwebapi import MinecraftAPI

api = MinecraftAPI()
api.connect()

# Chain callbacks
api.Player("Steve").getPosition().then(
    lambda pos: print(f"Position: {pos}")
)

# Handle multiple requests
positions = []
for player in ["Steve", "Alex", "Notch"]:
    api.Player(player).getPosition().then(
        lambda pos, p=player: positions.append({p: pos})
    )
```

#### Manual Connection Management

```python
from mcwebapi import MinecraftAPI

api = MinecraftAPI(host="192.168.1.100", port=8765, auth_key="secret")

try:
    api.connect()
    
    if api.is_authenticated():
        result = api.Player("Steve").getHealth().wait()
        print(result)
        
finally:
    api.disconnect()
```

## API Reference

### MinecraftAPI

Main API class for interacting with the server.

```python
MinecraftAPI(
    host: str = "localhost",
    port: int = 8765,
    auth_key: str = "default-secret-key-change-me",
    timeout: float = 10.0
)
```

**Methods:**
- `connect()` - Establish connection and authenticate
- `disconnect()` - Close connection
- `is_connected() -> bool` - Check connection status
- `is_authenticated() -> bool` - Check authentication status

**Modules:**
- `api.Player` - Player operations
- `api.Level` - World operations
- `api.Block` - Block operations
- ... and many more soon!

### Promise API

All API calls return a `Promise` object:

```python
promise = api.Player("Steve").getHealth()

# Wait synchronously
result = promise.wait() # blocks main loop

# Or use callbacks
promise.then(lambda health: print(f"Health: {health}")) # resolves in connection thread, sometime

# Check status
if promise.is_completed():
    if promise.is_successful():
        print(promise.result)
```

## Server Setup

This client requires the Minecraft WebSocket API mod to be installed on your server.

**Mod Repository:** [MinecraftWebsocketAPI](https://github.com/addavriance/MinecraftWebsocketAPI)

1. Install the NeoForge mod on your Minecraft 1.21.1 server
2. Configure `config/mcwebapi-server.toml`:
   ```toml
   [websocket]
       #WebSocket server port
       # Default: 8765
       # Range: 1000 ~ 65535
       port = 8765
       #Authentication key for binary protocol
       authKey = "default-secret-key-change-me"
       #Enable TLS/SSL encryption
       enableSSL = false
       #Request timeout in seconds
       # Default: 30
       # Range: 1 ~ 300
       timeout = 30
       #Allowed origins for CORS
       allowedOrigins = "*"
       #WebSocket server host
       host = "0.0.0.0"
   ```
3. Restart the server or just join the world

## Requirements

- Python 3.7+
- `websocket-client>=1.3.0`
- Minecraft with mcwebapi mod installed

## Error Handling

```python
from mcwebapi import MinecraftAPI

with MinecraftAPI() as api:
    try:
        result = api.Player("NonExistentPlayer").getHealth().wait()  # returns None

        print(result)

        api.Player("Steve").teleportTo('', 0)  # not enough arguments, will raise an exception
        api.Player("Steve").teleportTo('', 0, 0, 8574843685768364873)  # in other cases that produce exceptions in game, will propagate them there
    except TimeoutError:
        print("Request timed out")
    except Exception as e:
        print(f"Error: {e}")
```

Common exceptions:
- `ConnectionError` - Failed to connect or not authenticated
- `TimeoutError` - Request exceeded timeout duration
- `Exception` - Server-side errors (invalid arguments, etc.)

## Configuration

### Timeout

Default timeout is 10 seconds. Adjust per instance:

```python
api = MinecraftAPI(timeout=30.0)  # 30 second timeout
```

### Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Setup

```bash
git clone https://github.com/addavriance/mcwebapi.git
cd mcwebapi
pip install -e .
```


## Protocol Details

The client uses WebSocket communication with Base64-encoded JSON messages:

**Request:**
```json
{
  "type": "REQUEST",
  "module": "player",
  "method": "getHealth",
  "args": ["Steve"],
  "requestId": "a1b",
  "timestamp": 1699564800.0
}
```

**Response:**
```json
{
  "type": "RESPONSE",
  "status": "SUCCESS",
  "data": 20.0,
  "requestId": "a1b",
  "timestamp": 1699564800000
}
```

## Roadmap

- [ ] Async/await support with asyncio
- [ ] Event subscriptions (player join/leave, block changes)
- [ ] Batch operations
- [ ] Response caching

## Contributing

Contributions welcome! Please open an issue or PR on [GitHub](https://github.com/addavriance/mcwebapi).

## Links

- **PyPI:** [pypi.org/project/mcwebapi](https://pypi.org/project/mcwebapi/)
- **Server Mod:** [MinecraftWebsocketAPI](https://github.com/addavriance/MinecraftWebsocketAPI)
- **Issues:** [GitHub Issues](https://github.com/addavriance/mcwebapi/issues)
