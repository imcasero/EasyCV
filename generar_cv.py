#!/usr/bin/env python3
"""Transform YAML data to a PDF CV.

Uso:
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

MESES = {
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

EN_CURSO = ("present", "actual", "actualidad")


def formatear_fecha(valor):
    """'2024-11' -> 'Nov 2024'. 'present' -> 'present'. Resto tal cual."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    if texto.lower() in EN_CURSO:
        return "present"
    partes = texto.split("-")
    if len(partes) >= 2 and partes[0].isdigit() and partes[1] in MESES:
        return f"{MESES[partes[1]]} {partes[0]}"
    return texto


def _a_meses(valor):
    """'2024-11' -> numero absoluto de meses. None si no se puede parsear."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto.lower() in EN_CURSO:
        hoy = date.today()
        return hoy.year * 12 + hoy.month
    partes = texto.split("-")
    if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit():
        return int(partes[0]) * 12 + int(partes[1])
    return None


def duracion(inicio, fin):
    """'2023-08', '2024-11' -> '1 year 4 months'. Cadena vacia si no aplica."""
    ini, f = _a_meses(inicio), _a_meses(fin)
    if ini is None or f is None or f < ini:
        return ""
    total = f - ini + 1
    anios, meses = divmod(total, 12)
    trozos = []
    if anios:
        trozos.append(f"{anios} year" + ("s" if anios != 1 else ""))
    if meses:
        trozos.append(f"{meses} month" + ("s" if meses != 1 else ""))
    return " ".join(trozos) or "1 month"


def icono_red(network):
    """Nombre del icono a usar para cada red social conocida."""
    clave = (network or "").strip().lower()
    return (
        clave if clave in ("linkedin", "github", "gitlab", "twitter", "x") else "link"
    )


def cargar_datos(ruta_yaml):
    with open(ruta_yaml, "r", encoding="utf-8") as f:
        datos = yaml.safe_load(f)
    if not isinstance(datos, dict) or "cv" not in datos:
        raise ValueError(f"{ruta_yaml}: se esperaba una clave raiz 'cv'.")
    cv = datos["cv"] or {}
    cv.setdefault("sections", {})
    return cv


def renderizar_html(cv):
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["fecha"] = formatear_fecha
    env.filters["duracion"] = duracion
    env.filters["icono"] = icono_red
    return env.get_template(TEMPLATE_NAME).render(cv=cv)


def main(argv):
    if len(argv) != 3:
        print(f"Uso: python {Path(argv[0]).name} cv.yaml cv.pdf", file=sys.stderr)
        return 1

    ruta_yaml = Path(argv[1])
    ruta_pdf = Path(argv[2])

    if not ruta_yaml.is_file():
        print(f"Error: no existe el archivo {ruta_yaml}", file=sys.stderr)
        return 1

    cv = cargar_datos(ruta_yaml)
    html = renderizar_html(cv)
    HTML(string=html, base_url=str(BASE_DIR)).write_pdf(str(ruta_pdf))

    print(f"PDF generado: {ruta_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
