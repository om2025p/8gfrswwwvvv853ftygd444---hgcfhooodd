from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
    page = context.new_page()

    # 1. Verify Portal Icon
    portal_url = f"file://{os.path.abspath('index.html')}"
    page.goto(portal_url)
    page.wait_for_selector("#appGrid")

    screenshot_portal = "/home/jules/verification/portal_icon_verified.png"
    page.screenshot(path=screenshot_portal)

    # 2. Verify Family Tree Spacing
    family_url = f"file://{os.path.abspath('family/index.html')}"
    page.goto(family_url)
    page.wait_for_selector("#emptyState")

    page.click("text=ثبت جد بزرگ پدری")
    page.wait_for_selector("#focusOverlay.active")
    page.click("#btn-dialog-next")
    page.fill("#member-name", "امیر بزرگ رضایی")
    page.click("#btn-dialog-next")
    page.click("#btn-dialog-next")
    page.click("#btn-dialog-next")
    page.click("#btn-dialog-next")

    page.wait_for_timeout(300)

    screenshot_family = "/home/jules/verification/family_spaced_nodes.png"
    page.screenshot(path=screenshot_family)

    browser.close()
    print("Portal and Spacing screenshots saved.")
