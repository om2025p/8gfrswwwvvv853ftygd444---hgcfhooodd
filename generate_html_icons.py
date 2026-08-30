import os
from playwright.sync_api import sync_playwright

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background shadow filter -->
    <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="10" flood-color="#000000" flood-opacity="0.3"/>
    </filter>

    <!-- Gradient for 3D blue text -->
    <linearGradient id="blue3d" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" />
      <stop offset="40%" stop-color="#1d4ed8" />
      <stop offset="100%" stop-color="#1e3a8a" />
    </linearGradient>

    <!-- Metallic Red stroke gradient for 3D edges -->
    <linearGradient id="red3d" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ef4444" />
      <stop offset="50%" stop-color="#dc2626" />
      <stop offset="100%" stop-color="#991b1b" />
    </linearGradient>

    <!-- Subtle background card gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="100%" stop-color="#f8fafc" />
    </linearGradient>
  </defs>

  <!-- Solid White Container Box with Rounded Corner and Dark Red/Blue Double Border -->
  <rect width="512" height="512" rx="110" fill="url(#bgGrad)" />
  <rect width="496" height="496" x="8" y="8" rx="102" fill="none" stroke="#dc2626" stroke-width="12" />
  <rect width="476" height="476" x="18" y="18" rx="92" fill="none" stroke="#2563eb" stroke-width="6" opacity="0.8" />

  <!-- Large 3D Embossed Bold Uppercase "HTML" Text fitted perfectly -->
  <g font-family="Arial Black, Impact, Arial, sans-serif" font-weight="900" font-size="150" text-anchor="middle" dominant-baseline="central">

    <!-- 3D Extrusion Layers (Dark Red Deep 3D Shadow Stack) -->
    <text x="256" y="280" fill="#450a0a" stroke="#450a0a" stroke-width="26" stroke-linejoin="round">HTML</text>
    <text x="256" y="276" fill="#7f1d1d" stroke="#7f1d1d" stroke-width="26" stroke-linejoin="round">HTML</text>
    <text x="256" y="272" fill="#991b1b" stroke="#991b1b" stroke-width="24" stroke-linejoin="round">HTML</text>
    <text x="256" y="268" fill="#b91c1c" stroke="#b91c1c" stroke-width="22" stroke-linejoin="round">HTML</text>
    <text x="256" y="264" fill="#dc2626" stroke="#dc2626" stroke-width="20" stroke-linejoin="round">HTML</text>

    <!-- Bright Red 3D Outer Edge Border -->
    <text x="256" y="256" fill="#ef4444" stroke="url(#red3d)" stroke-width="18" stroke-linejoin="round">HTML</text>

    <!-- Sharp White Isolation Outline between Red Edge and Blue Front -->
    <text x="256" y="256" fill="none" stroke="#ffffff" stroke-width="8" stroke-linejoin="round">HTML</text>

    <!-- Main Front 3D Blue Face -->
    <text x="256" y="256" fill="url(#blue3d)">HTML</text>

    <!-- Top Bevel Light Reflective Line -->
    <text x="256" y="253" fill="none" stroke="#93c5fd" stroke-width="2" opacity="0.9">HTML</text>
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

print("HTML Viewer high-contrast fitted 3D icons rendered successfully!")
