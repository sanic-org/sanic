from sanic.cli.app import SanicCLI
from sanic.compat import OS_IS_WINDOWS, enable_windows_color_support


if OS_IS_WINDOWS:
    enable_windows_color_support()


def main(args=None):
    cli = SanicCLI()
    cli.attach()
    cli.run(args)


if __name__ == "__main__":
    main()
