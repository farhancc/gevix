#!/usr/bin/env python3
"""Generate blog/<slug>.html article pages and sitemap.xml from posts.json.

Run after editing posts.json or the shared styles in blog.html:
    python3 build.py
"""
import json, re, html, datetime, pathlib

ROOT = pathlib.Path(__file__).parent
SITE = "https://gevix.in"
posts = json.loads((ROOT / "posts.json").read_text())
base = (ROOT / "blog.html").read_text()

ARTICLE_CSS = (ROOT / "article.css").read_text()
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def iso(d):
    day, mon, year = d.split()
    return f"{year}-{MONTHS[mon]:02d}-{int(day):02d}"


def words(body):
    return len(re.sub(r"<[^>]+>", " ", body).split())


def read_time(body):
    return f"{max(1, round(words(body) / 200))} min read"


def esc(s):
    return html.escape(s, quote=True)


def cover(p):
    if p["color"] == "cobalt":
        return (f'<div class="cover" style="background:var(--cobalt);color:#fff">'
                f'<span style="background:rgba(18,17,26,.3)">{p["cat"]}</span></div>')
    return f'<div class="cover" style="background:var(--{p["color"]})"><span>{p["cat"]}</span></div>'


def card(p):
    return (f'      <a class="post" href="/blog/{p["slug"]}">\n        {cover(p)}\n        <div class="body">\n'
            f'          <h3>{p["title"]}</h3>\n          <p>{p["ex"]}</p>\n'
            f'          <div class="meta"><time datetime="{iso(p["date"])}">{p["date"]}</time><span>{read_time(p["body"])}</span></div>\n'
            f'        </div>\n      </a>')


# Shared chrome from blog.html
head_styles = re.search(r"<style>.*?</style>\n<style>.*?</style>", base, re.S).group(0)
header = re.search(r'<header class="top">.*?</header>', base, re.S).group(0)
footer = re.search(r'<footer class="on-ink">.*?</footer>', base, re.S).group(0)
wa = re.search(r'<a class="wa".*?</a>', base, re.S).group(0)
script = re.search(r"<script>\n\(function\(\)\{\n  var menu=.*?</script>", base, re.S).group(0)
fonts = re.search(r'<link rel="preload"[^\n]*\n<link rel="preload"[^\n]*\n<style>[^<]*</style>', base, re.S).group(0)


def article_page(i, p):
    prev = posts[i - 1] if i > 0 else None
    nxt = posts[i + 1] if i < len(posts) - 1 else None
    url = f"{SITE}/blog/{p['slug']}"
    on = "on-cobalt" if p["color"] == "cobalt" else f"on-{p['color']}"
    pill = ' style="background:rgba(18,17,26,.3)"' if p["color"] == "cobalt" else ""
    title = f"{p['title']} | Gevix"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "@id": url + "#article", "headline": p["title"], "description": p["ex"],
         "url": url, "mainEntityOfPage": url, "datePublished": iso(p["date"]), "dateModified": iso(p["date"]),
         "author": {"@type": "Person", "name": html.unescape(p["authorName"]), "jobTitle": p["authorRole"]},
         "publisher": {"@id": f"{SITE}/#org"}, "image": f"{SITE}/og-image.png",
         "articleSection": p["cat"], "wordCount": words(p["body"]), "inLanguage": "en",
         "isPartOf": {"@id": f"{SITE}/blog#blog"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Writing", "item": SITE + "/blog"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]}]}
    nav = '<nav class="post-nav" aria-label="Adjacent posts">'
    nav += (f'<a href="/blog/{prev["slug"]}"><span>Newer</span><b>{prev["title"]}</b></a>' if prev else "<span></span>")
    nav += (f'<a href="/blog/{nxt["slug"]}" class="next"><span>Older</span><b>{nxt["title"]}</b></a>' if nxt else "<span></span>")
    nav += "</nav>"
    more = "\n".join(card(q) for q in [q for q in posts if q["slug"] != p["slug"]][:3])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<title>{esc(title)}</title>
<meta name="description" content="{esc(p['ex'])}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Gevix">
<meta property="og:title" content="{esc(p['title'])}">
<meta property="og:description" content="{esc(p['ex'])}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="article:published_time" content="{iso(p['date'])}">
<meta property="article:section" content="{p['cat']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(p['title'])}">
<meta name="twitter:description" content="{esc(p['ex'])}">
<meta name="twitter:image" content="{SITE}/og-image.png">
<meta name="theme-color" content="#2B3FFF">
<script type="application/ld+json">{json.dumps(ld)}</script>
{fonts}
{head_styles}
<style>
{ARTICLE_CSS}</style>
</head>
<body>
{header}

<main>
<section class="post-hero {on}">
  <div class="wrap">
    <a class="crumb" href="/blog">Writing</a>
    <span class="cat"{pill}>{p['cat']}</span>
    <h1>{p['title']}</h1>
    <div class="byline"><i style="background:var(--{p['authorColor']})">{p['authorInit']}</i><div><b>{p['authorName']}</b><span>{p['authorRole']}</span></div><time class="sep" datetime="{iso(p['date'])}">{p['date']}</time><span class="sep">{read_time(p['body'])}</span></div>
  </div>
</section>

<section class="field on-paper">
  <div class="wrap">
    <article class="article" style="--accent:var(--{p['color']})">{p['body']}
    </article>
    {nav}
  </div>
</section>

<section class="field on-paper more" style="padding-top:0">
  <div class="wrap">
    <h2>More writing</h2>
    <div class="posts">
{more}
    </div>
    <div class="posts-more"><a class="btn btn-cobalt" href="/blog">All posts</a></div>
  </div>
</section>
</main>

{footer}

{wa}
{script}
</body>
</html>
"""


(ROOT / "blog").mkdir(exist_ok=True)
for i, p in enumerate(posts):
    (ROOT / "blog" / f"{p['slug']}.html").write_text(article_page(i, p))

latest = max(iso(p["date"]) for p in posts)
urls = [(SITE + "/", latest), (SITE + "/work", latest), (SITE + "/blog", latest)]
urls += [(f"{SITE}/blog/{p['slug']}", iso(p["date"])) for p in posts]
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sm += [f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls]
sm.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n")
print(f"built {len(posts)} articles, sitemap with {len(urls)} URLs")
