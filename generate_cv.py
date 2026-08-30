#!/usr/bin/env python3
"""Transform YAML data to a PDF CV.

Usage:
    python generar_cv.py cv.yaml cv.pdf
"""

import os
import sys
from datetime import date
from pathlib import Path

if sys.platform == "darwin":
    for _prefix in ("/opt/homebrew/lib", "/usr/local/lib"):
        if os.path.isdir(_prefix):
            _current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
            if _prefix not in _current.split(":"):
                os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
                    f"{_prefix}:{_current}" if _current else _prefix
                )

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
TEMPLATE_NAME = "cv.html"

MONTHS = {
    "01": "Jan",
    "02": "Feb",
    "03": "Mar",
    "04": "Apr",
    "05": "May",
    "06": "Jun",
    "07": "Jul",
    "08": "Aug",
    "09": "Sep",
    "10": "Oct",
    "11": "Nov",
    "12": "Dec",
}

ONGOING = ("present", "actual", "actualidad")


def format_date(value):
    """'2024-11' -> 'Nov 2024'. 'present' -> 'present'. Otherwise unchanged."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in ONGOING:
        return "present"
    parts = text.split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1] in MONTHS:
        return f"{MONTHS[parts[1]]} {parts[0]}"
    return text


def _to_months(value):
    """'2024-11' -> absolute number of months. None if it can't be parsed."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in ONGOING:
        today = date.today()
        return today.year * 12 + today.month
    parts = text.split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return int(parts[0]) * 12 + int(parts[1])
    return None


def duration(start, end):
    """'2023-08', '2024-11' -> '1 year 4 months'. Empty string if not applicable."""
    start_m, end_m = _to_months(start), _to_months(end)
    if start_m is None or end_m is None or end_m < start_m:
        return ""
    total = end_m - start_m + 1
    years, months = divmod(total, 12)
    chunks = []
    if years:
        chunks.append(f"{years} year" + ("s" if years != 1 else ""))
    if months:
        chunks.append(f"{months} month" + ("s" if months != 1 else ""))
    return " ".join(chunks) or "1 month"


def network_icon(network):
    """Icon name to use for each known social network."""
    key = (network or "").strip().lower()
    return (
        key if key in ("linkedin", "github", "gitlab", "twitter", "x") else "link"
    )


NETWORK_URL_TEMPLATES = {
    "linkedin": "https://linkedin.com/in/{u}",
    "github": "https://github.com/{u}",
    "gitlab": "https://gitlab.com/{u}",
    "twitter": "https://twitter.com/{u}",
    "x": "https://x.com/{u}",
    "stackoverflow": "https://stackoverflow.com/users/{u}",
}


def ensure_scheme(url):
    """Prefix 'https://' onto a bare domain if no scheme is already present."""
    text = str(url or "").strip()
    if not text or "://" in text:
        return text
    return f"https://{text}"


def network_url(network, username):
    """Full clickable URL for a social_networks entry.

    If `username` already looks like a domain/path (contains '.' or '/'),
    it is treated as already complete and only gets a scheme prefix. Otherwise
    it is expanded via the known network's URL template.
    """
    text = str(username or "").strip()
    if not text:
        return ""
    if "://" in text:
        return text
    if "." in text or "/" in text:
        return ensure_scheme(text)
    key = (network or "").strip().lower()
    if key in NETWORK_URL_TEMPLATES:
        return NETWORK_URL_TEMPLATES[key].format(u=text)
    return ensure_scheme(text)


def load_data(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "cv" not in data:
        raise ValueError(f"{yaml_path}: expected a root key 'cv'.")
    cv = data["cv"] or {}
    cv.setdefault("sections", {})
    cv.setdefault("show_duration", False)
    return cv


def render_html(cv):
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["format_date"] = format_date
    env.filters["duration"] = duration
    env.filters["icon"] = network_icon
    env.filters["ensure_scheme"] = ensure_scheme
    env.filters["network_url"] = network_url
    return env.get_template(TEMPLATE_NAME).render(cv=cv)


def main(argv):
    if len(argv) != 3:
        print(f"Usage: python {Path(argv[0]).name} cv.yaml cv.pdf", file=sys.stderr)
        return 1

    yaml_path = Path(argv[1])
    pdf_path = Path(argv[2])

    if not yaml_path.is_file():
        print(f"Error: file {yaml_path} does not exist", file=sys.stderr)
        return 1

    cv = load_data(yaml_path)
    html = render_html(cv)
    HTML(string=html, base_url=str(BASE_DIR)).write_pdf(str(pdf_path))

    print(f"PDF generated: {pdf_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
