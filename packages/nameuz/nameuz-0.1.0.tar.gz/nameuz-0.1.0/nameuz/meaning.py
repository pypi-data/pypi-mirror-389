import requests
from lxml import html

clean = lambda x: x[0].strip() if x else ""


class Meaning:
    def __init__(self, name: str, page: int = 1):
        self.name = name
        self.page = page

    def response(self):
        try:
            url = f"https://ismlar.com/search/{self.name}?page={self.page}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            rows = tree.xpath("//ul[@class='list-none space-y-2']/li")

            data = []
            for row in rows:
                name = clean(row.xpath(".//h2/a/text()"))
                meaning = clean(row.xpath(".//div[@class='space-y-4']//text()"))

                record = {
                    "name": name,
                    "meaning": meaning
                }

                if all(record.values()):
                    data.append(record)

            return data if data else None
        except Exception:
            return None