"""
Requester, used to fetch URLs (website sources) concurrently (using threads).
"""

import concurrent.futures

import requests
from typing import Tuple, List, Callable


class Requester():
    """
    Requester class. Uses threads to fetch a list of urls concurrently and calls a callback once finished.
    """
    def __init__(self, max_workers=5):
        # Use a thread pool executor with a default of 5 workers (concurrent connections/threads)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def fetch_url(self, url: str, timeout: int) -> Tuple[bool, str | None]:
        """Fetch and return the source of the passed url."""
        try:
            response = requests.get(url, timeout=timeout)
        # An error occurred (most likely timeout error):
        except requests.exceptions.RequestException:
            return(False, None)
        else:
            # Check if response code is 'ok'
            if response.status_code == 200:
                return (True, response.text)
            else:
                return (False, None)

    def fetch_concurrently(self, urls: List[dict], callback: Callable) -> None:
        """Fetch list of urls concurrently and call the passed callback function for each of them when finished."""
        for url_dict in urls:
            future = self.executor.submit(self.fetch_url, url_dict['url'], url_dict['timeout'])
            # Use of default arguments necessary here because lambdas are produced in a for loop!
            future.add_done_callback(lambda _, url_dict=url_dict, future=future: 
                                     callback(url_dict['id'], future.result()[0], future.result()[1]))

            
