# Gevix

Marketing site for Gevix, a design and engineering studio. Four static pages, no build step.

- `index.html` – home
- `work.html` – case studies (`/work`)
- `blog.html` – writing (`/blog`)
- `post.html` – article page; the URL hash picks the post (`/post#week-five`)

## Run locally

```bash
npx serve .
```

## Deploy

Static site on Vercel. `vercel.json` turns on clean URLs so `/work` serves `work.html`.

## Before going live

- Replace the WhatsApp number in each page's `<a class="wa">` (`wa.me/447700900000` is a placeholder).
- Replace `hello@gevix.co` with the real address.
- Add `<link rel="canonical">` and `og:url` once the domain is known.
- Client names, testimonials and figures are placeholders.
