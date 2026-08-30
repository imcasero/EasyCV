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

## Header

Top-level fields hanging directly off `cv`. Rendered centered.

| Field | Required | What it renders |
| --- | --- | --- |
| `name` | **Yes** | Large bold title (24pt). Also the PDF document title |
| `headline` | No | Line below the name, regular size |
| `location` | No | Contact item with a map-pin icon |
| `phone` | No | Contact item with the generic link icon |
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

Only the `https://` and `http://` prefixes are stripped. Nothing else — a
trailing slash **is kept**.

```yaml
website: "https://imcasero.dev"     # renders  imcasero.dev
website: "https://imcasero.dev/"    # renders  imcasero.dev/
```

### `social_networks`

A list of maps with two keys:

| Key | What it does |
| --- | --- |
| `network` | **Only picks the icon. It is never printed anywhere** |
| `username` | The text that shows, exactly as you write it |

```yaml
social_networks:
  - network: LinkedIn
    username: "imcasero"
  - network: GitHub
    username: "imcasero"
```

Renders: `[LinkedIn icon] imcasero  [GitHub icon] imcasero`

Icons with real artwork: `LinkedIn` and `GitHub` (case-insensitive). Any other
`network` value falls back to the generic link icon — including `GitLab`,
`Twitter` and `X`, which the script's icon-picking helper recognises but the
template does not draw yet.

Because `network` is never printed, an ATS extracting text sees those two
entries as `imcasero imcasero`, with nothing identifying them. This is the
trade-off described in the README. If it matters to you, put the full handle in
`username`:

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

A list of maps. Each entry renders a block that never splits across pages.

| Field | Required | What it renders |
| --- | --- | --- |
| `company` | Yes in practice | First line, in **bold** |
| `position` | No | Follows the company after a comma, not bold |
| `location` | No | First chunk of the metadata line |
| `start_date` | No | Second chunk, formatted (see *Dates*) |
| `end_date` | No | Joined to `start_date` with an en dash |
| `highlights` | No | List of justified bullets |

The second line joins with ` · ` only the chunks that exist:

```
location · start_date – end_date · duration
```

Example:

```yaml
- company: "CaixaBank Tech"
  position: "Frontend Squad Lead"
  location: "Madrid, Spain"
  start_date: "2024-11"
  end_date: "present"
  highlights:
    - "First achievement"
```

Renders:

```
CaixaBank Tech, Frontend Squad Lead
Madrid, Spain · Nov 2024 – present · 1 year 10 months
  • First achievement
```

Drop `position` and the line is just `CaixaBank Tech` in bold. Drop `end_date`
and only the start date shows — **the duration disappears**, since it cannot be
computed without an end date.

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

Computed from `start_date` and `end_date`, and it is **inclusive** — it counts
both the start and the end month.

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
