"""Extended data structures."""

import heapq
from collections import OrderedDict
from typing import Any, Dict, Optional


class PriorityQueue:
    """Priority queue implementation."""

    def __init__(self):
        self._queue = []
        self._index = 0

    def push(self, item: Any, priority: float):
        """Add item with priority."""
        heapq.heappush(self._queue, (priority, self._index, item))
        self._index += 1

    def pop(self) -> Any:
        """Remove and return highest priority item."""
        return heapq.heappop(self._queue)[-1]

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0


class Trie:
    """Trie (prefix tree) implementation."""

    def __init__(self):
        self._root = {}

    def insert(self, word: str):
        """Insert word into trie."""
        node = self._root
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node["$"] = True

    def search(self, word: str) -> bool:
        """Search for word in trie."""
        node = self._root
        for char in word:
            if char not in node:
                return False
            node = node[char]
        return "$" in node

    def starts_with(self, prefix: str) -> bool:
        """Check if any word starts with prefix."""
        node = self._root
        for char in prefix:
            if char not in node:
                return False
            node = node[char]
        return True


class LRUCache:
    """LRU Cache implementation."""

    def __init__(self, capacity: int):
        self._cache = OrderedDict()
        self._capacity = capacity

    def get(self, key: Any) -> Optional[Any]:
        """Get value by key."""
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: Any, value: Any):
        """Put key-value pair."""
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self._capacity:
            self._cache.popitem(last=False)
        self._cache[key] = value


class CircularBuffer:
    """Circular buffer implementation."""

    def __init__(self, size: int):
        self._buffer = [None] * size
        self._size = size
        self._head = 0
        self._count = 0

    def append(self, item: Any):
        """Append item to buffer."""
        self._buffer[self._head] = item
        self._head = (self._head + 1) % self._size
        if self._count < self._size:
            self._count += 1

    def get_all(self) -> list:
        """Get all items in order."""
        if self._count == 0:
            return []
        start = (self._head - self._count) % self._size
        result = []
        for i in range(self._count):
            idx = (start + i) % self._size
            result.append(self._buffer[idx])
        return result

