# ATS-friendly CV generator

Turns a YAML file of CV data into a single-column PDF, built so Applicant
Tracking Systems extract the text in the right order.

YAML → Jinja2 (HTML) → WeasyPrint (PDF). No server, no API.

**Field-by-field reference: [SCHEMA.md](SCHEMA.md)** — what every field means
and exactly what it renders.

## Install

WeasyPrint needs system libraries (pango, cairo, gdk-pixbuf, glib, harfbuzz) on
top of the Python package:

```bash
brew install pango cairo gdk-pixbuf libffi        # macOS
# sudo apt install libpango-1.0-0 libpangoft2-1.0-0   # Debian/Ubuntu

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

On macOS those Homebrew libraries are not on the default `dyld` path and
WeasyPrint fails to import with `cannot load library 'libgobject-2.0-0'`. The
script prepends `/opt/homebrew/lib` (or `/usr/local/lib`) to
`DYLD_FALLBACK_LIBRARY_PATH` before importing WeasyPrint, so you do not need to
export anything by hand.

## Usage

```bash
.venv/bin/python generate_cv.py 30-08-2026-SPAIN.yaml cv.pdf
```

Two arguments, both required: input YAML and output PDF.

## Files

| File | Purpose |
| --- | --- |
| `generate_cv.py` | Loads the YAML, registers the Jinja2 filters, renders and writes the PDF |
| `templates/cv.html` | Template and CSS. Everything visual lives here |
| `SCHEMA.md` | Full data schema reference |
| `requirements.txt` | PyYAML, Jinja2, weasyprint |
| `30-08-2026-SPAIN.yaml` | Sample / real CV data |

## Data at a glance

Everything hangs off a `cv` root key. Any missing field or section is skipped.

```yaml
cv:
  show_duration: false        # optional, defaults to false either way
  name: "Diego Casero Martín"
  headline: "Frontend Developer"
  location: "Madrid area, Spain"
  email: "you@email.com"
  website: "https://imcasero.dev"
  social_networks:
    - network: LinkedIn
      username: "imcasero"

  sections:
    summary:
      - "Frontend Developer with..."
    experience:
      - company: "CaixaBank Tech"       # multiple roles at the same company
        location: "Madrid, Spain"
        positions:
          - title: "Frontend Squad Lead"
            start_date: "2026-07"
            end_date: "present"
            highlights:
              - "..."
          - title: "Frontend Developer"
            start_date: "2024-11"
            end_date: "2026-07"
            highlights:
              - "..."
      - company: "Globant"              # a single role: no `positions` needed
        position: "Frontend Developer"
        location: "Madrid, Spain"
        start_date: "2023-08"
        end_date: "2024-11"
        highlights:
          - "..."
    education:
      - institution: "IES Domenico Scarlatti"
        area: "Software & Web Development"
        degree: "VET"
        start_date: "2021-09"
        end_date: "2023-04"
    skills:
      - label: "Frontend Development"
        details: "TypeScript, React, ..."
    additional_information:
      - bullet: "EU Citizen (Spanish Passport)"
```

Section order in the PDF is fixed (Summary → Experience → Education → Skills →
Additional Information), not the YAML's. To change it, reorder the blocks in
`templates/cv.html`.

See [SCHEMA.md](SCHEMA.md) for every field, date handling, the computed
duration, and the edge cases.

## Template filters

| Filter | Example | Result |
| --- | --- | --- |
| `format_date` | `"2024-11" \| format_date` | `Nov 2024` |
| `duration` | `"2023-08" \| duration("2024-11")` | `1 year 4 months` |
| `icon` | `"LinkedIn" \| icon` | `linkedin` (SVG icon name) |

## ATS design decisions

What makes the PDF parseable, and why it is built this way:

- **Single column.** No row-direction `flex`/`grid`, no `float`, no layout
  tables. Each role's location and dates run full width under the job title,
  not in a right-hand column.
- **DOM order = reading order.** Verified by extracting the text back out of the
  generated PDF.
- **No photo, no images.** The contact icons are inline SVG and purely
  decorative.
- **Web-safe typography:** Arial/Helvetica.
- **Standard section headings:** Summary, Experience, Education, Skills,
  Additional Information.
- **Controlled page breaks** via `break-inside: avoid` per entry and
  `break-after: avoid` on headings, so a heading never strands at the bottom of
  a page. A company with multiple `positions` is the one exception: the page
  can break between two roles, just never inside one role's bullets — see
  [SCHEMA.md](SCHEMA.md#positions-shape-multiple-roles-same-company).

### Known trade-offs

Two places where visual fidelity beat ATS purity. If a job portal ever fails to
autofill from this PDF, start here:

1. **Icons instead of text labels.** Contact details use icons, so in the
   extracted text LinkedIn and GitHub come out as bare `imcasero`, with no word
   identifying the network. To revert, replace the `{{ icon(...) }}` calls in
   the `.contact` block of `templates/cv.html` with plain text (`LinkedIn:`,
   `GitHub:`, `Email:`).
2. **The section rule spans the full width** under the heading, instead of
   starting right after the word. The visually "correct" version needs
   `position: relative` on the `h2` text, and that makes the headings extract
   **at the end of each page**, detached from their content. It was tried and
   rejected: do not reintroduce it without re-checking the extracted text.

## Verifying the output

Checking that the text comes out in a coherent order, which is the whole point:

```bash
.venv/bin/pip install pypdf
.venv/bin/python -c "
from pypdf import PdfReader
for i, p in enumerate(PdfReader('cv.pdf').pages):
    print(f'--- page {i+1} ---'); print(p.extract_text())"
```

Image preview (macOS, first page only):

```bash
sips -s format png cv.pdf --out preview.png
```

## Customising

Everything visual is in the `<style>` block of `templates/cv.html`: page margins
in `@page`, sizes in `body`/`h1`/`h2`, spacing between roles in `.entry`. The
SVG icons live in the `icon()` macro at the top of the body; to add a new
network, add its branch to the macro and its name to the icon-picking helper in
`generate_cv.py`.
