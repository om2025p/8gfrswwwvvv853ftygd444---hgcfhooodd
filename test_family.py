import os
from playwright.sync_api import sync_playwright

def run_automated_family_tree_tests():
    print("🚀 استارت اسکریپت تست خودکار شجره‌نامه عمارت دیجیتال...")

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()

        # Navigate to our family tree page
        filepath = os.path.abspath("family/index.html")
        page.goto(f"file://{filepath}")

        # 1. Verify Empty State is visible
        print("🔍 تایید وجود صفحه خالی شروع کار (Empty State)...")
        assert page.locator("text=از اینجا شروع کنید").is_visible()
        page.screenshot(path="family_test_empty_state.png")
        print("✅ صفحه خالی با موفقیت ثبت و تایید شد.")

        # 2. Click Add First Ancestor
        print("🌱 کلیک روی دکمه ثبت اولین جد و شروع فازهای ثبت...")
        page.click("text=ثبت اولین جد")
        page.wait_for_timeout(300)

        # Phase 1: Set male
        page.click("#gender-male")
        page.click("text=بعدی")
        page.wait_for_timeout(200)

        # Phase 2: Enter Core Details
        print("📝 وارد کردن نام خانوادگی جد بزرگ...")
        page.fill("#member-name", "امیر رضایی")
        page.fill("#member-job", "بنیان‌گذار عمارت")
        page.fill("#member-relation", "جد بزرگ پدری")
        page.fill("#member-birthplace", "اصفهان")
        page.click("text=بعدی")
        page.wait_for_timeout(200)

        # Phase 3: Life details
        page.click("text=بعدی")
        page.wait_for_timeout(200)

        # Phase 4: Marital details
        page.click("#marital-married")
        page.fill("#member-spouses-count", "1")
        page.fill("#member-children-count", "2")
        page.click("text=بعدی")
        page.wait_for_timeout(200)

        # Phase 5: Bio and submit
        page.fill("#member-bio", "جد بزرگ خاندان رضایی در عمارت دیجیتال")
        print("💾 ثبت نهایی اطلاعات جد بزرگ...")
        page.click("text=ثبت نهایی")
        page.wait_for_timeout(500)

        # Take a screenshot after adding the ancestor
        page.screenshot(path="family_test_ancestor_added.png")
        print("✅ جد بزرگ با موفقیت ثبت شد.")

        # 3. Check for chain focus spotlight nodes
        print("🎯 تایید وجود افکت کادرهای موقت چشمک‌زن فرزندان...")
        # Since 2 children were specified, child placeholder nodes are rendered
        assert page.locator("text=فرزند 1").is_visible()
        assert page.locator("text=فرزند 2").is_visible()
        print("✅ تایید وجود کادرهای موقت فرزند ۱ و فرزند ۲ بر روی بوم!")

        # 4. Try adding Child 1 to verify automatic family name inheritance
        print("👶 کلیک روی کادر موقت فرزند ۱ جهت تست ارث‌بری خودکار فامیلی (با فورس به دلیل انیمیشن چشمک‌زن)...")
        page.click("text=فرزند 1", force=True)
        page.wait_for_timeout(300)

        # Transition to Phase 2 to verify input field already has inherited 'رضایی'
        page.click("text=بعدی")
        page.wait_for_timeout(200)

        inherited_name = page.input_value("#member-name")
        print(f"🧬 فامیلی ارث‌بری شده در کادر نام فرزند: '{inherited_name}'")
        assert "رضایی" in inherited_name, "ارث‌بری هوشمند نام خانوادگی با خطا مواجه شد!"
        print("✅ سیستم ارث‌بری هوشمند نام خانوادگی با موفقیت تایید شد!")

        page.screenshot(path="family_test_child_inheritance.png")

        browser.close()
        print("🎉 تمام تست‌های خودکار شجره‌نامه عمارت با موفقیت و امتیاز ۱۰۰٪ پاس شدند! دمت گرم رئیس! 🏆💚")

if __name__ == "__main__":
    run_automated_family_tree_tests()
