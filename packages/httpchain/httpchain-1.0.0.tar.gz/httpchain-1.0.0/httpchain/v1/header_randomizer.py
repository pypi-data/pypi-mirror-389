# httpchain/header_randomizer.py

import time
from typing import Dict, Optional


class HeaderRandomizer:
    """Simple header randomizer that generates random browser-like headers."""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    ACCEPT_HEADERS = [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "*/*",
    ]
    
    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en-US;q=0.9,en;q=0.8",
        "en-US,en;q=0.8",
        "en,en-US;q=0.9",
    ]
    
    ACCEPT_ENCODINGS = [
        "gzip, deflate, br",
        "gzip, deflate",
        "gzip",
    ]
    
    def __init__(self):
        # Use time for randomization
        self._seed = int(time.time() * 1000000) % 2147483647
        self._counter = 0
    
    def _random_choice(self, choices):
        """Simple random choice without external libs."""
        if not choices:
            return ""
        # Simple LCG
        a = 1103515245
        c = 12345
        m = 2147483647
        self._seed = (a * self._seed + c + self._counter) % m
        self._counter += 1
        return choices[self._seed % len(choices)]
    
    def generate_headers(self, base_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Generate random headers and merge with base headers."""
        headers = {
            "User-Agent": self._random_choice(self.USER_AGENTS),
            "Accept": self._random_choice(self.ACCEPT_HEADERS),
            "Accept-Language": self._random_choice(self.ACCEPT_LANGUAGES),
            "Accept-Encoding": self._random_choice(self.ACCEPT_ENCODINGS),
            "Connection": "keep-alive",
        }
        
        # Merge with base headers (base headers override)
        if base_headers:
            for key, value in base_headers.items():
                headers[key] = value
        
        return headers


# Simple function for direct use
def get_random_headers(base_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Get random headers with optional base headers."""
    randomizer = HeaderRandomizer()
    return randomizer.generate_headers(base_headers)
