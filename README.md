# Generador de CV ATS-friendly

Convierte un YAML con los datos de tu CV en un PDF de una sola columna, pensado
para que los ATS (Applicant Tracking Systems) extraigan el texto en el orden
correcto.

YAML → Jinja2 (HTML) → WeasyPrint (PDF). Sin servidor, sin API.

## Instalación

WeasyPrint necesita librerías de sistema (pango, cairo, gdk-pixbuf, glib,
harfbuzz) además del paquete Python:

```bash
brew install pango cairo gdk-pixbuf libffi        # macOS
# sudo apt install libpango-1.0-0 libpangoft2-1.0-0   # Debian/Ubuntu

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

En macOS esas librerías de Homebrew no están en el `dyld` path por defecto y
WeasyPrint falla al importar con `cannot load library 'libgobject-2.0-0'`. El
script añade `/opt/homebrew/lib` (o `/usr/local/lib`) a
`DYLD_FALLBACK_LIBRARY_PATH` antes de importar WeasyPrint, así que no hace falta
exportar nada a mano.

## Uso

```bash
.venv/bin/python generar_cv.py 30-08-2026-SPAIN.yaml cv.pdf
```

Dos argumentos, ambos obligatorios: YAML de entrada y PDF de salida.

## Archivos

| Archivo | Qué hace |
| --- | --- |
| `generar_cv.py` | Carga el YAML, registra los filtros Jinja2, renderiza y escribe el PDF |
| `templates/cv.html` | Plantilla y CSS. Aquí se toca todo lo visual |
| `requirements.txt` | PyYAML, Jinja2, weasyprint |
| `30-08-2026-SPAIN.yaml` | CV de ejemplo / datos reales |

## Esquema del YAML

Todo cuelga de una clave raíz `cv`. Cualquier campo o sección ausente se omite
del PDF sin romper nada.

```yaml
cv:
  name: "Diego Casero Martín"      # obligatorio
  headline: "Frontend Developer"
  location: "Madrid area, Spain"
  phone: "+34 600 000 000"          # opcional, no está en el ejemplo
  email: "tu@email.com"
  website: "https://imcasero.dev"   # el https:// se quita al mostrarlo
  social_networks:
    - network: LinkedIn             # solo LinkedIn y GitHub tienen icono propio
      username: "imcasero"          # el resto usa el icono genérico de enlace

  sections:
    summary:                        # lista de párrafos
      - "Frontend Developer with..."

    experience:
      - company: "CaixaBank Tech"
        position: "Frontend Squad Lead"
        location: "Madrid, Spain"
        start_date: "2024-11"       # formato YYYY-MM
        end_date: "present"         # o YYYY-MM
        highlights:                 # lista de bullets
          - "..."

    education:
      - institution: "IES Domenico Scarlatti"
        area: "Software & Web Development"
        degree: "VET"
        location: "Aranjuez, Spain"
        start_date: "2021-09"
        end_date: "2023-04"

    skills:
      - label: "Frontend Development"
        details: "TypeScript, React, ..."

    additional_information:
      - bullet: "EU Citizen (Spanish Passport)"
```

El orden de las secciones en el PDF es fijo (Summary → Experience → Education →
Skills → Additional Information), no el del YAML. Para cambiarlo, reordena los
bloques en `templates/cv.html`.

### Fechas

`start_date` y `end_date` se escriben como `YYYY-MM`. El script formatea
`2024-11` → `Nov 2024`, y `present` (o `actual`/`actualidad`) → `present`.

En Experience se añade además la duración calculada (`1 year 10 months`). Si
`end_date` es `present`, se calcula **contra la fecha de hoy**, así que el mismo
YAML genera un número distinto según el día en que ejecutes el script. Education
no muestra duración.

## Filtros Jinja2 disponibles en la plantilla

| Filtro | Ejemplo | Resultado |
| --- | --- | --- |
| `fecha` | `"2024-11" \| fecha` | `Nov 2024` |
| `duracion` | `"2023-08" \| duracion("2024-11")` | `1 year 4 months` |
| `icono` | `"LinkedIn" \| icono` | `linkedin` (nombre del icono SVG) |

`icono` devuelve además `gitlab`, `twitter` y `x`, pero el macro `icono()` de la
plantilla todavía no dibuja esos tres: caen al icono genérico de enlace. Lo
mismo pasa con `phone`.

## Decisiones de diseño ATS

Lo que hace el PDF parseable, y por qué está así:

- **Una sola columna.** Sin `flex`/`grid` en fila, sin `float`, sin tablas de
  maquetación. La ubicación y las fechas de cada puesto van a ancho completo
  bajo el nombre del puesto, no en una columna derecha.
- **Orden del DOM = orden de lectura.** Verificado extrayendo el texto del PDF
  generado.
- **Sin foto ni imágenes.** Los iconos de contacto son SVG inline, decorativos.
- **Tipografía web-safe:** Arial/Helvetica.
- **Headers de sección estándar:** Summary, Experience, Education, Skills,
  Additional Information.
- **Saltos de página controlados** con `break-inside: avoid` por entrada y
  `break-after: avoid` en los headers, para que un título no quede huérfano al
  final de una página.

### Concesiones conocidas

Dos puntos donde la fidelidad visual gana a la pureza ATS. Si algún portal te
falla al autocompletar, empieza por aquí:

1. **Iconos en vez de labels de texto.** El contacto se muestra con iconos, así
   que en el texto extraído LinkedIn y GitHub salen como `imcasero` a secas, sin
   la palabra que identifica la red. Para revertirlo, sustituye en
   `templates/cv.html` las llamadas `{{ icono(...) }}` del bloque `.contacto`
   por texto plano (`LinkedIn:`, `GitHub:`, `Email:`).
2. **La regla de sección cruza todo el ancho** bajo el título, en lugar de
   arrancar justo después de la palabra. La versión "correcta" visualmente
   requiere `position: relative` sobre el texto del `h2`, y eso hace que los
   headers se extraigan **al final de cada página**, separados de su contenido.
   Se probó y se descartó: no lo reintroduzcas sin volver a comprobar el texto
   extraído.

## Verificar el resultado

Comprobar que el texto sale en orden coherente, que es el punto de todo esto:

```bash
.venv/bin/pip install pypdf
.venv/bin/python -c "
from pypdf import PdfReader
for i, p in enumerate(PdfReader('cv.pdf').pages):
    print(f'--- pág {i+1} ---'); print(p.extract_text())"
```

Vista previa como imagen (macOS, solo primera página):

```bash
sips -s format png cv.pdf --out preview.png
```

## Personalizar

Todo lo visual está en el `<style>` de `templates/cv.html`: márgenes de página
en `@page`, tamaños en `body`/`h1`/`h2`, y espaciado entre puestos en
`.entrada`. Los iconos SVG están en el macro `icono()` al principio del body;
para añadir una red nueva, añade su rama al macro y su nombre a la lista de
`icono_red()` en `generar_cv.py`.
