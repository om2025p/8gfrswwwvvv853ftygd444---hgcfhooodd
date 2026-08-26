import subprocess
import os

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#388E3C" />
      <stop offset="100%" stop-color="#1B5E20" />
    </radialGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFE082" />
      <stop offset="50%" stop-color="#FFD54F" />
      <stop offset="100%" stop-color="#FFB300" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.35"/>
    </filter>
  </defs>

  <!-- Background rounded box -->
  <rect width="512" height="512" rx="110" fill="url(#bgGlow)" />

  <!-- Outer Gold Decorative Ring -->
  <circle cx="256" cy="256" r="230" fill="none" stroke="url(#goldGrad)" stroke-width="6" stroke-dasharray="16 8" opacity="0.4" />
  <circle cx="256" cy="256" r="218" fill="none" stroke="#FFFFFF" stroke-width="2" opacity="0.2" />

  <!-- Crown on Top -->
  <path d="M 216 110 L 236 130 L 256 95 L 276 130 L 296 110 L 290 145 L 222 145 Z" fill="url(#goldGrad)" filter="url(#shadow)" />

  <!-- Tree Trunk & Base Roots -->
  <g filter="url(#shadow)">
    <!-- Main Roots -->
    <path d="M 256 340 Q 230 400 170 420 M 256 340 Q 282 400 342 420 M 256 360 L 256 430" stroke="url(#goldGrad)" stroke-width="14" stroke-linecap="round" fill="none" />

    <!-- Trunk -->
    <path d="M 236 370 C 236 300 216 260 170 210 M 276 370 C 276 300 296 260 342 210 M 256 370 L 256 190" stroke="url(#goldGrad)" stroke-width="18" stroke-linecap="round" fill="none" />
  </g>

  <!-- Golden Family Connection Nodes (Leaves & Cards) -->
  <g filter="url(#shadow)">
    <!-- Top Central Ancestor Node -->
    <circle cx="256" cy="180" r="28" fill="url(#goldGrad)" stroke="#FFFFFF" stroke-width="4" />
    <circle cx="256" cy="180" r="14" fill="#1B5E20" />

    <!-- Sub Nodes Left & Right (Parents) -->
    <circle cx="170" cy="220" r="24" fill="url(#goldGrad)" stroke="#FFFFFF" stroke-width="4" />
    <circle cx="342" cy="220" r="24" fill="url(#goldGrad)" stroke="#FFFFFF" stroke-width="4" />

    <!-- Branches to Children -->
    <path d="M 170 244 L 130 310 M 170 244 L 200 310 M 342 244 L 312 310 M 342 244 L 382 310" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" fill="none" opacity="0.8" />

    <!-- Children Generation Nodes -->
    <circle cx="130" cy="315" r="18" fill="#E8F5E9" stroke="url(#goldGrad)" stroke-width="4" />
    <circle cx="200" cy="315" r="18" fill="#E8F5E9" stroke="url(#goldGrad)" stroke-width="4" />
    <circle cx="312" cy="315" r="18" fill="#E8F5E9" stroke="url(#goldGrad)" stroke-width="4" />
    <circle cx="382" cy="315" r="18" fill="#E8F5E9" stroke="url(#goldGrad)" stroke-width="4" />
  </g>

  <!-- Glowing Emerald Leaves -->
  <g fill="#A5D6A7" opacity="0.9">
    <path d="M 256 140 C 245 125 256 110 256 110 C 256 110 267 125 256 140 Z" />
    <path d="M 145 195 C 130 190 135 175 135 175 C 135 175 150 180 145 195 Z" />
    <path d="M 367 195 C 382 190 377 175 377 175 C 377 175 362 180 367 195 Z" />
  </g>
</svg>
'''

with open("family/tree_icon.svg", "w") as f:
    f.write(svg_content)

print("SVG written successfully.")
