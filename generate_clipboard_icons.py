import os
from playwright.sync_api import sync_playwright

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="50%" stop-color="#1e293b" />
      <stop offset="100%" stop-color="#0f172a" />
    </linearGradient>

    <!-- Outer Ring Gradient -->
    <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="50%" stop-color="#818cf8" />
      <stop offset="100%" stop-color="#c084fc" />
    </linearGradient>

    <!-- Clipboard Board Gradient -->
    <linearGradient id="boardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#334155" />
      <stop offset="100%" stop-color="#1e293b" />
    </linearGradient>

    <!-- Paper Sheet Gradient -->
    <linearGradient id="paperGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="100%" stop-color="#f1f5f9" />
    </linearGradient>

    <!-- Metallic Clip Gradient -->
    <linearGradient id="clipGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#cbd5e1" />
      <stop offset="50%" stop-color="#94a3b8" />
      <stop offset="100%" stop-color="#64748b" />
    </linearGradient>

    <!-- Cyan Accent Line Gradient -->
    <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="100%" stop-color="#3b82f6" />
    </linearGradient>

    <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="16" stdDeviation="12" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
  </defs>

  <!-- Container Base -->
  <rect width="512" height="512" rx="110" fill="url(#bgGrad)" />
  <rect width="496" height="496" x="8" y="8" rx="102" fill="none" stroke="url(#borderGrad)" stroke-width="8" opacity="0.9" />

  <!-- Main Board with Drop Shadow -->
  <g filter="url(#dropShadow)">
    <rect x="116" y="90" width="280" height="360" rx="28" fill="url(#boardGrad)" stroke="#475569" stroke-width="4" />

    <!-- Paper Sheet -->
    <rect x="136" y="130" width="240" height="300" rx="16" fill="url(#paperGrad)" />

    <!-- Text Lines on Paper -->
    <rect x="166" y="180" width="180" height="18" rx="9" fill="url(#lineGrad)" />
    <rect x="166" y="218" width="140" height="14" rx="7" fill="#94a3b8" />
    <rect x="166" y="250" width="160" height="14" rx="7" fill="#cbd5e1" />

    <!-- Folder Badge Symbol on Paper -->
    <rect x="166" y="290" width="180" height="110" rx="14" fill="#e2e8f0" />
    <rect x="180" y="310" width="100" height="14" rx="7" fill="#0284c7" />
    <rect x="180" y="338" width="140" height="10" rx="5" fill="#64748b" />
    <rect x="180" y="360" width="120" height="10" rx="5" fill="#94a3b8" />
    <rect x="180" y="382" width="80" height="10" rx="5" fill="#38bdf8" />

    <!-- Metallic Clip Holder -->
    <rect x="206" y="66" width="100" height="44" rx="12" fill="url(#clipGrad)" stroke="#f8fafc" stroke-width="2" />
    <circle cx="256" cy="88" r="12" fill="#0f172a" />
    <circle cx="256" cy="88" r="6" fill="#38bdf8" />
  </g>
</svg>
'''

os.makedirs("clipboard", exist_ok=True)
with open("clipboard/icon.svg", "w") as f:
    f.write(svg_content.strip())

html_content = f'''
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ margin: 0; padding: 0; background: transparent; display: flex; justify-content: center; align-items: center; }}
    svg {{ display: block; width: 100%; height: 100%; }}
  </style>
</head>
<body>
  {svg_content}
</body>
</html>
'''

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html_content)

    page.set_viewport_size({"width": 512, "height": 512})
    svg_el = page.query_selector("svg")
    svg_el.screenshot(path="clipboard/icon-512.png", omit_background=True)
    svg_el.screenshot(path="clipboard/icon-512-maskable.png", omit_background=True)

    page.set_viewport_size({"width": 192, "height": 192})
    svg_el.screenshot(path="clipboard/icon-192.png", omit_background=True)
    svg_el.screenshot(path="clipboard/icon-192-maskable.png", omit_background=True)

    page.set_viewport_size({"width": 180, "height": 180})
    svg_el.screenshot(path="clipboard/apple-touch-icon.png", omit_background=True)

    page.set_viewport_size({"width": 64, "height": 64})
    svg_el.screenshot(path="clipboard/favicon.png", omit_background=True)

    browser.close()

# Copy favicon.png to favicon.ico
with open("clipboard/favicon.png", "rb") as f_in:
    with open("clipboard/favicon.ico", "wb") as f_out:
        f_out.write(f_in.read())

print("Clipboard App 3D Android icons generated successfully!")
