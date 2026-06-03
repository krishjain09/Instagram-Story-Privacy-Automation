"""
Instagram "Hide Story From" Automation Script 
===========================================================================
Targets the REAL Instagram page as of 2026:
    URL  : https://www.instagram.com/accounts/hide_story_and_live_from/
"""

import asyncio
import getpass
import sys

from playwright.async_api import (
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

STORY_HIDE_URL = "https://www.instagram.com/accounts/hide_story_and_live_from/"
HEADLESS = False     

SCROLL_STEP_PX   = 600     
SCROLL_PAUSE_MS  = 1_800   
MAX_STABLE_TICKS = 3       
MAX_SCROLL_TICKS = 300     
MAX_CLICK_RETRY  = 3       

# ---------------------------------------------------------------------------
# BLOKS-ACCURATE SELECTORS
# ---------------------------------------------------------------------------

ROW_SELECTOR = 'div:has(> div > [aria-label="Toggle checkbox"])'
TOGGLE_SELECTOR = '[aria-label="Toggle checkbox"]'

# ---------------------------------------------------------------------------
# BROWSER SETUP
# ---------------------------------------------------------------------------

async def build_context(playwright: Playwright):
    browser = await playwright.chromium.launch(
        headless=HEADLESS,
        args=["--disable-blink-features=AutomationControlled"],
    )
    kwargs = dict(
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    context = await browser.new_context(**kwargs)
    page    = await context.new_page()
    return browser, context, page


# ---------------------------------------------------------------------------
# MANUAL GATE OVERRIDE LOGIN ROUTINE
# ---------------------------------------------------------------------------

async def login_via_terminal(page: Page) -> None:
    print("\n" + "=" * 50)
    print("  INSTAGRAM CREDENTIALS REQUIRED")
    print("=" * 50)
    
    username = await asyncio.to_thread(input, "Enter Instagram Username/Email: ")
    password = await asyncio.to_thread(getpass.getpass, "Enter Instagram Password (hidden): ")
    
    username = username.strip()
    if not username or not password:
        raise RuntimeError("Username and password cannot be empty.")

    print("\n[→] Opening Instagram Login window...")
    await page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
    
    print("[→] Locating login elements...")
    user_selector = 'input[name="username"], input[type="text"]'
    
    try:
        await page.wait_for_selector(user_selector, timeout=15000, state="visible")
    except PlaywrightTimeout:
        raise RuntimeError("Could not find the login inputs. Try running the script again.")
    
    print("[→] Typing username...")
    user_field = page.locator(user_selector).first
    await user_field.click()
    await page.keyboard.type(username, delay=120)
    await page.wait_for_timeout(500)
    
    print("[→] Typing password...")
    await page.keyboard.press("Tab")
    await page.wait_for_timeout(300)
    await page.keyboard.type(password, delay=120)
    await page.wait_for_timeout(500)
    
    print("[→] Submitting form...")
    await page.keyboard.press("Enter")
    
    # --- THE MANUAL OVERRIDE GATE ---
    print("\n" + "╔" + "═" * 58 + "╗")
    print("  ⚠️ ACTION REQUIRED IN THE BROWSER AND TERMINAL")
    print("  1. Go to the browser window.")
    print("  2. Complete all 'I am not a robot' / CAPTCHA image grids.")
    print("  3. Solve any 2FA security codes if asked.")
    print("  4. Wait until you are fully looking at your Home Feed page.")
    print("╚" + "═" * 58 + "╝")
    
    # This completely halts the code execution until you press Enter in the terminal!
    await asyncio.to_thread(input, "\n👉 Press [ENTER] here in the terminal ONLY AFTER you are completely logged in: ")
    
    print(f"\n[✓] Resuming script for @{username}...")
    print("[→] Giving the session 3 seconds to fully settle...")
    await page.wait_for_timeout(3000)

    # Clean up common post-login pop-up speedbumps
    for target in ["Not Now", "Cancel"]:
        try:
            await page.locator(f"button:has-text('{target}')").first.click(timeout=2000)
        except PlaywrightTimeout:
            pass


# ---------------------------------------------------------------------------
# SCROLL — lazy-load elements
# ---------------------------------------------------------------------------

async def scroll_until_stable(page: Page) -> int:
    print("[→] Scrolling to load all followers …")

    previous = 0
    stable   = 0
    ticks    = 0

    while stable < MAX_STABLE_TICKS and ticks < MAX_SCROLL_TICKS:
        current = await page.locator(ROW_SELECTOR).count()

        if current > previous:
            print(f"    Found {current} user rows loaded …", end="\r")
            previous = current
            stable   = 0
        else:
            stable += 1

        await page.evaluate(
            """(step) => {
                const selectors = [
                    'main [style*=\"overflow-y: auto\"]',
                    'main [style*=\"overflow: auto\"]',
                    'main [style*=\"overflow-y:auto\"]',
                    '[role=\"main\"] > div',
                    'main',
                ];
                for (const s of selectors) {
                    const el = document.querySelector(s);
                    if (el && el.scrollHeight > el.clientHeight) {
                        el.scrollTop += step;
                        return;
                    }
                }
                window.scrollBy(0, step);
            }""",
            SCROLL_STEP_PX,
        )

        await page.wait_for_timeout(SCROLL_PAUSE_MS)
        ticks += 1

    final = await page.locator(ROW_SELECTOR).count()
    print(f"\n[✓] Scrolling completed — {final} rows parsed.")
    return final


# ---------------------------------------------------------------------------
# BLOKS TOGGLE STATE CHECK
# ---------------------------------------------------------------------------

async def is_toggled_on(toggle_el) -> bool:
    try:
        html = await toggle_el.evaluate("(e) => e.outerHTML")
        return "circle-check__filled" in html
    except:
        return False


async def click_toggle(page: Page, toggle_el) -> bool:
    for attempt in range(1, MAX_CLICK_RETRY + 1):
        try:
            await toggle_el.scroll_into_view_if_needed()
            await toggle_el.click(timeout=5000, force=True)
            return True
        except Exception as exc:
            if attempt < MAX_CLICK_RETRY:
                await page.wait_for_timeout(400 * attempt)
            else:
                print(f"\n    [!] Toggle click failed ({exc})")
                return False
    return False


# ---------------------------------------------------------------------------
# CORE PROCESSOR
# ---------------------------------------------------------------------------

async def process_all(page: Page, want_on: bool) -> None:
    total = await scroll_until_stable(page)

    if total == 0:
        print("\n[✗] 0 valid rows found matching structural components.")
        return

    action = "Hiding from" if want_on else "Unhiding from"
    print(f"\n[→] {action} — processing {total} items …\n")

    changed = skipped = failed = 0

    for i in range(total):
        row = page.locator(ROW_SELECTOR).nth(i)
        toggle = row.locator(TOGGLE_SELECTOR).first
        
        try:
            username = await row.locator('span[data-bloks-name="bk.components.Text"]').first.text_content(timeout=1000)
            username = username.strip()
        except Exception:
            try:
                username = await row.locator('span').first.text_content(timeout=1000)
                username = username.strip().split('\n')[0]
            except Exception:
                username = f"User_Index_{i}"

        current = await is_toggled_on(toggle)

        if current == want_on:
            skipped += 1
        else:
            print(f"  [→] Updating: {username} ...")
            ok = await click_toggle(page, toggle)
            if ok:
                changed += 1
                await page.wait_for_timeout(500)  
            else:
                failed += 1

    print("\n" + "─" * 52)
    print(f"  ✓ Total Actions Run : {changed}")
    print(f"  – Skipped (Correct) : {skipped}")
    print(f"  ✗ Action Failures   : {failed}")
    print("─" * 52)


# ---------------------------------------------------------------------------
# MAIN WORKFLOWS
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=" * 55)
    print("  Instagram Story Privacy Automation ")
    print("=" * 55)

    async with async_playwright() as pw:
        browser, context, page = await build_context(pw)
        try:
            await login_via_terminal(page)

            print(f"\n[→] Navigating to target: {STORY_HIDE_URL} …")
            await page.goto(STORY_HIDE_URL, wait_until="domcontentloaded")
            print("Waiting for Bloks structural UI...")
            await page.wait_for_timeout(6000)

            print("\nSelect Process Mode:")
            print("  [1] Hide story from ALL users")
            print("  [2] Unhide story for ALL users")
            print("  [q] Quit")
            
            choice = await asyncio.to_thread(input, "\nEnter choice: ")
            choice = choice.strip().lower()

            if choice == "1":
                await process_all(page, want_on=True)
            elif choice == "2":
                await process_all(page, want_on=False)
            else:
                print("Exiting script.")

        except RuntimeError as err:
            print(f"\n[ERROR] {err}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user.")
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())