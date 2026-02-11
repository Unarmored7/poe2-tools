"""Module entry point for `python -m poe2_tools`."""

import ttkbootstrap as ttk

from poe2_tools.app import CombinedApp


def main() -> None:
    root = ttk.Window(themename="cosmo")
    app = CombinedApp(root)
    app.run()


if __name__ == "__main__":
    main()
