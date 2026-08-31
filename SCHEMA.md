# Data schema reference

The data model behind a CV: what every field means and exactly what it renders
in the PDF.

Examples are written in YAML because that is the only input format the generator
reads today, but the schema itself is format-agnostic — the same field names,
nesting and value rules apply to any config format added later.

Rules that apply everywhere:

- The root key **must** be `cv`. Without it the script aborts with an error
  about the missing `cv` root key.
- Any missing or empty field is skipped without breaking the render (the only
  exception is `name`, see below).
- Fields not listed in this reference are silently ignored. There is no warning:
  if you type `possition` instead of `position`, that data just never shows up.
- Section order in the PDF is fixed and does **not** follow your source file:
  Summary → Experience → Education → Skills → Additional Information.

---

## Display options

Top-level, boolean fields hanging directly off `cv`. They don't map to a piece
of content — they toggle how other fields render.

| Field | Type | Default | What it does |
| --- | --- | --- | --- |
| `show_duration` | boolean | `false` | Show the computed duration (`1 year 4 months`) next to each experience role's dates |
| `show_footer` | boolean | `true` | Print a page footer: `name` bottom-left, `Page N of M` bottom-right |
| `last_updated_date` | string | — | When set (and `show_footer` is on), also prints `Last updated <value>` bottom-center. Free text, printed verbatim |

```yaml
cv:
  show_duration: true
  show_footer: true
  last_updated_date: "August 2026"
```

