"""Tests for pycollectionsx core functions."""

from pycollectionsx import PriorityQueue, Trie, LRUCache, CircularBuffer


def test_priority_queue():
    pq = PriorityQueue()
    pq.push("low", 3)
    pq.push("high", 1)
    assert pq.pop() == "high"
    assert pq.pop() == "low"


def test_trie():
    trie = Trie()
    trie.insert("hello")
    assert trie.search("hello") is True
    assert trie.search("hell") is False
    assert trie.starts_with("hell") is True


def test_lru_cache():
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(2, "b")
    assert cache.get(1) == "a"
    cache.put(3, "c")
    assert cache.get(2) is None


def test_circular_buffer():
    buf = CircularBuffer(3)
    buf.append(1)
    buf.append(2)
    buf.append(3)
    assert len(buf.get_all()) == 3
    buf.append(4)
    assert 1 not in buf.get_all()

