# RecallBricks Python SDK

The Memory Layer for AI - Persistent memory across all AI models.

## Installation
```bash
pip install recallbricks
```

## Quick Start
```python
from recallbricks import RecallBricks

rb = RecallBricks("your-api-key")

# Create a memory
memory = rb.create_memory(
    text="User prefers dark mode",
    tags=["preference", "ui"]
)

# Search memories
results = rb.search("dark mode", limit=5)
for memory in results:
    print(memory.text)
```

## Documentation

Visit https://recallbricks.com/docs for full documentation.

## License

MIT