If omitted, or set to any falsy value, durations are computed but never
printed — the dates themselves (`start_date`/`end_date`) still show either way.
See *Duration* under [Dates](#dates) for how the number itself is computed.

---

## Header

Top-level fields hanging directly off `cv`. Rendered centered.

| Field | Required | What it renders |
| --- | --- | --- |
| `name` | **Yes** | Large bold title (24pt). Also the PDF document title |
| `headline` | No | Line below the name, regular size |
| `location` | No | Contact item with a map-pin icon |
| `phone` | No | Contact item with a phone-handset icon |
| `email` | No | Contact item with an envelope icon |
| `website` | No | Contact item with a link icon |
| `social_networks` | No | One contact item per list entry |

**`name` has no conditional in the template.** If it is missing the PDF still
renders, just with an empty title. You will not see an error on the console.

### Contact line order

Fixed by the template, not by your source file:

```
location · phone · email · website · social_networks (in list order)
```

### `website`

Displayed text has the `https://` and `http://` prefixes stripped — nothing
else, a trailing slash **is kept**. The full value (with a `https://` prefix
added back if you omitted it) becomes a real clickable link in the PDF.

```yaml
website: "https://imcasero.dev"     # renders  imcasero.dev  → links to https://imcasero.dev
website: "https://imcasero.dev/"    # renders  imcasero.dev/ → links to https://imcasero.dev/
website: "imcasero.dev"             # renders  imcasero.dev  → links to https://imcasero.dev
```

### `social_networks`

A list of maps with two keys:

| Key | What it does |
| --- | --- |
| `network` | Picks the icon, **and** which URL template builds the link. Never printed as text |
| `username` | The text that shows, exactly as you write it. Also becomes a real clickable link |

```yaml
social_networks:
  - network: LinkedIn
    username: "imcasero"
  - network: GitHub
    username: "imcasero"
```

Renders: `[LinkedIn icon] imcasero  [GitHub icon] imcasero`, the first linking
to `https://linkedin.com/in/imcasero` and the second to
`https://github.com/imcasero`.

Icons with real artwork: `LinkedIn` and `GitHub` (case-insensitive). Any other
`network` value falls back to the generic link icon — including `GitLab`,
`Twitter` and `X`, which the script's icon-picking helper recognises but the
template does not draw an icon for yet; the link itself still resolves
correctly for those three plus `stackoverflow`.

**How the link is built**, in order:

1. If `username` already contains `://`, it is used as the link exactly as
   written.
2. Else if `username` contains a `.` or a `/` (it looks like a domain or
   path already), it's used as-is with `https://` prepended.
3. Else, for a known `network` (`linkedin`, `github`, `gitlab`, `twitter`, `x`,
   `stackoverflow`), `username` is expanded into that network's profile URL
   template (`https://linkedin.com/in/{username}`, etc.).
4. Otherwise, `username` gets a bare `https://` prepended.

Because `network` is never printed as text, an ATS extracting text sees those
two entries as `imcasero imcasero`, with nothing identifying them — the
trade-off described in the README. If that matters to you, put the full handle
in `username` instead of a bare username; per rule 2 above, it still resolves
to the right link:

```yaml
  - network: LinkedIn
    username: "linkedin.com/in/imcasero"
```

---

## `sections`

Every section lives here. A section with an empty list renders nothing at all,
not even its heading.

### `summary`

A list of **strings**, not maps. Each item becomes a justified paragraph.

```yaml
summary:
  - "Frontend Developer with 3 years of experience..."
  - "Optional second paragraph."
```

Heading rendered: **Summary**

### `experience`

A list of maps, one per company. Each entry can be **flat** (a single role at
that company) or hold a **`positions` list** (several roles at the same
company — promotions, internal moves). The two shapes are mutually exclusive:
if `positions` is present, `position`, `start_date`, `end_date` and
`highlights` on the entry itself are ignored.

#### Flat shape (single role)

A flat entry renders a block that never splits across pages.

| Field | Required | What it renders |
| --- | --- | --- |
| `company` | Yes in practice | First line, in **bold** |
| `position` | No | Follows the company after a comma, not bold |
| `location` | No | First chunk of the metadata line |
| `start_date` | No | Second chunk, formatted (see *Dates*) |
| `end_date` | No | Joined to `start_date` with an en dash |
| `highlights` | No | List of justified bullets |

The metadata line joins with ` · ` only the chunks that exist:

```
location · start_date – end_date · duration
```

Example:

```yaml
- company: "Globant"
  position: "Frontend Developer"
  location: "Madrid, Spain"
  start_date: "2023-08"
  end_date: "2024-11"
  highlights:
    - "First achievement"
```

Renders (with [`show_duration: true`](#display-options); it's `false` by default):

```
Globant, Frontend Developer
Madrid, Spain · Aug 2023 – Nov 2024 · 1 year 4 months
  • First achievement
```

Drop `position` and the line is just `Globant` in bold. Drop `end_date` and
only the start date shows — **the duration disappears**, since it cannot be
computed without an end date.

#### `positions` shape (multiple roles, same company)

| Field | Required | What it renders |
| --- | --- | --- |
| `company` | Yes in practice | Company line, in **bold**, printed once |
| `location` | No | Printed once, right under the company line |
| `positions` | Yes (to use this shape) | One block per role, in the order listed |

Each item inside `positions` is its own map:

| Field | Required | What it renders |
| --- | --- | --- |
| `title` | No | Role name, in *italics* |
| `start_date` | No | First chunk of that role's metadata line |
| `end_date` | No | Joined to `start_date` with an en dash |
| `highlights` | No | List of justified bullets, scoped to that role |

A role's metadata line is just `start_date – end_date · duration` — `location`
does not repeat per role, since it is shared and already printed once above.

List `positions` most-recent-first, the same convention as everything else in
`experience`.

Example:

```yaml
- company: "CaixaBank Tech"
  location: "Madrid, Spain"
  positions:
    - title: "Frontend Squad Lead"
      start_date: "2026-07"
      end_date: "present"
      highlights:
        - "Leading a 3-person team"
    - title: "Frontend Developer"
      start_date: "2024-11"
      end_date: "2026-07"
      highlights:
        - "Built internal tools serving 5,000+ daily users"
```

Renders (with [`show_duration: true`](#display-options); it's `false` by default):

```
CaixaBank Tech
Madrid, Spain

Frontend Squad Lead
Jul 2026 – present · 2 months
  • Leading a 3-person team

Frontend Developer
Nov 2024 – Jul 2026 · 1 year 9 months
  • Built internal tools serving 5,000+ daily users
```

With the default `show_duration: false`, each role's line is just the dates,
e.g. `Jul 2026 – present`.

Unlike the flat shape, an entry with `positions` **can** split across a page
break — but only between two roles, never in the middle of one role's bullets.
With a long list of roles at one company, this is the trade-off that keeps a
single company from being pushed whole onto a fresh page.

Heading rendered: **Experience**

### `education`

Same shape as `experience`, but no bullets and **no computed duration**.

| Field | What it renders |
| --- | --- |
| `institution` | First line, in **bold** |
| `degree` | Follows the institution after a comma |
| `area` | Follows the degree after an em dash (`—`) |
| `location` | First chunk of the metadata line |
| `start_date` / `end_date` | Second chunk |

```yaml
- institution: "IES Domenico Scarlatti"
  area: "Software & Web Development"
  degree: "VET"
  location: "Aranjuez, Spain"
  start_date: "2021-09"
  end_date: "2023-04"
```

Renders:

```
IES Domenico Scarlatti, VET — Software & Web Development
Aranjuez, Spain · Sep 2021 – Apr 2023
```

Note the print order is `degree` then `area`, the reverse of how they are
usually written in the source file.

Heading rendered: **Education**

### `skills`

A list of maps. Each entry is a paragraph, not a bullet.

| Field | What it renders |
| --- | --- |
| `label` | **Bold** label, followed by a colon |
| `details` | Running text after it |

```yaml
- label: "Frontend Development"
  details: "TypeScript, React, Next.js"
```

Renders: **Frontend Development:** TypeScript, React, Next.js

The colon comes from the template. Do not write it into `label`.

Heading rendered: **Skills**

### `additional_information`

A list of maps with a single `bullet` key. It is a map, not a bare string.

```yaml
additional_information:
  - bullet: "EU Citizen (Spanish Passport)"
  - bullet: "Open to hybrid and remote work"
```

Renders a bullet list. Heading rendered: **Additional Information**

---

## Inline Markdown

A small subset of Markdown is rendered inside these text fields:

- `summary` paragraphs
- `experience` → `highlights` (both the flat and the `positions` shapes)
- `skills` → `details`
- `additional_information` → `bullet`

| You write | You get |
| --- | --- |
| `**text**` or `__text__` | **bold** |
| `*text*` or `_text_` | *italic* |
| `` `text` `` | monospace |
| `[label](https://url)` | `label` as a real clickable link, styled as plain text (a bare domain gets `https://` prepended) |

Everything else is HTML-escaped and printed literally, so `<`, `&`, stray `*`
and intra-word `snake_case` underscores are safe. Every other field
(`name`, `headline`, `company`, `title`, dates, …) is plain text — Markdown
there is printed verbatim.

---

## Dates

Expected format: **`YYYY-MM`, with a zero-padded month**.

| You write | You get | Note |
| --- | --- | --- |
| `"2024-11"` | `Nov 2024` | |
| `"2024-1"` | `2024-1` | Without the leading zero it is **not** formatted, just copied through |
| `"present"` | `present` | `actual` and `actualidad` work too |
| `"2024-11-15"` | `Nov 2024` | The day is ignored |
| `"Summer 2024"` | `Summer 2024` | Any unparseable text passes through untouched |

In YAML, always quote them. Unquoted, `2024-11-15` is read as a native date and
`2024-11` as a string: both work, but through different code paths.

### Duration (`experience` only)

Only printed when [`show_duration`](#display-options) is `true` — it defaults
to hidden. Computed from `start_date` and `end_date` either way, and it is
**inclusive** — it counts both the start and the end month.

```
Aug 2023 – Nov 2024  →  16 months  →  "1 year 4 months"
```

With `end_date: "present"` it is computed **against today's date**, so the same
data produces a different number depending on the day you run the script.

The duration is omitted when `start_date` or `end_date` is missing, when either
one is unparseable, or when the end date precedes the start date.

---

## Minimal example

The bare essentials, in YAML:

```yaml
cv:
  name: "First Last"
  email: "you@email.com"
  sections:
    experience:
      - company: "Company"
        position: "Role"
        start_date: "2024-01"
        end_date: "present"
        highlights:
          - "What you did"
```
