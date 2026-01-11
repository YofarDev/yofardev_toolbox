"""Entry point for Yofardev Toolbox."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import App

def main():
    """Launch the application."""
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
