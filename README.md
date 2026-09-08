# Heliocare Editorial

Static mirror of the finished Heliocare photoprotection articles, for the Singapore market.

**This is a draft mirror, not a publishing destination.** Nothing here is bylined, medically
reviewed or illustrated yet. Every page carries a `noindex, nofollow` meta tag, `robots.txt`
disallows everything, and `vercel.json` sets an `X-Robots-Tag` header, so search engines
should not index it. Anyone with the URL can still read it: on Vercel's Hobby plan the
production domain is publicly accessible, and password protection is an Enterprise feature or
a paid Pro add-on.

## Where the content lives

All article content is in **`content/state.json`**. That is the single source of truth.
`build.py` reads it and writes plain HTML into `public/`. There is no framework and no
dependencies beyond Python 3.

```
content/state.json   the articles: title, standfirst, blocks, FAQ, references
build.py             generates public/ from state.json
public/              deployed output (do not hand-edit; it is regenerated)
vercel.json          output directory, clean URLs, noindex header
```

## Editing

```bash
python3 build.py
```

Then commit and push. Vercel redeploys on every push to `main`.

Blocks in `state.json` use these types:

| type | fields | renders as |
|---|---|---|
| `p` | `html` | paragraph |
| `h2` | `html` | section heading |
| `quote` | `html`, `cite` | pull quote with attribution |
| `figure` | `svg`, `html` | inline SVG with caption |
| `table` | `html` | scrollable table |
| `note` | `html` | callout box |
| `list` | `html` | bulleted list |
| `slot` | `html` | **internal only, stripped from the public build** |

`slot` blocks are photography briefs and production notes. `build.py` filters them out, so they
stay in `state.json` for internal use and never reach the site.

## Deploying

1. In Vercel, **Add New → Project**, import this repository.
2. Framework preset: **Other**. Leave the build command empty.
3. Output directory: `public` (already set in `vercel.json`).
4. Deploy.

Every later push to `main` deploys automatically.

## Editing surface

Browser editing lives in the Claude artifact, not here. This repo is the published mirror.
Keep `content/state.json` as the source of truth for both, so the two do not drift.

## Sources

Every statistic in every article carries a numbered reference in APA 7th edition, ordered by
first citation. Two articles cite manufacturer-funded trials; that funding is disclosed in the
body text at the point of citation rather than only in the reference list.
