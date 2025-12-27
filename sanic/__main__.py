import tracerite

tracerite.load()

from sanic.cli.app import SanicCLI
from sanic.compat import OS_IS_WINDOWS, enable_windows_color_support
from sanic.startup.errors import maybe_handle_startup_error

if OS_IS_WINDOWS:
    enable_windows_color_support()


def main(args=None):
    try:
        cli = SanicCLI()
        cli.attach()
        cli.run(args)
    except Exception as e:
        maybe_handle_startup_error(e)


if __name__ == "__main__":
    main()
