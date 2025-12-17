"""
Web Browser Utilities - Open external links in user's default browser.

This module provides helper functions to open documentation, support, and
information pages in the user's default web browser.

WHY separate module:
    These functions are called from multiple places (system tray menu, first-run
    welcome). Centralizing them here makes it easy to:
    - Update URLs in one place
    - Add tracking parameters if needed
    - Mock during testing
    - Add error handling uniformly

WHY webbrowser.open():
    Python's webbrowser module is cross-platform and respects the user's
    default browser preference (Edge, Chrome, Firefox, etc.). It's more
    polite than hardcoding chrome.exe or other specific browsers.

WHY new=2:
    This parameter tells webbrowser to open in a new tab if possible, rather
    than reusing an existing tab or opening a new window. This is less
    disruptive to users' workflow.

    Options:
    - new=0: Same window/tab (not ideal - takes over existing tab)
    - new=1: New window (disruptive, clutters taskbar)
    - new=2: New tab (polite, keeps browser windows organized)

URL strategy:
    All URLs point to catlock.app domain, which provides:
    - Professional presentation
    - Easy to update without recompiling app
    - Analytics on which docs users access
    - SEO benefits for project visibility

See also:
    - tray_icon.py: Menu items that call these functions
    - config.py: Calls open_about() on first run
"""

import webbrowser


def open_about():
    """
    Open the PawGate About page in user's default browser.

    The About page explains:
    - What PawGate does (protect your computer from cats)
    - How to use it (hotkeys, tray icon menu)
    - Why it was created (real problem with real feline Fiona)

    WHY open on first run:
        Users who just installed PawGate might not understand what it does or
        how to use it. Opening the About page provides immediate context and
        reduces "What is this thing?" confusion.

    URL: https://catlock.app/about/

    See also:
        - config.py: Calls this on first run (config file doesn't exist)
        - tray_icon.py: Menu item "About"
    """
    # Open in new tab (new=2) to avoid disrupting existing browser session
    webbrowser.open("https://catlock.app/about/", new=2)


def open_buy_me_a_coffee():
    """
    Open the developer's Buy Me a Coffee page for donations.

    This provides a way for grateful users to support the project with
    small donations. It's linked from the system tray menu as "Support".

    WHY Buy Me a Coffee:
        - Simple, no account required for donors
        - Lower fees than Patreon or similar platforms
        - Casual, low-pressure (coffee metaphor is friendly)
        - Common in open-source community

    WHY in tray menu:
        Users who find PawGate valuable can easily support it without
        hunting for a GitHub sponsors link or donation page.

    URL: https://buymeacoffee.com/richiehowelll

    See also:
        - tray_icon.py: Menu item "Support ☕"
    """
    # Open in new tab (new=2) to avoid disrupting existing browser session
    webbrowser.open("https://buymeacoffee.com/richiehowelll", new=2)


def open_help():
    """
    Open the PawGate FAQ/Help page in user's default browser.

    The Help page answers common questions:
    - How do I change the hotkey?
    - Why isn't my keyboard locking?
    - How do I uninstall PawGate?
    - Does it work with multiple monitors?
    - Can I lock automatically when I leave?

    WHY FAQ instead of in-app help:
        - Web pages are easier to update than recompiling/redistributing app
        - Can include screenshots, GIFs, videos
        - Users can bookmark for future reference
        - Search engines can index for discoverability

    URL: https://catlock.app/faq/

    See also:
        - tray_icon.py: Menu item "Help"
    """
    # Open in new tab (new=2) to avoid disrupting existing browser session
    webbrowser.open("https://catlock.app/faq/", new=2)

