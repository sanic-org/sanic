import pytest

from sanic.worker.state import WorkerState


def gen_state(**kwargs):
    return WorkerState({"foo": kwargs}, "foo")


def test_set_get_state():
    state = gen_state()
    state["additional"] = 123
    assert state["additional"] == 123
    assert state.get("additional") == 123
    assert state._state == {"foo": {"additional": 123}}


def test_del_state():
    state = gen_state(one=1)
    assert state["one"] == 1
    del state["one"]
    assert state._state == {"foo": {}}


def test_iter_state():
    result = [item for item in gen_state(one=1, two=2)]
    assert result == ["one", "two"]


def test_state_len():
    result = [item for item in gen_state(one=1, two=2)]
    assert len(result) == 2


def test_state_repr():
    assert repr(gen_state(one=1, two=2)) == repr({"one": 1, "two": 2})


def test_state_eq():
    state = gen_state(one=1, two=2)
    assert state == {"one": 1, "two": 2}
    assert state != {"one": 1}


def test_state_keys():
    assert list(gen_state(one=1, two=2).keys()) == list(
        {"one": 1, "two": 2}.keys()
    )


def test_state_values():
    assert list(gen_state(one=1, two=2).values()) == list(
        {"one": 1, "two": 2}.values()
    )


def test_state_items():
    assert list(gen_state(one=1, two=2).items()) == list(
        {"one": 1, "two": 2}.items()
    )


def test_state_update():
    state = gen_state()
    assert len(state) == 0
    state.update({"nine": 9})
    assert len(state) == 1
    assert state["nine"] == 9


def test_state_pop():
    state = gen_state(one=1)
    with pytest.raises(NotImplementedError):
        state.pop()


def test_state_full():
    state = gen_state(one=1)
    assert state.full() == {"foo": {"one": 1}}


@pytest.mark.parametrize("key", WorkerState.RESTRICTED)
def test_state_restricted_operation(key):
    state = gen_state()
    message = f"Cannot set restricted key on WorkerState: {key}"
    with pytest.raises(LookupError, match=message):
        state[key] = "Nope"
        del state[key]

    with pytest.raises(LookupError, match=message):
        state.update({"okay": True, key: "bad"})
