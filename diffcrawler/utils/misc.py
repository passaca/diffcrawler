"""
Miscellaneous utility functions and classes.
"""

import datetime
import re
import difflib

from bs4 import BeautifulSoup


def format_date(date: datetime.datetime) -> str:
    """Return a formatted date string."""
    return f'{date :%d %b %Y, %H:%M}'

def is_valid_url(url: str) -> bool:
    """Check if the passed URL is of a valid URL format."""
    # Regex from Django, not perfect for edge cases, but probably good for most uses
    regex = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(regex, url) is not None

class SiteDiff():
    """
    Class responsible to make diffs of two website sources (two revisions) and to calculate
    the number of changes between them.
    """

    def __init__(self, src1: str, src2: str):
        self._src1 = src1
        self._src2 = src2

        # Get stripped version of sources (list of individual text elements in each source)
        self._stripped1 = self._parse_html(src1)
        self._stripped2 = self._parse_html(src2)

    def _parse_html(self, src: str) -> list:
        """Parse the HTML source and return a list of the individual text elements."""
        soup = BeautifulSoup(src, 'html.parser')
        return list(soup.stripped_strings)
    
    def diff(self) -> str:
        """Return the diff of the stripped versions of the two sources."""
        site1 = [string + '\n' for string in self._stripped1]
        site2 = [string + '\n' for string in self._stripped2]

        diff = ''.join(difflib.ndiff(site1, site2))

        return diff
    
    def num_changes(self) -> int:
        """Calculate and return the number of changes between the sources (what's new in src1)"""
        changes = 0
        
        for line in self.diff().splitlines():
            if line.startswith('- '):
                changes += 1
        
        return changes
    
class IncorrectFileFormatError(Exception):
    """
    Exception used if the file format is detected to be of an incorrect format.
    """

    pass