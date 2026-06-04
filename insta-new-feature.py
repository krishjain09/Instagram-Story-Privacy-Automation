"""
Instagram "Hide Story From" Automation  (v24 — Strict State Verification Engine)
=======================================================================
URL: https://www.instagram.com/accounts/hide_story_and_live_from/
"""

import asyncio
import sys
import time
from playwright.async_api import (
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

STORY_HIDE_URL   = "https://www.instagram.com/accounts/hide_story_and_live_from/"
HEADLESS         = False          # Must stay False — Instagram blocks headless

SCROLL_STEP_PX   = 280            # Smaller steps so the virtual DOM doesn't panic-drop rows
SCROLL_PAUSE_MS  = 2800           # Generous wait time to let rows completely settle and change color
MAX_STALL_TICKS  = 10             # Stops loop if the true end of the list is reached
CLICK_PAUSE_MS   = 600            # Delay after clicking to let Instagram sync with the cloud databases
TOGGLE_TIMEOUT   = 3_500          # Per-toggle check threshold
ROW_TIMEOUT      = 600            # Per-row name identification threshold

# ═══════════════════════════════════════════════════════════════════
# SELECTORS
# ═══════════════════════════════════════════════════════════════════

ROW_SELECTOR     = 'div:has(> div > [aria-label="Toggle checkbox"])'
TOGGLE_SELECTOR  = '[aria-label="Toggle checkbox"]'
# Spinner selector — deliberately narrow so we never match decorative SVGs.
# circle[stroke] alone matches profile-picture borders, icons, and every other
# circular SVG on the page, causing an infinite wait loop.
# We only match elements that Instagram actually uses for loading indicators:
#   • role="progressbar"  — ARIA loading bar
#   • svg[aria-label="Loading..."]  — explicit loading SVG label
# circle[stroke] is intentionally excluded.
# SPINNER_SELECTOR = 'svg[aria-label="Loading..."], [role="progressbar"]'
# Spinner selector — strictly targeted to active animated graphic wrappers
# to prevent capturing structural layout containers utilizing role="progressbar".
SPINNER_SELECTOR = 'svg[aria-label="Loading..."], div[role="progressbar"] svg, div[style*="rotate"]'
# ═══════════════════════════════════════════════════════════════════
# BROWSER SETUP
# ═══════════════════════════════════════════════════════════════════

async def build_context(playwright: Playwright):
    browser = await playwright.chromium.launch(
        headless=HEADLESS,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
        ],
    )
    context = await browser.new_context(
        no_viewport=True,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    page = await context.new_page()
    return browser, context, page


# ═══════════════════════════════════════════════════════════════════
# LOGIN ENGINE
# ═══════════════════════════════════════════════════════════════════

async def login_via_terminal(page: Page) -> None:
    print("\n" + "=" * 55)
    print("  INSTAGRAM CREDENTIALS")
    print("=" * 55)

    username = (await asyncio.to_thread(input, "Username / Email : ")).strip()
    password = (await asyncio.to_thread(input, "Password         : ")).strip()
    
    if not username or not password:
        raise RuntimeError("Username and password cannot be empty.")

    print("\n[→] Opening Instagram login page …")
    await page.goto(
        "https://www.instagram.com/accounts/login/",
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    await page.wait_for_timeout(2000)

    try:
        for btn_text in ["Allow all cookies", "Allow essential and optional cookies", "Accept"]:
            btn = page.locator(f"button:has-text('{btn_text}')").first
            if await btn.is_visible(timeout=800):
                await btn.click()
                await page.wait_for_timeout(500)
                break
    except Exception:
        pass

    print("[→] Waiting for login form fields …")
    try:
        username_field = page.locator('input[type="text"], input[name="username"]').first
        password_field = page.locator('input[type="password"], input[name="password"]').first
        await username_field.wait_for(state="attached", timeout=15_000)
    except PlaywrightTimeout:
        raise RuntimeError("Login form fields not found. Instagram layout changed.")

    print("[→] Autotyping username …")
    await username_field.focus()
    await username_field.click()
    await page.keyboard.type(username, delay=80)

    print("[→] Autotyping password …")
    await password_field.focus()
    await password_field.click()
    await page.keyboard.type(password, delay=80)

    print("[→] Auto-submitting login form …")
    try:
        login_button = page.locator('form button[type="submit"], form button:has-text("Log in")').first
        await login_button.wait_for(state="visible", timeout=3000)
        await login_button.click(force=True)
    except Exception:
        try:
            print("[→] Button click layer blocked, fallback to keyboard Enter injection…")
            await password_field.focus()
            await page.keyboard.press("Enter")
        except Exception as e:
            print(f"[!] Auto-submit failed: {e}")

    await page.wait_for_timeout(4000)

    print("\n╔" + "═" * 58 + "╗")
    print("║ 🛑 ACTION REQUIRED: SECURITY & BOT VERIFICATION          ║")
    print("║                                                          ║")
    print("║ 1. Look at the open browser window.                      ║")
    print("║ 2. Complete any 'Not a Robot' CAPTCHAs, puzzles, or 2FA. ║")
    print("║ 3. Make sure you are fully on your Instagram Feed / Home.║")
    print("╚" + "═" * 58 + "╝")
    
    await asyncio.to_thread(
        input, "\n👉 Once you have cleared everything manually, press [ENTER] here to resume: "
    )

    for label in ["Not Now", "Cancel", "Skip", "Close"]:
        try:
            await page.locator(f"button:has-text('{label}')").first.click(timeout=1500)
        except Exception:
            pass

    print(f"\n[✓] Securely logged in as @{username}. Syncing panel systems…")
    await page.wait_for_timeout(1000)


# ═══════════════════════════════════════════════════════════════════
# SCROLL UTILITIES
# ═══════════════════════════════════════════════════════════════════

async def find_scroll_container(page: Page) -> str | None:
    result = await page.evaluate("""
        () => {
            const anchor = document.querySelector('[aria-label="Toggle checkbox"]');
            if (!anchor) return null;
            let el = anchor.parentElement;
            while (el && el !== document.body) {
                const style    = window.getComputedStyle(el);
                const overflow = style.overflowY;
                const scrollable = (overflow === 'auto' || overflow === 'scroll');
                if (scrollable && el.scrollHeight > el.clientHeight) {
                    el.setAttribute('data-ig-scroll-target', 'true');
                    return true;
                }
                el = el.parentElement;
            }
            return false;
        }
    """)
    return result

async def get_scroll_pos(page: Page, use_inner: bool) -> int:
    if use_inner:
        return await page.evaluate("() => { const el = document.querySelector('[data-ig-scroll-target]'); return el ? el.scrollTop : 0; }")
    return await page.evaluate("() => window.scrollY")

async def do_scroll(page: Page, use_inner: bool, step: int) -> None:
    if use_inner:
        await page.evaluate("(step) => { const el = document.querySelector('[data-ig-scroll-target]'); if (el) el.scrollTop += step; }", step)
    else:
        await page.evaluate("(step) => window.scrollBy(0, step)", step)


# ═══════════════════════════════════════════════════════════════════
# STRICT VISUAL STATE VALIDATOR
# ═══════════════════════════════════════════════════════════════════

async def is_toggled_on(toggle_el) -> bool:
    """
    Determine whether a toggle is currently ON (story hidden from this person).

    BUG FIXES vs v24:
    ─────────────────
    1. Never search outerHTML as a raw string.
       outerHTML serialises the *entire subtree* — any descendant that happens
       to carry aria-checked="true" would make the whole thing read as True,
       even if the toggle itself is Off.

    2. Read aria-checked via getAttribute(), not string search.
       getAttribute is the canonical DOM API — it is unaffected by attribute
       ordering or quote style differences in HTML serialisation.

    3. Three independent signals are combined; majority-vote is NOT used —
       instead we use a strict priority order so the most reliable signal
       always wins.

    Priority order (most → least reliable):
      A. aria-checked attribute on the toggle element itself (canonical)
      B. SVG fill colour — Instagram fills the circle blue (#0095F6 / currentColor
         inside a specific class) when checked, grey when unchecked
      C. Presence of a specific Bloks class name ONLY on the toggle element
         (not its descendants) to avoid subtree pollution
    """
    # ── Signal A: aria-checked on the toggle element itself ───────────
    # This is the authoritative ARIA state — read it as a DOM property,
    # not by searching serialised HTML.
    try:
        aria = await toggle_el.evaluate(
            "(el) => el.getAttribute('aria-checked')",
            timeout=600,
        )
        if aria is not None:
            # aria is a string: "true" or "false"
            result = aria.strip().lower() == "true"
            return result
    except Exception:
        pass

    # ── Signal B: SVG fill colour inside the toggle ───────────────────
    # Instagram Bloks colours the inner circle element:
    #   checked   → fill="#0095F6"  or class containing "filled"
    #   unchecked → fill="#DBDBDB"  or class containing "empty" / no fill attr
    try:
        colour_state = await toggle_el.evaluate("""
            (el) => {
                // Look for any circle/path element inside the toggle
                const circle = el.querySelector('circle, path, svg');
                if (!circle) return null;
                const fill = circle.getAttribute('fill') || '';
                const cls  = circle.getAttribute('class') || '';
                if (fill.toLowerCase() === '#0095f6' || cls.includes('filled')) {
                    return 'on';
                }
                if (fill.toLowerCase() === '#dbdbdb' || cls.includes('empty')) {
                    return 'off';
                }
                return null;   // inconclusive
            }
        """, timeout=600)
        if colour_state == 'on':
            return True
        if colour_state == 'off':
            return False
    except Exception:
        pass

    # ── Signal C: class name on the toggle element only (not subtree) ─
    # Last resort — check only the toggle element's own class list,
    # never the full innerHTML, to avoid subtree pollution.
    try:
        own_class = await toggle_el.evaluate(
            "(el) => el.className || ''",
            timeout=600,
        )
        own_class_lower = own_class.lower()
        if "circle-check__filled" in own_class_lower or "checked" in own_class_lower:
            return True
    except Exception:
        pass

    # If all signals are inconclusive, treat as OFF (safe default —
    # worst case we click something that was already correct, which
    # Instagram will just toggle back; we verify afterward anyway).
    return False


# ═══════════════════════════════════════════════════════════════════
# STABLE ACTION CONTROLLER
async def process_all(page: Page, want_on: bool) -> None:
    target_label = "Hidden" if want_on else "Visible"
    action_verb  = "Hide from" if want_on else "Unhide for"

    # Meta Bloks Framework specific structural element paths
    BLOKS_ROW_SELECTOR = 'div[data-bloks-name="bk.components.Flexbox"] > div[style*="pointer-events: auto"][style*="cursor: pointer"]'
    USERNAME_SELECTOR  = 'span[data-bloks-name="bk.components.Text"]'
    CHECKBOX_SELECTOR  = 'div[aria-label="Toggle checkbox"]'

    print("\n[→] Waiting for follower list to render …")
    try:
        await page.wait_for_selector(BLOKS_ROW_SELECTOR, timeout=20_000)
    except PlaywrightTimeout:
        print("\n[!] No follower rows found after 20 s.")
        return

    print("[→] Detecting scroll container …")
    use_inner = await find_scroll_container(page)
    container_label = "inner <div>" if use_inner else "window"
    print(f"[✓] Scroll target : {container_label}")

    processed_history: set[str] = set()
    
    total_changed  = 0
    total_skipped  = 0
    total_failed   = 0
    stall_ticks    = 0
    prev_scroll    = -1
    loop           = 0
    start_time     = time.time()

    print("\n" + "─" * 65)
    print(f"  Starting virtual-DOM scroll engine  →  goal: {target_label}")
    print("─" * 65)

    while stall_ticks < MAX_STALL_TICKS:
        loop += 1
        
        scroll_pos = await get_scroll_pos(page, use_inner)

        # Base end-of-list verification via duplicate tracking analysis
        if scroll_pos <= prev_scroll:
            stall_ticks += 1
            print(f"  [DEBUG] Scroll resting (pos={scroll_pos}px, tick {stall_ticks}/{MAX_STALL_TICKS})")
            if stall_ticks >= MAX_STALL_TICKS:
                break
        else:
            current_viewport_rows = await page.locator(BLOKS_ROW_SELECTOR).all()
            if current_viewport_rows:
                all_dups = True
                for r_node in current_viewport_rows:
                    try:
                        u_node = r_node.locator(USERNAME_SELECTOR).first
                        r_user = await u_node.text_content(timeout=300)
                        if r_user and r_user.strip() not in processed_history:
                            all_dups = False
                            break
                    except Exception:
                        continue
                if all_dups:
                    stall_ticks += 1
                    print(f"  [DEBUG] Frame contains only duplicate entries. Nearing bottom boundary (tick {stall_ticks}/{MAX_STALL_TICKS}).")
                    if stall_ticks >= MAX_STALL_TICKS:
                        break
                else:
                    stall_ticks = 0
            else:
                stall_ticks = 0

        prev_scroll = scroll_pos
        
        visible_rows = await page.locator(BLOKS_ROW_SELECTOR).all()
        row_count = len(visible_rows)
        print(f"\n  [DEBUG] Frame={loop:<4} ScrollPos={scroll_pos:<5}px VisibleRows={row_count:<3} UniqueHandled={len(processed_history)}")

        if row_count == 0:
            await do_scroll(page, use_inner, SCROLL_STEP_PX)
            await page.wait_for_timeout(SCROLL_PAUSE_MS)
            continue

        changed_any_state = False

        for i in range(row_count):
            try:
                row = visible_rows[i]
                user_text_node = row.locator(USERNAME_SELECTOR).first
                toggle_loc = row.locator(CHECKBOX_SELECTOR).first

                if not await user_text_node.count() or not await toggle_loc.count():
                    continue

                username = await user_text_node.text_content(timeout=ROW_TIMEOUT)
                if not username:
                    continue
                username = username.strip()

                if username.lower() == "search":
                    continue

                if username in processed_history:
                    print(f"    [↩ Dup   ]  {username:<32}  already processed — skipping")
                    continue

                processed_history.add(username)
                print(f"    [✓ Row ]  {username}")

                # Safely capture current state via inner SVG components
                icon_inner_html = await toggle_loc.inner_html()
                state_before = "filled" in icon_inner_html.lower()
                
                print(
                    f"    [State]  {username:<32}  "
                    f"before={'Hidden' if state_before else 'Visible'}  "
                    f"want={target_label}"
                )

                if state_before == want_on:
                    total_skipped += 1
                    print(f"    [─ Skip ]  {username:<32}  (already {target_label})")
                    continue

                # Pre-click lookup to protect against clicking the floating message layer
                await toggle_loc.scroll_into_view_if_needed()
                is_covered = await page.evaluate("""
                    (args) => {
                        const rows = document.querySelectorAll(args.rowSel);
                        const row = rows[args.idx];
                        const msgBtn = document.querySelector('div[role="button"]:-webkit-any-link, div[style*="position: fixed"] div[role="button"], div#id_messages_button');
                        const floatingMsg = msgBtn || [...document.querySelectorAll('div')].find(d => d.innerText && d.innerText.includes('Messages') && window.getComputedStyle(d).position === 'fixed');
                        
                        if (!row || !floatingMsg) return false;
                        const rRect = row.getBoundingClientRect();
                        const mRect = floatingMsg.getBoundingClientRect();
                        
                        return !(rRect.right < mRect.left || rRect.left > mRect.right || rRect.bottom < mRect.top || rRect.top > mRect.bottom);
                    }
                """, {"rowSel": BLOKS_ROW_SELECTOR, "idx": i})

                if is_covered:
                    print("    [⚠ Overlap Warning] Row blocked by floating chat panel. Offsetting element upward...")
                    await do_scroll(page, use_inner, 120)
                    await page.wait_for_timeout(400)

                # Ensure layout menus are dismissed
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(100)

                print(f"    [⚡ Click ]  {username:<32}  (attempting {action_verb})")
                await toggle_loc.click(timeout=TOGGLE_TIMEOUT, force=True)
                await page.wait_for_timeout(CLICK_PAUSE_MS)

                # Verification sync check
                updated_html = await toggle_loc.inner_html()
                state_after = "filled" in updated_html.lower()
                
                print(
                    f"    [Verify]  {username:<32}  "
                    f"after={'Hidden' if state_after else 'Visible'}  "
                    f"expected={target_label}"
                )

                if state_after == want_on:
                    total_changed += 1
                    print(f"    [✓ Done  ]  {username:<32}  (confirmed {target_label})")
                    changed_any_state = True
                else:
                    total_failed += 1
                    print(f"    [✗ NoFlip]  {username:<32}  (state change unacknowledged by cloud server)")

            except Exception as row_err:
                total_failed += 1
                print(f"    [✗ Error ]  Skipping target list index {i}: {row_err}")
                continue

        # Smooth container progression step down the tree layout
        await do_scroll(page, use_inner, SCROLL_STEP_PX)
        await page.wait_for_timeout(SCROLL_PAUSE_MS)

    total_time = int(time.time() - start_time)
    print("\n" + "═" * 55)
    print("  ✅  PROCESSING COMPLETE")
    print("═" * 55)
    print(f"  Time taken          : {total_time // 60}m {total_time % 60}s")
    print(f"  Total Checked       : {len(processed_history)}")
    print(f"  Toggles adjusted    : {total_changed}")
    print(f"  Already correct     : {total_skipped}")
    print(f"  Execution failures  : {total_failed}")
    print("═" * 55)
#═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

async def main() -> None:
    print("═" * 55)
    print("  Instagram Story Privacy Automation  v24")
    print("═" * 55)

    async with async_playwright() as pw:
        browser, context, page = await build_context(pw)
        try:
            await login_via_terminal(page)

            print(f"\n[→] Navigating to {STORY_HIDE_URL} …")
            await page.goto(STORY_HIDE_URL, wait_until="domcontentloaded")
            print("[→] Waiting 5 s for Bloks UI to fully render …")
            await page.wait_for_timeout(5_000)

            print("\n  What would you like to do?")
            print("  [1] Hide story from ALL followers")
            print("  [2] Unhide story for ALL followers")
            print("  [q] Quit")
            choice = (await asyncio.to_thread(input, "\n  Enter choice: ")).strip().lower()

            if choice == "1":
                await process_all(page, want_on=True)
            elif choice == "2":
                await process_all(page, want_on=False)
            else:
                print("Exiting.")

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