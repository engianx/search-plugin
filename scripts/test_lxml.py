import lxml.etree
from typing import Any, Iterator

xmlp = lxml.etree.XMLParser(
    recover=True, remove_comments=True, resolve_entities=False
)

xmltext = """
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
<url>
<loc>https://dodoutdoors.com/</loc>
<changefreq>daily</changefreq>
</url>
<url>
<loc>https://dodoutdoors.com/products/sugoi-chair</loc>
<lastmod>2025-01-29T13:04:46-08:00</lastmod>
<changefreq>daily</changefreq>
<image:image>
<image:loc>https://cdn.shopify.com/s/files/1/0555/1154/8056/files/1_GIFSUGOITANDEFAULTCopyofGIF8-Versamin2.gif?v=1724230329</image:loc>
<image:title>Sugoi Chair</image:title>
<image:caption>both</image:caption>
</image:image>
</url>
</urlset>
"""

def extract(elem) -> dict[str, Any]:
    d: dict[str, Any] = {}
    for el in elem.getchildren():
        tag = el.tag
        assert isinstance(tag, str)
        name = tag.split("}", 1)[1] if "}" in tag else tag

        if name == "link":
            if "href" in el.attrib:
                d.setdefault("alternate", []).append(el.get("href"))
        else:
            if el.text and el.text.strip():
                d[name] = el.text.strip()
            else:
                d[name] = extract(el)
    return d

def iterate(root) -> Iterator[dict[str, Any]]:
    for elem in root.getchildren():
        d = extract(elem)
        if "loc" in d:
            yield d


root = lxml.etree.fromstring(xmltext, parser=xmlp)

for elem in iter(root):
    print(elem)