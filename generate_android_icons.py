import os
import asyncio
from playwright.async_api import async_playwright

html_icon = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 0;
    width: 512px;
    height: 512px;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background Gradient -->
    <radialGradient id="bgGrad" cx="50%" cy="35%" r="70%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#020617"/>
    </radialGradient>

    <!-- Metallic Shield Gradient -->
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="30%" stop-color="#cbd5e1"/>
      <stop offset="70%" stop-color="#64748b"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>

    <!-- Golden Arrow Gradient -->
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fef08a"/>
      <stop offset="30%" stop-color="#facc15"/>
      <stop offset="70%" stop-color="#eab308"/>
      <stop offset="100%" stop-color="#ca8a04"/>
    </linearGradient>

    <!-- Neon Blue Energy Arc -->
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="50%" stop-color="#2563eb"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>

    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>

    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="14" flood-color="#000000" flood-opacity="0.65"/>
    </filter>
  </defs>

  <!-- Base Squircle -->
  <rect width="512" height="512" rx="120" fill="url(#bgGrad)"/>
  <rect width="502" height="504" x="5" y="4" rx="116" fill="none" stroke="url(#blueGrad)" stroke-width="6" opacity="0.8"/>

  <!-- Glowing Rim Light -->
  <circle cx="256" cy="256" r="210" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.3" filter="url(#glow)"/>

  <!-- 3D Metallic Outer Shield -->
  <g filter="url(#shadow)">
    <path d="M 256 70
             C 340 70, 400 95, 400 160
             C 400 280, 320 380, 256 440
             C 192 380, 112 280, 112 160
             C 112 95, 172 70, 256 70 Z"
          fill="url(#shieldGrad)"/>

    <path d="M 256 86
             C 328 86, 380 108, 380 165
             C 380 268, 308 358, 256 418
             C 204 358, 132 268, 132 165
             C 132 108, 184 86, 256 86 Z"
          fill="#0f172a"/>
  </g>

  <!-- Inner Blue Arc & Golden Download Arrow -->
  <g filter="url(#shadow)">
    <!-- Inner Blue Core -->
    <path d="M 256 102
             C 314 102, 360 120, 360 170
             C 360 255, 298 335, 256 392
             C 214 335, 152 255, 152 170
             C 152 120, 198 102, 256 102 Z"
          fill="url(#blueGrad)" opacity="0.35"/>

    <!-- Golden 3D Download Arrow -->
    <path d="M 216 130
             L 296 130
             L 296 220
             L 346 220
             L 256 320
             L 166 220
             L 216 220 Z"
          fill="url(#goldGrad)"
          stroke="#fef08a"
          stroke-width="3"
          filter="url(#glow)"/>

    <!-- Bottom Shield Tray Base -->
    <rect x="186" y="340" width="140" height="24" rx="12" fill="url(#goldGrad)" filter="url(#glow)"/>
  </g>
</svg>
</body>
</html>
'''

async def generate_icons():
    temp_html = "temp_android_icon.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_icon)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 512, "height": 512})
        await page.goto(f"file://{os.path.abspath(temp_html)}")

        icon_512 = "restricted/android/app/src/main/res/drawable/ic_app_launcher.png"
        os.makedirs(os.path.dirname(icon_512), exist_ok=True)
        await page.screenshot(path=icon_512, omit_background=True)

        # Generate Android mipmap sizes
        densities = {
            "mipmap-mdpi": 48,
            "mipmap-hdpi": 72,
            "mipmap-xhdpi": 96,
            "mipmap-xxhdpi": 144,
            "mipmap-xxxhdpi": 192,
        }

        for folder, size in densities.items():
            dir_path = f"restricted/android/app/src/main/res/{folder}"
            os.makedirs(dir_path, exist_ok=True)

            p_res = await browser.new_page(viewport={"width": size, "height": size})
            await p_res.goto(f"file://{os.path.abspath(temp_html)}")

            # Save square and round icons
            await p_res.screenshot(path=f"{dir_path}/ic_launcher.png", omit_background=True)
            await p_res.screenshot(path=f"{dir_path}/ic_launcher_round.png", omit_background=True)
            await p_res.close()

        await browser.close()

    if os.path.exists(temp_html):
        os.remove(temp_html)

    print("Android 3D Launcher icons generated successfully across all mipmap resolutions!")

if __name__ == "__main__":
    asyncio.run(generate_icons())
