// The evolver of a persistent map (pyrsistent's PMap.evolver()): a mutable view with
// "transaction like" semantics. `event` names each step for the driver; `observed` is what
// the driver reads back after it.
//
// The evolver starts from ORIGINAL, a one-entry map built with a two-bucket vector, and keys
// are small ints, so 0, 2 and 4 share a bucket and storing a fourth key grows the vector.
module pmap_evolver {
  type Removal = Removed | Missing | NoRemoval
  type Event = { op: str, key: int, value: int }
  type View = {
    // what the evolver holds: e[key] for every key in e
    entries: int -> int,
    // len(e)
    count: int,
    // e.is_dirty()
    dirty: bool,
    // the map the last e.persistent() returned (the original map before the first call)
    snapshot: int -> int,
    snapshotCount: int,
    // the map the evolver was made from; an evolver never changes it
    original: int -> int,
    // whether the last step's remove() removed the key or raised KeyError
    lastRemoval: Removal,
  }

  pure val ORIGINAL = Map(0 -> 0)
  pure val KEYS = Set(0, 1, 2, 4)
  pure val VALUES = 0.to(2)

  var event: Event
  var observed: View

  pure def without(entries: int -> int, key: int): int -> int =
    entries.keys().exclude(Set(key)).mapBy(k => entries.get(k))

  action init = all {
    event' = { op: "init", key: 0, value: 0 },
    observed' = {
      entries: ORIGINAL,
      count: 1,
      dirty: false,
      snapshot: ORIGINAL,
      snapshotCount: 1,
      original: ORIGINAL,
      lastRemoval: NoRemoval,
    },
  }

  // e[key] = value. The evolver is dirty after a write that changed what it holds since the
  // last persistent(); storing the value a key already has is not a change.
  action store(key: int, value: int): bool = {
    val unchanged = observed.entries.keys().contains(key) and observed.entries.get(key) == value
    val entries = observed.entries.put(key, value)
    all {
      event' = { op: "store", key: key, value: value },
      observed' = {
        ...observed,
        entries: entries,
        count: entries.keys().size(),
        dirty: observed.dirty or not(unchanged),
        lastRemoval: NoRemoval,
      },
    }
  }

  // e.remove(key): removes a present key, raises KeyError for a missing one and changes nothing.
  action erase(key: int): bool = all {
    event' = { op: "erase", key: key, value: 0 },
    observed' = if (observed.entries.keys().contains(key)) {
      val entries = without(observed.entries, key)
      { ...observed, entries: entries, count: entries.keys().size(), dirty: true, lastRemoval: Removed }
    } else {
      { ...observed, lastRemoval: Missing }
    },
  }

  // e.persistent(): a map holding what the evolver holds, which later writes to the evolver
  // never change. The evolver is clean afterwards.
  action persist = all {
    event' = { op: "persist", key: 0, value: 0 },
    observed' = {
      ...observed,
      snapshot: observed.entries,
      snapshotCount: observed.count,
      dirty: false,
      lastRemoval: NoRemoval,
    },
  }

  // A read-only step, so that a witness can end in an assertion without repeating an action.
  action inspect = all { event' = { op: "inspect", key: 0, value: 0 }, observed' = observed }

  action step = {
    nondet key = KEYS.oneOf()
    nondet value = VALUES.oneOf()
    any { store(key, value), erase(key), persist }
  }

  val consistent = all {
    observed.count == observed.entries.keys().size(),
    observed.snapshotCount == observed.snapshot.keys().size(),
    observed.original == ORIGINAL,
  }

  // persistent() returns a map that later writes to the evolver do not change, and the
  // original map is never touched.
  run snapshotSurvivesLaterWritesTest = init.then(store(1, 1)).then(persist).then(store(1, 2))
    .then(erase(0))
    .then(all {
      assert(observed.snapshot == Map(0 -> 0, 1 -> 1) and observed.entries == Map(1 -> 2)
        and observed.original == ORIGINAL),
      inspect,
    })

  // 0 and 4 share a bucket before and after the fourth key grows the bucket vector; growing
  // keeps both, and removing one leaves the other.
  run growingKeepsCollidingKeysTest = init.then(store(4, 1)).then(store(1, 1)).then(store(2, 2))
    .then(all { assert(observed.entries == Map(0 -> 0, 1 -> 1, 2 -> 2, 4 -> 1) and observed.count == 4), erase(0) })
    .then(all { assert(observed.entries == Map(1 -> 1, 2 -> 2, 4 -> 1) and observed.count == 3), inspect })

  run removingMissingKeyRaisesTest = init.then(erase(1))
    .then(all {
      assert(observed.lastRemoval == Missing and observed.entries == ORIGINAL and not(observed.dirty)),
      inspect,
    })

  // persistent() leaves the evolver clean, and storing a key's current value keeps it clean.
  run sameValueStoreStaysCleanTest = init.then(store(1, 1)).then(persist).then(store(1, 1))
    .then(all { assert(not(observed.dirty) and observed.snapshot == Map(0 -> 0, 1 -> 1)), inspect })
}
