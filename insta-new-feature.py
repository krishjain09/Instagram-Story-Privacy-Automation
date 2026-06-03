"""
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

SCROLL_PAUSE_MS  = 1000    # Time to wait after snapping for DOM elements to load
MAX_EMPTY_SCROLLS = 6      # Stops execution once the end of the list is reached

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
    
    print("\n" + "╔" + "═" * 58 + "╗")
    print("  ⚠️ ACTION REQUIRED IN THE BROWSER AND TERMINAL")
    print("  1. Go to the browser window.")
    print("  2. Complete all 'I am not a robot' / CAPTCHA image grids.")
    print("  3. Solve any 2FA security codes if asked.")
    print("  4. Wait until you are fully looking at your Home Feed page.")
    print("╚" + "═" * 58 + "╝")
    
    await asyncio.to_thread(input, "\n👉 Press [ENTER] here in the terminal ONLY AFTER you are completely logged in: ")
    
    print(f"\n[✓] Resuming script for @{username}...")
    print("[→] Giving the session 3 seconds to fully settle...")
    await page.wait_for_timeout(3000)

    for target in ["Not Now", "Cancel"]:
        try:
            await page.locator(f"button:has-text('{target}')").first.click(timeout=2000)
        except PlaywrightTimeout:
            pass


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
    try:
        await toggle_el.scroll_into_view_if_needed()
        await toggle_el.click(timeout=3000, force=True)
        return True
    except Exception as exc:
        print(f"\n    [!] Click failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# CORE STREAM PROCESSOR (ELEMENT-SNAPPING HIGH-VIS ENGINE)
# ---------------------------------------------------------------------------

async def stream_process_all(page: Page, want_on: bool) -> None:
    target_state_label = "Hidden" if want_on else "Visible"
    action_verb = "Hiding From" if want_on else "Unhiding From"
    
    print(f"\n[→] Launching Core Engine: Preparing to mass-set users to {target_state_label}...")
    print("-" * 65)

    processed_usernames = set()
    changed = skipped = failed = empty_scroll_ticks = loop_index = 0

    while empty_scroll_ticks < MAX_EMPTY_SCROLLS:
        current_visible_count = await page.locator(ROW_SELECTOR).count()
        new_users_found_in_this_pass = False
        last_row_element = None

        for i in range(current_visible_count):
            row = page.locator(ROW_SELECTOR).nth(i)
            last_row_element = row  
            
            try:
                username = await row.locator('span[data-bloks-name="bk.components.Text"]').first.text_content(timeout=400)
                username = username.strip()
            except:
                try:
                    username = await row.locator('span').first.text_content(timeout=400)
                    username = username.strip().split('\n')[0]
                except:
                    username = f"User_Index_L{loop_index}_I{i}"

            # Skip over profiles we have already categorized and logged
            if username in processed_usernames:
                continue

            toggle = row.locator(TOGGLE_SELECTOR).first
            if await toggle.count() == 0:
                continue

            new_users_found_in_this_pass = True
            processed_usernames.add(username)

            current_state = await is_toggled_on(toggle)
            if current_state == want_on:
                skipped += 1
                # Scrolling real-time feedback for skipped users
                print(f"  [✓ Skipped]  @{username:<25} (Already {target_state_label})")
            else:
                # Scrolling real-time feedback for processed actions
                print(f"  [⚡ Updated]  @{username:<25} (Action: {action_verb})")
                ok = await click_toggle(page, toggle)
                if ok:
                    changed += 1
                    await page.wait_for_timeout(350)  
                else:
                    failed += 1
                    print(f"  [✗ Failed ]  @{username:<25} (Click Refused)")

        if new_users_found_in_this_pass:
            empty_scroll_ticks = 0  
        else:
            empty_scroll_ticks += 1 

        # Snap directly down to the lowest loaded row to render the next block
        if last_row_element:
            try:
                await last_row_element.scroll_into_view_if_needed(timeout=2000)
            except:
                pass
        
        await page.wait_for_timeout(SCROLL_PAUSE_MS)
        loop_index += 1
        
        # Keep the summary stats constantly tracking seamlessly in the base layer
        print(f"    >> [Current Session Counters] Total Evaluated: {len(processed_usernames)} | Modified: {changed} | Skipped: {skipped}", end="\r")

    print("\n\n" + "─" * 55)
    print("  🏁 PLATFORM PIPELINE PROCESSING TERMINATED CLEANLY")
    print(f"  ✓ Unique Profiles Scanned     : {len(processed_usernames)}")
    print(f"  ✓ State Switches Executed     : {changed}")
    print(f"  – Left Untouched (Correct)    : {skipped}")
    print(f"  ✗ Core Failures/Errors        : {failed}")
    print("─" * 55)


# ---------------------------------------------------------------------------
# MAIN WORKFLOWS
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=" * 55)
    print("  Instagram Story Privacy Automation")
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
                await stream_process_all(page, want_on=True)
            elif choice == "2":
                await stream_process_all(page, want_on=False)
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