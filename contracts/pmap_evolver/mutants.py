"""Planted bugs in PMap's evolver, each one method of pyrsistent._pmap.PMap._Evolver.

The contract must catch every one. conftest.py patches the method for one history and
restores it when the history ends. Each body is the real method with one plausible fault.
"""

from itertools import chain

from pyrsistent import pvector
from pyrsistent._pmap import PMap


def remove_keeps_count(self, key):
    """remove() takes the entry out of its bucket but does not decrement the size."""
    index, bucket = PMap._get_bucket(self._buckets_evolver, key)
    if bucket:
        new_bucket = [(k, v) for (k, v) in bucket if not (k == key)]
        if len(bucket) > len(new_bucket):
            self._buckets_evolver[index] = new_bucket if new_bucket else None
            return self
    raise KeyError(key)


def remove_missing_silent(self, key):
    """remove() of a missing key returns quietly instead of raising KeyError."""
    index, bucket = PMap._get_bucket(self._buckets_evolver, key)
    if bucket:
        new_bucket = [(k, v) for (k, v) in bucket if not (k == key)]
        size_diff = len(bucket) - len(new_bucket)
        if size_diff > 0:
            self._buckets_evolver[index] = new_bucket if new_bucket else None
            self._size -= size_diff
    return self


def overwrite_in_place(self, key, val):
    """Overwriting a key edits the bucket list in place. The bucket is shared with the map the
    evolver came from and with earlier snapshots, so they change too."""
    index, bucket = PMap._get_bucket(self._buckets_evolver, key)
    if bucket:
        for position, (k, v) in enumerate(bucket):
            if k == key:
                if v is not val:
                    bucket[position] = (k, val)
                    self._buckets_evolver[index] = bucket
                return self
    if len(self._buckets_evolver) < 0.67 * self._size:
        self._reallocate()
        return self.set(key, val)
    self._buckets_evolver[index] = [(key, val)] + (bucket or [])
    self._size += 1
    return self


def rehash_drops_collisions(self):
    """Growing the bucket vector keeps only the last key that lands in each new bucket."""
    new_size = 2 * len(self._buckets_evolver)
    new_list = new_size * [None]
    buckets = self._buckets_evolver.persistent()
    for k, v in chain.from_iterable(x for x in buckets if x):
        new_list[hash(k) % new_size] = [(k, v)]
    self._buckets_evolver = pvector().evolver()
    self._buckets_evolver.extend(new_list)


def persistent_forgets_result(self):
    """persistent() builds the new map but does not keep it, so a later call with no new
    writes returns the map the evolver was made from."""
    if self.is_dirty():
        return PMap(self._size, self._buckets_evolver.persistent())
    return self._original_pmap


# mutant name -> (PMap._Evolver method it replaces, the faulty method)
MUTANTS = {
    "remove-keeps-count": ("remove", remove_keeps_count),
    "remove-missing-silent": ("remove", remove_missing_silent),
    "overwrite-in-place": ("set", overwrite_in_place),
    "rehash-drops-collisions": ("_reallocate", rehash_drops_collisions),
    "persistent-forgets-result": ("persistent", persistent_forgets_result),
}
