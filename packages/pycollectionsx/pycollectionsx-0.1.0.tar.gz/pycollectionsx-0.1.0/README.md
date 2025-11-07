# pycollectionsx

Extended data-structure toolkit — PriorityQueue, Trie, LRUCache, etc.

## Installation

```bash
pip install pycollectionsx
```

## Usage

```python
from pycollectionsx import PriorityQueue, Trie, LRUCache

pq = PriorityQueue()
pq.push("item", 1)

trie = Trie()
trie.insert("hello")

cache = LRUCache(10)
cache.put("key", "value")
```

## License

MIT

