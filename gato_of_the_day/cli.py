"""CLI interface for gato_of_the_day project.

Be creative! do whatever you want!

- Install click or typer and create a CLI app
- Use builtin argparse
- Start a web application
- Import things from your .base module
"""

import bot

def main():  # pragma: no cover
    """
    The main function executes on commands:
    `python -m gato_of_the_day` and `$ gato_of_the_day `.

    This is your program's entry point.

    You can change this function to do whatever you want.
    Examples:
        * Run a test suite
        * Run a server
        * Do some other stuff
        * Run a command line application (Click, Typer, ArgParse)
        * List all available tasks
        * Run an application (Flask, FastAPI, Django, etc.)
    """
    bot.run_bot()
