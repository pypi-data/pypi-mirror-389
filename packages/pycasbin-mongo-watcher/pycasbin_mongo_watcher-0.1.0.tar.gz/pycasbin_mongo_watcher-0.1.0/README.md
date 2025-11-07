# PyCasbin MongoDB Watcher

MongoDB watcher for [PyCasbin](https://github.com/casbin/pycasbin). It enables distributed policy synchronization across multiple Casbin instances using MongoDB Change Streams.

## Installation

```bash
pip install pycasbin-mongo-watcher
```

## Quick Start

```python
import casbin
from mongo_watcher import new_watcher

# Reload policy on updates
def on_update():
    enforcer.load_policy()

# Create MongoDB watcher
watcher = new_watcher(
    dsn="mongodb://localhost:27017",
    db_name="casbin",
    collection="casbin_watcher",
)
watcher.set_update_callback(on_update)

# Initialize Casbin enforcer
enforcer = casbin.Enforcer("path/to/model.conf", "path/to/policy.csv")
# Bind watcher to enforcer
enforcer.set_watcher(watcher)
```

## License

Apache-2.0. See [LICENSE](LICENSE).
