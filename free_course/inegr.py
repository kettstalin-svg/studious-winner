import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SEARCH_HOST = "poisk-evka.ru"
SEARCH_PATH = "/search"

class PoiskEvkaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_link = False
        self.current_link = None
        self.results = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        href = attrs.get("href")
        if tag == "a" and href:
            if href.startswith("/"):
                href = urllib.parse.urljoin(f"https://{SEARCH_HOST}", href)
            if href.startswith(f"https://{SEARCH_HOST}") or href.startswith(f"http://{SEARCH_HOST}"):
                self.current_link = {"href": href, "text": ""}
                self.in_link = True

    def handle_data(self, data):
        if self.in_link and self.current_link is not None:
            self.current_link["text"] += data.strip()

    def handle_endtag(self, tag):
        if tag == "a" and self.in_link and self.current_link is not None:
            if self.current_link["text"]:
                self.results.append(self.current_link)
            self.current_link = None
            self.in_link = False


def search_poiskevka(query):
    params = urllib.parse.urlencode({"q": query}, encoding="utf-8")
    url = f"https://{SEARCH_HOST}{SEARCH_PATH}?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(request, timeout=15) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = PoiskEvkaParser()
    parser.feed(html)
    return url, parser.results[:10]


def main():
    if len(sys.argv) < 2:
        print("Usage: python inegr.py <search query>")
        return

    query = " ".join(sys.argv[1:])
    url, results = search_poiskevka(query)

    print("Search URL:", url)
    if results:
        print("Found links:")
        for item in results:
            print("-", item["text"] or item["href"])
            print("  ", item["href"])
    else:
        print("No results found or no links extracted.")


if __name__ == "__main__":
    main()
