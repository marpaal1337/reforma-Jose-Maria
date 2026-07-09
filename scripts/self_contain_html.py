#!/usr/bin/env python3
"""Make index.html and planos.html fully self-contained by inlining all external resources."""

import base64

CURRENT_DIR = "/home/mpalaciosa/dev/reforma-Jose-Maria"

def read_b64_font(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

INTER_B64 = read_b64_font("/tmp/Inter.woff2")
SS4_B64 = read_b64_font("/tmp/SourceSerif4.woff2")

FONT_CSS = f"""<style>
@font-face {{
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url(data:font/woff2;base64,{INTER_B64}) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
@font-face {{
  font-family: 'Source Serif 4';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url(data:font/woff2;base64,{SS4_B64}) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
</style>
"""

def make_index_self_contained():
    path = f"{CURRENT_DIR}/index.html"
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace Google Fonts link lines (7-9)
    old = '  <link rel="preconnect" href="https://fonts.googleapis.com">\n' \
          '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n' \
          '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap">'
    new = '  ' + FONT_CSS.strip()
    html = html.replace(old, new)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ {path} is now self-contained (fonts inlined)")

def make_planos_self_contained():
    path = f"{CURRENT_DIR}/planos.html"
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Replace Google Fonts link lines (7-9)
    old_fonts = '  <link rel="preconnect" href="https://fonts.googleapis.com">\n' \
                '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n' \
                '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap">'
    new_fonts = '  ' + FONT_CSS.strip()
    html = html.replace(old_fonts, new_fonts)

    # 2. Inline Leaflet CSS
    with open("/tmp/leaflet.css", 'r', encoding='utf-8') as f:
        leaflet_css = f.read()
    old_leaflet_css = '  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">\n' \
                      '  <style>'
    new_leaflet = f'  <style>\n{leaflet_css}\n</style>\n  <style>'
    html = html.replace(old_leaflet_css, new_leaflet)

    # 3. Inline Leaflet JS
    with open("/tmp/leaflet.js", 'r', encoding='utf-8') as f:
        leaflet_js = f.read()
    old_leaflet_js = '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n<script>'
    new_leaflet_js = f'<script>{leaflet_js}</script>\n<script>'
    html = html.replace(old_leaflet_js, new_leaflet_js)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ {path} is now self-contained (fonts + Leaflet inlined)")

if __name__ == '__main__':
    make_index_self_contained()
    make_planos_self_contained()
    print("Done!")
