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
    <radialGradient id="bgGrad" cx="50%" cy="35%" r="75%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#020617"/>
    </radialGradient>

    <!-- Metallic Shield Gradient -->
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="35%" stop-color="#cbd5e1"/>
      <stop offset="70%" stop-color="#64748b"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>

    <!-- Golden Download Arrow Gradient -->
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="20%" stop-color="#fef08a"/>
      <stop offset="50%" stop-color="#facc15"/>
      <stop offset="80%" stop-color="#eab308"/>
      <stop offset="100%" stop-color="#ca8a04"/>
    </linearGradient>

    <!-- Neon Blue Energy Arc -->
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="50%" stop-color="#2563eb"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>

    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="10" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>

    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="#000000" flood-opacity="0.7"/>
    </filter>
  </defs>

  <!-- Base Rounded Squircle -->
  <rect width="512" height="512" rx="120" fill="url(#bgGrad)"/>
  <rect width="502" height="504" x="5" y="4" rx="116" fill="none" stroke="url(#blueGrad)" stroke-width="8" opacity="0.85"/>

  <!-- Glowing Rim Light -->
  <circle cx="256" cy="256" r="215" fill="none" stroke="#38bdf8" stroke-width="3" opacity="0.35" filter="url(#glow)"/>

  <!-- 3D Metallic Outer Shield Frame -->
  <g filter="url(#shadow)">
    <path d="M 256 60
             C 345 60, 410 88, 410 155
             C 410 285, 325 390, 256 450
             C 187 390, 102 285, 102 155
             C 102 88, 167 60, 256 60 Z"
          fill="url(#shieldGrad)"/>

    <path d="M 256 78
             C 332 78, 388 102, 388 160
             C 388 272, 312 368, 256 426
             C 200 368, 124 272, 124 160
             C 124 102, 180 78, 256 78 Z"
          fill="#0f172a"/>
  </g>

  <!-- PROMINENT 3D DOWNLOAD SYMBOL -->
  <g filter="url(#shadow)">
    <!-- Inner Blue Glowing Shield Core -->
    <path d="M 256 96
             C 318 96, 366 116, 366 165
             C 366 258, 298 345, 256 400
             C 214 345, 146 258, 146 165
             C 146 116, 194 96, 256 96 Z"
          fill="url(#blueGrad)" opacity="0.4"/>

    <!-- Large Bold 3D Golden Download Arrow (نماد دانلود برجسته) -->
    <path d="M 206 115
             L 306 115
             L 306 215
             L 366 215
             L 256 335
             L 146 215
             L 206 215 Z"
          fill="url(#goldGrad)"
          stroke="#ffffff"
          stroke-width="4"
          filter="url(#glow)"/>

    <!-- 3D Download Tray / Base Bracket -->
    <path d="M 156 330
             L 156 375
             C 156 385, 166 395, 176 395
             L 336 395
             C 346 395, 356 385, 356 375
             L 356 330"
          fill="none"
          stroke="url(#goldGrad)"
          stroke-width="22"
          stroke-linecap="round"
          stroke-linejoin="round"
          filter="url(#glow)"/>
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

            await p_res.screenshot(path=f"{dir_path}/ic_launcher.png", omit_background=True)
            await p_res.screenshot(path=f"{dir_path}/ic_launcher_round.png", omit_background=True)
            await p_res.close()

        await browser.close()

    if os.path.exists(temp_html):
        os.remove(temp_html)

    print("Prominent Download Symbol 3D Launcher Icons generated successfully across all mipmaps!")

if __name__ == "__main__":
    asyncio.run(generate_icons())
