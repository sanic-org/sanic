from collections.abc import Mapping
from typing import Any, Dict, ItemsView, Iterator, KeysView, List
from typing import Mapping as MappingType
from typing import ValuesView


dict


class WorkerState(Mapping):
    RESTRICTED = (
        "health",
        "pid",
        "requests",
        "restart_at",
        "server",
        "start_at",
        "starts",
        "state",
    )

    def __init__(self, state: Dict[str, Any], current: str) -> None:
        self._name = current
        self._state = state

    def __getitem__(self, key: str) -> Any:
        return self._state[self._name][key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.RESTRICTED:
            self._write_error([key])
        self._state[self._name] = {
            **self._state[self._name],
            key: value,
        }

    def __delitem__(self, key: str) -> None:
        if key in self.RESTRICTED:
            self._write_error([key])
        self._state[self._name] = {
            k: v for k, v in self._state[self._name].items() if k != key
        }

    def __iter__(self) -> Iterator[Any]:
        return iter(self._state[self._name])

    def __len__(self) -> int:
        return len(self._state[self._name])

    def __repr__(self) -> str:
        return repr(self._state[self._name])

    def __eq__(self, other: object) -> bool:
        return self._state[self._name] == other

    def keys(self) -> KeysView[str]:
        return self._state[self._name].keys()

    def values(self) -> ValuesView[Any]:
        return self._state[self._name].values()

    def items(self) -> ItemsView[str, Any]:
        return self._state[self._name].items()

    def update(self, mapping: MappingType[str, Any]) -> None:
        if any(k in self.RESTRICTED for k in mapping.keys()):
            self._write_error(
                [k for k in mapping.keys() if k in self.RESTRICTED]
            )
        self._state[self._name] = {
            **self._state[self._name],
            **mapping,
        }

    def pop(self) -> None:
        raise NotImplementedError

    def full(self) -> Dict[str, Any]:
        return dict(self._state)

    def _write_error(self, keys: List[str]) -> None:
        raise LookupError(
            f"Cannot set restricted key{'s' if len(keys) > 1 else ''} on "
            f"WorkerState: {', '.join(keys)}"
        )
