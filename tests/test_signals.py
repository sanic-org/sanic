import logging
from pytest import mark, raises

from sanic.exceptions import SignalsNotFrozenException
from sanic.signals import SignalRegistry, SignalContext, SignalData


class TestSignalsRegistry:
    def test_singleton_nature(self, signal_registry):
        assert signal_registry == SignalRegistry()

    def test_signal_registration(self, signal_registry):
        signal_registry.register(
            context=SignalContext(
                namespace="test", context="unittest", action=None
            ),
            owner="ut",
        )
        ctx = SignalContext(
            namespace="test", context="unittest", action="success"
        )
        signal_registry.register(
            context=ctx,
            owner="ut",
        )
        signal_registry.freeze(context=ctx)
        signal_registry.freeze()
        assert len(signal_registry.signals.keys()) == len(
            SignalRegistry().signals.keys()
        )

    @mark.asyncio
    async def test_signal_dispatch(
        self, signal_registry, dummy_signal_callback_sync, callback_tracker
    ):
        called = 0

        async def _callback(app, loop, signal, data):
            nonlocal called
            logger = logging.getLogger()
            logger.info(f"{data} {signal}")
            called = 1

        ctx = SignalContext(
            namespace="test", context="unittest", action="success"
        )
        signal_registry.register(
            context=ctx,
            owner="ut",
        )
        tracker = callback_tracker()
        signal_registry.subscribe(
            context=ctx,
            callback=dummy_signal_callback_sync(call_tracker=tracker),
        )
        signal_registry.subscribe(context=ctx, callback=_callback)
        signal_registry.freeze()
        await signal_registry.dispatch(
            context=ctx,
            data=SignalData(additional_info={"test": "Test"}),
            app=None,
            loop=None,
        )
        assert called == 1

    @mark.asyncio
    async def test_failure_for_unfrozen_signal(
        self,
        signal_registry,
        test_signal_context,
        dummy_signal_callback,
        callback_tracker,
    ):
        data = callback_tracker()
        signal_registry.register(context=test_signal_context, owner="ut")
        signal_registry.subscribe(
            context=test_signal_context,
            callback=dummy_signal_callback(call_tracker=data),
        )
        with raises(expected_exception=SignalsNotFrozenException) as _:
            await signal_registry.dispatch(
                context=test_signal_context, data=None
            )
