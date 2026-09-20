#!/usr/bin/env python3
"""Generate blog/<slug>.html, the dynamic sections of blog.html/work.html, and
sitemap.xml from content/posts/*.json and content/work/*.json.

Run after editing content by hand, or automatically on every Vercel deploy
(see vercel.json's buildCommand). Content is normally edited through the CMS
at /admin instead of by hand.
"""
import json, re, html, datetime, pathlib

ROOT = pathlib.Path(__file__).parent
SITE = "https://gevix.in"

posts = sorted(
    (json.loads(f.read_text()) for f in (ROOT / "content" / "posts").glob("*.json")),
    key=lambda p: p["date"], reverse=True,
)
work_items = sorted(
    (json.loads(f.read_text()) for f in (ROOT / "content" / "work").glob("*.json")),
    key=lambda w: w["order"],
)

base = (ROOT / "blog.html").read_text()
ARTICLE_CSS = (ROOT / "article.css").read_text()


def display_date(iso_date):
    return datetime.date.fromisoformat(iso_date).strftime("%-d %b %Y")


def esc(s):
    return html.escape(s, quote=True)


def md_to_html(body):
    """Small markdown-lite -> HTML converter covering exactly what article
    bodies use: paragraphs, ## headings, - lists, > blockquotes, **bold**,
    `code` and [text](url) links."""
    def inline(s):
        s = html.escape(s, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
        return s

    blocks = re.split(r"\n\s*\n", body.strip())
    out = []
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        if lines[0].startswith("## "):
            out.append(f"<h2>{inline(lines[0][3:].strip())}</h2>")
        elif lines[0].startswith("> "):
            out.append(f"<blockquote>{inline(' '.join(l[2:].strip() for l in lines))}</blockquote>")
        elif lines[0].startswith("- "):
            items = "".join(f"<li>{inline(l[2:].strip())}</li>" for l in lines)
            out.append(f"<ul>{items}</ul>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)


def words(body_html):
    return len(re.sub(r"<[^>]+>", " ", body_html).split())


def read_time(body_html):
    return f"{max(1, round(words(body_html) / 200))} min read"


def cover(p):
    image = p.get("coverImage")
    if image:
        style = f"background:var(--{p['color']}) url('{esc(image)}') center/cover no-repeat;color:#fff"
        return (f'<div class="cover" style="{style}">'
                f'<span style="background:rgba(18,17,26,.55)">{p["cat"]}</span></div>')
    if p["color"] == "cobalt":
        return (f'<div class="cover" style="background:var(--cobalt);color:#fff">'
                f'<span style="background:rgba(18,17,26,.3)">{p["cat"]}</span></div>')
    return f'<div class="cover" style="background:var(--{p["color"]})"><span>{p["cat"]}</span></div>'


def card(p):
    return (f'      <a class="post" href="/blog/{p["slug"]}" data-cat="{p["cat"].lower()}">\n        {cover(p)}\n        <div class="body">\n'
            f'          <h3>{p["title"]}</h3>\n          <p>{p["ex"]}</p>\n'
            f'          <div class="meta"><time datetime="{p["date"]}">{display_date(p["date"])}</time><span>{read_time(md_to_html(p["body"]))}</span></div>\n'
            f'        </div>\n      </a>')


def featured(p):
    return (f'    <a class="featured" href="/blog/{p["slug"]}" data-cat="{p["cat"].lower()}">\n      {cover(p)}\n      <div class="body">\n'
            f'        <h2>{p["title"]}</h2>\n        <p>{p["ex"]}</p>\n'
            f'        <div class="meta"><time datetime="{p["date"]}">{display_date(p["date"])}</time><span>{read_time(md_to_html(p["body"]))}</span><span>{p["authorName"]}</span></div>\n'
            f'      </div>\n    </a>')


def posts_section_html(posts):
    grid = "\n".join(card(p) for p in posts[1:])
    return f"{featured(posts[0])}\n    <div class=\"posts\">\n{grid}\n    </div>"


def blog_ld_json(posts):
    ld = {"@context": "https://schema.org", "@type": "Blog", "@id": f"{SITE}/blog#blog",
          "url": f"{SITE}/blog", "name": "Gevix Writing",
          "description": "Notes from the Gevix studio on process, design and engineering.",
          "publisher": {"@id": f"{SITE}/#org"}, "inLanguage": "en",
          "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f"{SITE}/blog/{p['slug']}",
                        "datePublished": p["date"], "author": {"@type": "Person", "name": p["authorName"]}}
                       for p in posts]}
    return f'<script type="application/ld+json">{json.dumps(ld)}</script>'


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
    body_html = md_to_html(p["body"])
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "@id": url + "#article", "headline": p["title"], "description": p["ex"],
         "url": url, "mainEntityOfPage": url, "datePublished": p["date"], "dateModified": p["date"],
         "author": {"@type": "Person", "name": p["authorName"], "jobTitle": p["authorRole"]},
         "publisher": {"@id": f"{SITE}/#org"}, "image": f"{SITE}/og-image.png",
         "articleSection": p["cat"], "wordCount": words(body_html), "inLanguage": "en",
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
    cover_image_html = ""
    cover_section_style = ""
    if p.get("coverImage"):
        cover_image_html = (f'<div class="wrap" style="margin-top:32px">\n'
                            f'  <img src="{esc(p["coverImage"])}" alt="" style="width:100%;max-height:440px;'
                            f'object-fit:cover;border-radius:18px;box-shadow:0 30px 60px rgba(18,17,26,.16);display:block">\n'
                            f'</div>')
        cover_section_style = ' style="padding-top:40px"'
    return f"""<!doctype html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-E1Q7JSZ5PY"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', 'G-E1Q7JSZ5PY');
</script>
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
<meta property="article:published_time" content="{p['date']}">
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
    <div class="byline"><i style="background:var(--{p['authorColor']})">{p['authorInit']}</i><div><b>{p['authorName']}</b><span>{p['authorRole']}</span></div><time class="sep" datetime="{p['date']}">{display_date(p['date'])}</time><span class="sep">{read_time(body_html)}</span></div>
  </div>
</section>

{cover_image_html}
<section class="field on-paper"{cover_section_style}>
  <div class="wrap">
    <article class="article" style="--accent:var(--{p['color']})">
{body_html}
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


def inject(text, name, new_content):
    start, end = f"<!-- BUILD:{name}:START -->", f"<!-- BUILD:{name}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    return pattern.sub(lambda m: f"{start}\n{new_content}\n{end}", text, count=1)


def work_mockup(w):
    image = w.get("image")
    if image:
        frame_style = ("width:100%;aspect-ratio:16/10;border-radius:18px;overflow:hidden;"
                       "box-shadow:0 30px 60px rgba(18,17,26,.22)")
        return (f'          <div aria-hidden="true" style="{frame_style}">'
                f'<img src="{esc(image)}" alt="" style="width:100%;height:100%;object-fit:cover;display:block">'
                f'</div>')
    return w.get("mockupHtml", "").rstrip()


def work_li(w):
    data_type = " ".join(w["dataType"])
    tags = "".join(f"<span>{t}</span>" for t in w["tags"])
    bullets = "".join(f"<li>{b}</li>" for b in w["bullets"])
    return (f'<li data-type="{data_type}" class="w-{w["color"]}" id="{w["slug"]}">\n'
            f'        <div class="work-frame" role="img" aria-label="{esc(w["ariaLabel"])}">\n'
            f'{work_mockup(w)}\n        </div>\n'
            f'        <div class="work-text">\n'
            f'          <h2>{w["title"]}</h2>\n'
            f'          <p>{w["description"]}</p>\n'
            f'          <ul class="did">{bullets}</ul>\n'
            f'          <div class="tags">{tags}</div>\n'
            f'          <p class="result">{w["result"]}</p>\n'
            f'        </div>\n      </li>')


def work_ld_json(work_items):
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": f"{SITE}/work",
          "url": f"{SITE}/work", "name": "Work by Gevix", "isPartOf": {"@id": f"{SITE}/#website"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1,
               "item": {"@type": "CreativeWork", "name": w["title"], "url": f"{SITE}/work#{w['slug']}",
                        "creator": {"@id": f"{SITE}/#org"}}}
              for i, w in enumerate(work_items)]}}
    return f'<script type="application/ld+json">{json.dumps(ld)}</script>'


(ROOT / "blog").mkdir(exist_ok=True)
for i, p in enumerate(posts):
    (ROOT / "blog" / f"{p['slug']}.html").write_text(article_page(i, p))

blog_html = inject(base, "POSTS", posts_section_html(posts))
blog_html = inject(blog_html, "BLOG-LD", blog_ld_json(posts))
(ROOT / "blog.html").write_text(blog_html)

work_html = (ROOT / "work.html").read_text()
work_html = inject(work_html, "WORK", "\n".join(work_li(w) for w in work_items))
work_html = inject(work_html, "WORK-LD", work_ld_json(work_items))
work_html = re.sub(r"Showing \d+ projects", f"Showing {len(work_items)} projects", work_html)
(ROOT / "work.html").write_text(work_html)

latest = max(p["date"] for p in posts)
urls = [(SITE + "/", latest), (SITE + "/work", latest), (SITE + "/blog", latest)]
urls += [(f"{SITE}/blog/{p['slug']}", p["date"]) for p in posts]
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sm += [f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls]
sm.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n")
print(f"built {len(posts)} articles, {len(work_items)} case studies, sitemap with {len(urls)} URLs")
