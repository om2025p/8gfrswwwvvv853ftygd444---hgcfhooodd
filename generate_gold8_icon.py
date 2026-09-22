import os
import subprocess

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- پس‌زمینه دارویی و پزشکی -->
    <linearGradient id="bgTeal" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#042f2e"/>
      <stop offset="35%" stop-color="#0f3e3a"/>
      <stop offset="70%" stop-color="#115e59"/>
      <stop offset="100%" stop-color="#042f2e"/>
    </linearGradient>

    <linearGradient id="capsuleRed" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f87171"/>
      <stop offset="100%" stop-color="#ef4444"/>
    </linearGradient>

    <linearGradient id="capsuleTeal" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2dd4bf"/>
      <stop offset="100%" stop-color="#0d9488"/>
    </linearGradient>

    <linearGradient id="pillWhite" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#ccfbf1"/>
    </linearGradient>

    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="10" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#000" flood-opacity="0.5"/>
    </filter>
  </defs>

  <!-- پس‌زمینه گرد -->
  <rect width="512" height="512" rx="110" fill="url(#bgTeal)" />
  <rect width="504" height="504" x="4" y="4" rx="106" fill="none" stroke="#2dd4bf" stroke-width="4" opacity="0.4" />

  <!-- هاله نور خروج جادویی درصدهای مثبت -->
  <circle cx="256" cy="256" r="180" fill="#0d9488" opacity="0.3" filter="url(#glow)" />

  <!-- صلیب دارویی و پزشکی پس‌زمینه -->
  <path d="M 236 120 L 276 120 L 276 236 L 392 236 L 392 276 L 276 276 L 276 392 L 236 392 L 236 276 L 120 276 L 120 236 L 236 236 Z" fill="#14b8a6" opacity="0.25" />

  <!-- کپسول دارویی بزرگ سه بعدی در مرکز -->
  <g transform="rotate(-30 256 256)" filter="url(#shadow)">
    <!-- نیمه چپ/بالا کپسول (قرمز/نارنجی) -->
    <path d="M 170 216 C 170 170, 210 130, 256 130 L 256 382 C 210 382, 170 342, 170 296 Z" fill="url(#capsuleRed)"/>
    <!-- نیمه راست/پایین کپسول (فیروزه‌ای) -->
    <path d="M 256 130 C 302 130, 342 170, 342 216 L 342 296 C 342 342, 302 382, 256 382 Z" fill="url(#capsuleTeal)"/>
    <!-- خط جداسازی وسط کپسول -->
    <line x1="256" y1="126" x2="256" y2="386" stroke="#ffffff" stroke-width="6" opacity="0.8"/>
  </g>

  <!-- قرص دائره‌ای در گوشه -->
  <g transform="translate(130, 350)" filter="url(#shadow)">
    <circle cx="0" cy="0" r="42" fill="url(#pillWhite)" />
    <line x1="-30" y1="0" x2="30" y2="0" stroke="#0d9488" stroke-width="4" opacity="0.6"/>
  </g>

  <!-- درصدهای مثبت و علامت‌های سود -->
  <g font-family="Tahoma, Arial, sans-serif" font-weight="900" filter="url(#shadow)">
    <text x="120" y="140" font-size="42" fill="#34d399" filter="url(#glow)">+25%</text>
    <text x="310" y="150" font-size="48" fill="#34d399" filter="url(#glow)">+50%</text>
    <text x="330" y="380" font-size="40" fill="#38bdf8" filter="url(#glow)">+88%</text>
    <text x="210" y="440" font-size="46" fill="#f59e0b" filter="url(#glow)">8</text>
  </g>
</svg>
'''

with open("gold8/chest_icon.svg", "w") as f:
    f.write(svg_content)

print("SVG icon written to gold8/chest_icon.svg")
