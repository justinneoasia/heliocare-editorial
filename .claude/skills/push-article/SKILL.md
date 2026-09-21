---
name: push-article
description: Merge a new or updated Heliocare article dropped in incoming/ (exported from Claude Cowork) into content/state.json, rebuild the site, commit, and push to GitHub so Vercel redeploys. Trigger phrases: "push new article", "push the new article", "push article".
---

Run this from the repo root: `C:\Users\JustinFok\Downloads\projects\heliocare-editorial`.

## 1. Find the new article

List files directly inside `incoming/` (ignore the `incoming/.processed/` subfolder and any
dotfiles). Pick the most recently modified one.

- If `incoming/` is empty, stop and tell the user: export/save the finished article from
  Cowork into the `incoming/` folder first, then run this again.
- If there are several candidate files and it isn't obvious which is the new article, ask
  the user which one before proceeding.

## 2. Turn it into an article object

Read the file. It may already be a JSON object shaped like an entry in
`content/state.json`'s `articles` array, or it may be a plain text/markdown draft.

Either way, produce a single article object with these fields (see existing entries in
`content/state.json` for the exact shape and citation conventions):

- `id` — kebab-case slug. Use one given in the file, otherwise derive from the title.
- `eyebrow`, `title`, `standfirst`, `sub`, `date`
- `byline`, `reviewer` — if not given, use the placeholder style already in the file
  (e.g. `"[Author name, credentials]"`), don't invent a real name or credential.
- `blocks` — array of `{type, html}` blocks (`p`, `h2`, `quote` + `cite`, `figure` + `svg`,
  `table`, `note`, `list`, `slot`), following the type table in `README.md`.
- `faq` — array of `{q, a}`.
- `refs` — array of `{n, html}`, numbered in order of first citation, APA 7th edition,
  matching the `<sup><a href="#rN">N</a></sup>` marker style used elsewhere in the file.

If the draft is missing pieces needed to fill this in faithfully (e.g. no references at
all, or ambiguous structure), ask the user rather than fabricating content or citations.

## 3. Merge into content/state.json

Check whether an article with this `id` already exists in the `articles` array.

- Exists: replace that entire object with the new one (an update).
- New: append it to the end of the `articles` array.

Write the file back preserving the existing 2-space JSON formatting. Leave every other
article untouched.

## 4. Build

From the repo root, run in order, stopping immediately if either fails and reporting the
error without touching git:

```
python build.py
python make_editor.py
```

## 5. Archive the processed file

Move the file from step 1 into `incoming/.processed/` (create that folder if it doesn't
exist) so it isn't picked up again next time.

## 6. Commit and push

Show `git status --short` so the change is visible, then:

```
git add -A
git commit -m "Add article: <title>"        # or "Update article: <title>" if it replaced one
git push
```

If `git push` fails with an authentication/interactive-prompt error (this happens in
sandboxed terminals that disable interactive git prompts), don't try to work around it.
Tell the user the commit is made locally but needs to be pushed from GitHub Desktop (or a
normal, non-sandboxed terminal) since this environment can't complete the GitHub sign-in
prompt.

## 7. Report

Confirm what was added/updated, that it built cleanly, and either that it's pushed (Vercel
will redeploy from `main` automatically) or that a manual push is still needed.
