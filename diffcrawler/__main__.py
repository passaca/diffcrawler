"""
Entry point to application. Instantiates application object and starts the main loop.
"""

from diffcrawler.app import DiffCrawler

if __name__ == "__main__":
    app = DiffCrawler()
    app.mainloop()
