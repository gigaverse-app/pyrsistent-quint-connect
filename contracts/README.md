# Model-based contracts

These contracts check pyrsistent against small [Quint](https://quint-lang.org/) models with
[pytest-quint-connect](https://github.com/gigaverse-app/pytest-quint-connect). Quint generates
histories of steps from each model, and pytest replays every history against the real code,
comparing what the code exposes with what the model expects after each step. Deliberately
broken variants of the code (mutants) show that each check can fail.

- [`pmap_evolver/`](pmap_evolver/): `PMap.evolver()`. The model is
  [`pmap_evolver.qnt`](pmap_evolver/pmap_evolver.qnt); the rest is plumbing.

Run them with tox (Python 3.13 and Node.js 22+; the plugin installs Quint on first use):

```bash
tox -e contracts
```

<!-- pytest-quint-connect:start -->
<!-- pytest-quint-connect:contracts pmap-evolver -->
<!-- pytest-quint-connect:evidence 06e76cc6726016ee renderer 1.4.0 -->
<a href="https://github.com/gigaverse-app/pytest-quint-connect" title="Mutants are planted fake bugs: deliberately broken copies of the code, used only during this test run. Each must make some history diverge, proving the tests are meaningful: they would notice that kind of bug"><img alt="Quint contracts: 1 contract passed · 20 histories · 5/5 mutants caught" src="https://img.shields.io/badge/Quint_contracts-1_contract_passed_%C2%B7_20_histories_%C2%B7_5%2F5_mutants_caught-brightgreen"></a>

<details>
<summary>✅ 1 contract · 26/26 cases · 5/5 mutants caught · 20 histories</summary>

| | <img width="2000" height="1" align="right" alt="">Contract | Cases passed | [Mutants caught](https://github.com/gigaverse-app/pytest-quint-connect/blob/v1.4.0/docs/why.md#proof-that-the-tests-can-fail "Mutants are planted fake bugs: deliberately broken copies of the code, used only during this test run. Each must make some history diverge, proving the tests are meaningful: they would notice that kind of bug") |
| :-: | :-- | --: | --: |
| ✅ | `pmap-evolver` `pmap_evolver/test_pmap_evolver_contract.py::test_pmap_evolver`<br><sub>20 histories (4 witnesses, 16 samples, seed 7) · every action covered · Quint 0.33.1</sub> | 26/26 | 5/5 |

</details>

<details>
<summary>🧪 5 mutants (planted fake bugs), all caught</summary>

| Contract | [Mutant](https://github.com/gigaverse-app/pytest-quint-connect/blob/v1.4.0/docs/why.md#proof-that-the-tests-can-fail "Mutants are planted fake bugs: deliberately broken copies of the code, used only during this test run. Each must make some history diverge, proving the tests are meaningful: they would notice that kind of bug") | <img width="2000" height="1" align="right" alt="">What it breaks | Caught by | At |
| :-- | :-- | :-- | :-- | :-- |
| `pmap-evolver` | `remove-keeps-count` | remove() takes the entry out but does not decrement the size, so len() overcounts | `witness-snapshotSurvivesLaterWritesTest`<br><sub>samples: 14/16 diverge</sub> | state 4, after `erase(key=0)` |
| `pmap-evolver` | `remove-missing-silent` | remove() of a missing key returns quietly instead of raising KeyError | `witness-removingMissingKeyRaisesTest`<br><sub>samples: 13/16 diverge</sub> | state 1, after `erase(key=1)` |
| `pmap-evolver` | `overwrite-in-place` | overwriting a key edits the shared bucket list in place, changing the original map and earlier snapshots | `witness-snapshotSurvivesLaterWritesTest`<br><sub>samples: 7/16 diverge</sub> | state 3, after `store(key=1, value=2)` |
| `pmap-evolver` | `rehash-drops-collisions` | growing the bucket vector keeps only one key per new bucket, losing colliding keys | `witness-growingKeepsCollidingKeysTest`<br><sub>samples: 1/16 diverge</sub> | state 3, after `store(key=2, value=2)` |
| `pmap-evolver` | `persistent-forgets-result` | persistent() does not keep the map it built, so a later call with no new writes returns the original map | `sample-0`<br><sub>samples: 8/16 diverge</sub> | state 5, after `persist()` |

</details>

<details open>
<summary>What <code>pmap-evolver</code> says</summary>

**Actions**, and the code each one drives:

- `init`: e = pmap({0: 0}, pre_size=2).evolver()
- `store`: e[key] = value
- `erase`: e.remove(key), observed as Removed or Missing (KeyError)
- `persist`: snapshot = e.persistent()
- `inspect`: read e, the snapshot and the original map without changing them

**Invariant** `consistent`, checked while sampling histories.

**Witnesses**, scenarios replayed exactly as written: `snapshotSurvivesLaterWritesTest`, `growingKeepsCollidingKeysTest`, `removingMissingKeyRaisesTest`, `sameValueStoreStaysCleanTest`.

**Bounds**: seed `7` · max_samples `200` · max_steps `10` · n_traces `16`.

**Witness `snapshotSurvivesLaterWritesTest`, step by step**: the observation the model starts from, then what it expects each action to change.

| State | Action | Model expects |
| --: | :-- | :-- |
| `0` | `init()` | `{ count: 1, dirty: false, entries: Map(0 -> 0), lastRemoval: NoRemoval, original: Map(0 -> 0), snapshot: Map(0 -> 0), snapshotCount: 1 }` |
| `1` | `store(key=1, value=1)` | `count: 1 → 2`<br>`dirty: false → true`<br>`entries: Map(0 -> 0) → Map(0 -> 0, 1 -> 1)` |
| `2` | `persist()` | `dirty: true → false`<br>`snapshot: Map(0 -> 0) → Map(0 -> 0, 1 -> 1)`<br>`snapshotCount: 1 → 2` |
| `3` | `store(key=1, value=2)` | `dirty: false → true`<br>`entries: Map(0 -> 0, 1 -> 1) → Map(0 -> 0, 1 -> 2)` |
| `4` | `erase(key=0)` | `count: 2 → 1`<br>`entries: Map(0 -> 0, 1 -> 2) → Map(1 -> 2)`<br>`lastRemoval: NoRemoval → Removed` |
| `5` | `inspect()` | unchanged |

</details>

<sub>Generated by [pytest-quint-connect](https://github.com/gigaverse-app/pytest-quint-connect) from contract receipts; [what a passing run proves](https://github.com/gigaverse-app/pytest-quint-connect/blob/v1.4.0/docs/limits.md).</sub>
<!-- pytest-quint-connect:end -->
