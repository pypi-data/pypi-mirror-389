## AgentKernel MongoDB Session Store

`agentkernel-mongo` is an extension package for the [`agentkernel`](https://github.com/yaalalabs/agent-kernel) framework. It provides a persistent, scalable, and production-ready session store using MongoDB as the backend.

When installed, this package automatically registers itself with the `agentkernel` framework, allowing you to switch session storage from the default `in_memory` or `redis` to `mongodb` with a simple configuration change.

This package uses MongoDB's native TTL (Time-To-Live) indexing feature to automatically purge stale sessions, ensuring your database remains clean and efficient.

### Installation

1. As a `pip` extra:

```shell
pip install agentkernel[mongo]
```

2. As a standalone package (if you already have `agentkernel` installed):

```shell
pip install agentkernel-mongo
```

This will automatically install the package and its required dependencies, `pymongo`.

### Configuration

This package is designed to work seamlessly with `agentkernel`'s configuration system.

Once installed, you can enable the MongoDB session store by modifying your `config.yaml` (or equivalent configuration file) for your `agentkernel` application.

**Example** `config.yaml`

```yaml
# ... other agentkernel configurations ...

session:
  # 1. Set the type to 'mongo'
  type: mongo

  # 2. Add the 'mongo' configuration block
  mongo:
    url: "mongodb://localhost:27017/"
    database: "agent_sessions"
    collection: "sessions"
    ttl: 604800 # Session TTL in seconds (default: 7 days)

# ... other configurations ...
```

### License

This package is licensed under the MIT.