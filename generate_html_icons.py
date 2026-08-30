import os
from playwright.sync_api import sync_playwright

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background shadow filter -->
    <filter id="shadow3d" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity="0.25"/>
    </filter>
    <!-- Gradient for 3D blue text -->
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#2563eb" />
      <stop offset="50%" stop-color="#1d4ed8" />
      <stop offset="100%" stop-color="#1e3a8a" />
    </linearGradient>
  </defs>

  <!-- White Background with rounded corners -->
  <rect width="512" height="512" rx="110" fill="#ffffff" />
  <rect width="500" height="500" x="6" y="6" rx="104" fill="none" stroke="#e5e7eb" stroke-width="4" />

  <!-- 3D Layer Effects & Red Outlines -->
  <g font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="130" text-anchor="middle" dominant-baseline="central">
    <!-- 3D Extrusion Shadows (Red & Dark Red Layering) -->
    <text x="256" y="274" fill="#7f1d1d" stroke="#b91c1c" stroke-width="24" stroke-linejoin="round">HTML</text>
    <text x="256" y="270" fill="#991b1b" stroke="#dc2626" stroke-width="24" stroke-linejoin="round">HTML</text>
    <text x="256" y="266" fill="#b91c1c" stroke="#ef4444" stroke-width="22" stroke-linejoin="round">HTML</text>
    <text x="256" y="262" fill="#dc2626" stroke="#f87171" stroke-width="20" stroke-linejoin="round">HTML</text>

    <!-- Main Outer Red Border Edge -->
    <text x="256" y="256" fill="#dc2626" stroke="#ef4444" stroke-width="18" stroke-linejoin="round">HTML</text>

    <!-- Inner White highlight stroke between red border & blue core -->
    <text x="256" y="256" fill="none" stroke="#ffffff" stroke-width="8" stroke-linejoin="round">HTML</text>

    <!-- Blue 3D Core Front Layer -->
    <text x="256" y="256" fill="url(#blueGrad)">HTML</text>

    <!-- Top Bevel Highlight for 3D Embossed Effect -->
    <text x="256" y="253" fill="none" stroke="#60a5fa" stroke-width="2" opacity="0.8">HTML</text>
  </g>
</svg>
'''

os.makedirs("html-viewer", exist_ok=True)
with open("html-viewer/icon.svg", "w") as f:
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
    svg_el.screenshot(path="html-viewer/icon-512.png", omit_background=True)
    svg_el.screenshot(path="html-viewer/icon-512-maskable.png", omit_background=True)

    page.set_viewport_size({"width": 192, "height": 192})
    svg_el.screenshot(path="html-viewer/icon-192.png", omit_background=True)
    svg_el.screenshot(path="html-viewer/icon-192-maskable.png", omit_background=True)

    page.set_viewport_size({"width": 180, "height": 180})
    svg_el.screenshot(path="html-viewer/apple-touch-icon.png", omit_background=True)

    page.set_viewport_size({"width": 64, "height": 64})
    svg_el.screenshot(path="html-viewer/favicon.png", omit_background=True)

    browser.close()

# Copy favicon.png to favicon.ico
with open("html-viewer/favicon.png", "rb") as f_in:
    with open("html-viewer/favicon.ico", "wb") as f_out:
        f_out.write(f_in.read())

print("HTML Viewer icons rendered successfully!")
