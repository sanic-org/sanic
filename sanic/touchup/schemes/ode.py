from .base import BaseScheme


class OptionalDispatchEvent(BaseScheme):
    ident = "ODE"

    def run(self, directive: str, offset: int) -> None:
        events = [signal.path for signal in self.app.signal_router.routes]

        if events:
            try:
                event, context = directive.split(" ", 1)
                ctx = f", context={context}"
            except ValueError:
                event = directive
                ctx = ""

            if event in events:
                pad = " " * offset
                self.add_line(
                    f'{pad}await self.dispatch("{event}"{ctx}, inline=True)'
                )
