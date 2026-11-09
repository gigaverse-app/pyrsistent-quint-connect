from collections.abc import Callable
from contextlib import ExitStack
from unittest import mock

import pytest
from mutants import MUTANTS
from pmap_evolver_driver import PmapEvolverDriver, Removal, View
from pytest_quint_connect import HistoryContext

from pyrsistent import PMap, pmap

# Every key the model can use (0, 1, 2 and 4) and a few it never does, so a stray entry shows.
# The evolver has no iteration, so observe() asks for each key in turn.
OBSERVED_KEYS = range(8)


class EvolverDriver(PmapEvolverDriver):
    """Applies model actions to a real PMap evolver and reads its state back.

    PmapEvolverDriver is generated from pmap_evolver.qnt (pmap_evolver_driver.py). No
    expected values are computed here; they come only from the model.
    """

    def __init__(self, mutant: str | None) -> None:
        self._undo = ExitStack()
        if mutant:
            method, faulty = MUTANTS[mutant]
            self._undo.enter_context(mock.patch.object(PMap._Evolver, method, faulty))
        self.init()

    def close(self) -> None:
        self._undo.close()

    def init(self) -> None:
        self.original = pmap({0: 0}, pre_size=2)
        self.evolver = self.original.evolver()
        # Before the first persistent() call, the latest map is the original one.
        self.snapshot = self.original
        self.last_removal: Removal = {"tag": "NoRemoval"}

    def store(self, key: int, value: int) -> None:
        self.evolver[key] = value
        self.last_removal = {"tag": "NoRemoval"}

    def erase(self, key: int) -> None:
        try:
            self.evolver.remove(key)
        except KeyError:
            self.last_removal = {"tag": "Missing"}
        else:
            self.last_removal = {"tag": "Removed"}

    def persist(self) -> None:
        self.snapshot = self.evolver.persistent()
        self.last_removal = {"tag": "NoRemoval"}

    def inspect(self) -> None:
        pass

    def observe(self) -> View:
        # Reads only: `in`, [], len() and is_dirty() leave the evolver as it was, and the two
        # maps are immutable. Never call persistent() here: it changes the evolver.
        evolver = self.evolver
        return {
            "entries": {key: evolver[key] for key in OBSERVED_KEYS if key in evolver},
            "count": len(evolver),
            "dirty": evolver.is_dirty(),
            "snapshot": dict(self.snapshot),
            "snapshotCount": len(self.snapshot),
            "original": dict(self.original),
            "lastRemoval": self.last_removal,
        }


@pytest.fixture
def evolver_driver() -> Callable[[HistoryContext], EvolverDriver]:
    return lambda context: EvolverDriver(context.mutant)
