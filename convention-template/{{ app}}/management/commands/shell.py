"""Python 3.13 REPL support using the unsupported _pyrepl module."""

from django.core.management.commands.shell import Command as BaseShellCommand


class Command(BaseShellCommand):
    shells = ["ipython", "bpython", "pyrepl", "python"]

    def pyrepl(self, options):
        from _pyrepl.main import interactive_console

        interactive_console()
