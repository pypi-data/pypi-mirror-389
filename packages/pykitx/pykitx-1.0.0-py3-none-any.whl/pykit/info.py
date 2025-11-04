from textwrap import dedent
from . import __version__

def show_about():
    print(dedent(f"""
      ╭─────────────────────────────────────────────╮
      │                 🧾  PyKit CLI               │
      ╰─────────────────────────────────────────────╯
      Name:        PyKit
      Version:     {__version__}
      Author:      Adit (DitDev · AetherStudio)
      Email:       rahmataditya2817@gmail.com
      GitHub:      https://github.com/rillToMe/pykit
      Docs:        https://pykit.vercel.app
      License:     MIT
      Python:      >=3.8
      Description: Modern Python project initializer
                   — scaffold packages, apps, tests, CI & templates.
      ╭─────────────────────────────────────────────╮
      │               Built by DitDev               │
      ╰─────────────────────────────────────────────╯
    """).strip())
