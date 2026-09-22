---
name: push-article
description: Merge a new or updated Heliocare article dropped in incoming/ (exported from Claude Cowork) into content/state.json, rebuild the site and the browser editor, then stop for the user to review and edit before anything is committed. Trigger phrases: "push new article", "push the new article", "push article".
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

Neither Python nor git is on PATH on this machine. Use the full paths:

- Python: `C:\Users\JustinFok\AppData\Local\Programs\Python\Python313\python.exe`
- git: prepend `C:\Users\JustinFok\AppData\Local\GitHubDesktop\app-3.6.5\resources\app\git\cmd` to `$env:PATH`

From the repo root, run in order, stopping immediately if either fails and reporting the
error without touching git:

```
python build.py
python make_editor.py
```

**Both, every time.** `make_editor.py` regenerates `editor.html`, which is what makes the
new article editable in the browser. Run it last, after the final build, so the editor
reflects the finished `state.json`. The review gate in step 6 depends on it.

## 5. Archive the processed file

Move the file from step 1 into `incoming/.processed/` (create that folder if it doesn't
exist) so it isn't picked up again next time.

## 6. Stop for review

**Do not run `git add`, `git commit` or `git push` yet.** The user reviews and edits every
article before anything reaches git. Leave the working tree dirty and hand the draft over:

- report what was added or updated, the word count and reference count, and that it built
  cleanly
- name anything that looked borderline against the brief's Stage 4 compliance gate
- point them at `editor.html` in the repo root to open in a browser
- remind them that after editing they press **Save state.json**, replace
  `content/state.json` with the downloaded file, and ask for a rebuild

Then stop and wait. Do not commit to "save the work", and do not carry a previous
article's approval over to this one.

## 7. Commit, only after the user approves

When the user says the draft is good, or hands back an edited `state.json`:

1. If `content/state.json` was replaced, re-run `python build.py` then `python make_editor.py`.
2. Show `git status --short`, then:

```
git add -A
git commit -m "Add article: <title>"        # or "Update article: <title>" if it replaced one
```

Don't attempt `git push`. This machine has no non-interactive GitHub credentials, so the
push fails with `could not read Username for 'https://github.com'`. Tell the user the
commit is local and needs pushing from GitHub Desktop, which triggers the Vercel redeploy.
