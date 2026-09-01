import os
from playwright.sync_api import sync_playwright

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Filter for soft 3D drop shadow -->
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#021024" flood-opacity="0.5"/>
    </filter>

    <filter id="embossGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>

    <!-- Deep Modern Blue & Cyan Gradient Background -->
    <linearGradient id="bgBlue" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7" />
      <stop offset="50%" stop-color="#0284c7" />
      <stop offset="100%" stop-color="#0f172a" />
    </linearGradient>

    <!-- Inner Metallic Glow Gradient for Glass Border -->
    <linearGradient id="cyanGlass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.3"/>
    </linearGradient>

    <!-- 3D White Text Front Gradient -->
    <linearGradient id="white3dGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="70%" stop-color="#e2e8f0" />
      <stop offset="100%" stop-color="#cbd5e1" />
    </linearGradient>

    <!-- Deep Blue 3D Extrusion Edge Gradient -->
    <linearGradient id="blueEdgeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0369a1" />
      <stop offset="100%" stop-color="#0c4a6e" />
    </linearGradient>
  </defs>

  <!-- Background rounded box with smooth soft edges -->
  <rect width="512" height="512" rx="110" fill="url(#bgBlue)" />

  <!-- Soft Cyan Glass Border -->
  <rect width="496" height="496" x="8" y="8" rx="102" fill="none" stroke="url(#cyanGlass)" stroke-width="6" opacity="0.9" />

  <!-- Globe & Network Subtle Background Motif -->
  <g opacity="0.15" stroke="#ffffff" stroke-width="3" fill="none">
    <circle cx="256" cy="256" r="180"/>
    <ellipse cx="256" cy="256" rx="180" ry="70"/>
    <ellipse cx="256" cy="256" rx="70" ry="180"/>
    <line x1="76" y1="256" x2="436" y2="256"/>
  </g>

  <!-- 3D Soft Embossed Bold White Text "WWW.com" -->
  <g font-family="Segoe UI, Arial Black, Impact, sans-serif" font-weight="900" text-anchor="middle" dominant-baseline="central" filter="url(#softShadow)">

    <!-- 3D Extrusion Stack for Depth (Soft 3D Edges) -->
    <text x="256" y="278" font-size="82" fill="#032b45" stroke="#032b45" stroke-width="18" stroke-linejoin="round">WWW.com</text>
    <text x="256" y="274" font-size="82" fill="#0369a1" stroke="#0369a1" stroke-width="16" stroke-linejoin="round">WWW.com</text>
    <text x="256" y="270" font-size="82" fill="#0284c7" stroke="#0284c7" stroke-width="14" stroke-linejoin="round">WWW.com</text>
    <text x="256" y="266" font-size="82" fill="#38bdf8" stroke="#38bdf8" stroke-width="10" stroke-linejoin="round">WWW.com</text>

    <!-- White Soft Outline -->
    <text x="256" y="256" font-size="82" fill="none" stroke="#ffffff" stroke-width="6" stroke-linejoin="round">WWW.com</text>

    <!-- Front Face -->
    <text x="256" y="256" font-size="82" fill="url(#white3dGrad)">WWW.com</text>

    <!-- Top Reflective Bevel Specular Line -->
    <text x="256" y="253" font-size="82" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.9">WWW.com</text>
  </g>
</svg>
'''

os.makedirs("funds", exist_ok=True)
with open("funds/icon.svg", "w") as f:
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
    svg_el.screenshot(path="funds/icon-512.png", omit_background=True)
    svg_el.screenshot(path="funds/icon-512-maskable.png", omit_background=True)

    page.set_viewport_size({"width": 192, "height": 192})
    svg_el.screenshot(path="funds/icon-192.png", omit_background=True)
    svg_el.screenshot(path="funds/icon-192-maskable.png", omit_background=True)

    page.set_viewport_size({"width": 180, "height": 180})
    svg_el.screenshot(path="funds/apple-touch-icon.png", omit_background=True)

    page.set_viewport_size({"width": 64, "height": 64})
    svg_el.screenshot(path="funds/favicon.png", omit_background=True)

    browser.close()

# Copy favicon.png to favicon.ico
with open("funds/favicon.png", "rb") as f_in:
    with open("funds/favicon.ico", "wb") as f_out:
        f_out.write(f_in.read())

print("Funds 3D icons generated successfully!")
