import requests
import os

from bs4 import BeautifulSoup

INDEX_URL = 'https://datatracker.ietf.org/doc/recent'
RFC_URL = 'https://tools.ietf.org/html/{}'
WG = 'IETF'


class IETFDraft:
    def __init__(self, cache_dir):
        self.cache_path = os.path.join(cache_dir, 'ietfdraft')
        self.cache = self._load_cache()

    def _load_cache(self):
        seen = {}
        if not os.path.exists(self.cache_path):
            return seen
        with open(self.cache_path) as cache:
            for line in cache.readlines():
                rfc_id = line.strip()
                seen[rfc_id] = True
        return seen

    def fetch(self):
        response = requests.get(INDEX_URL)
        if not response.ok:
            raise Exception('Failed to fetch IETF Draft results: {}'.format(
                response.text))
        cache_file = open(self.cache_path, 'w')
        soup = BeautifulSoup(response.text, 'html5lib')
        rows = soup.findAll('td', 'doc')
        for row in rows:
            rfc_id = row.find('a').text.strip()
            url = RFC_URL.format(rfc_id)
            title = row.find('b').text.strip()
            cache_file.write(rfc_id + '\n')
            if rfc_id in self.cache:
                continue
            yield {
                'wg': WG,
                'id': rfc_id,
                'title': title,
                'url': url
            }
        cache_file.close()
