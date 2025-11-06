"""Playwright helpers for human-like mouse movement and typing.

These utilities attempt to simulate more realistic user behavior while
interacting with pages via Playwright's sync API.
"""

from random import randint
from time import time

from playwright.sync_api import Page, Error

from autowebx import Timer


def add_mouse_position_listener(page: Page):
    page.add_init_script("""
      window._mousePos = {x: 0, y: 0};
      document.addEventListener('mousemove', e => {
        window._mousePos.x = e.clientX;
        window._mousePos.y = e.clientY;
      });
    """)


def mouse_position(page: Page):
    return page.evaluate("window._mousePos")


def in_viewport(page: Page, selector: str):
    return page.evaluate("""
      (selector) => {
        const el = document.querySelector(selector);
        if (!el) return "not-found";
        const rect = el.getBoundingClientRect();
        const viewHeight = window.innerHeight || document.documentElement.clientHeight;

        if (rect.bottom < 0) return "above";        // fully above viewport
        if (rect.top > viewHeight) return "below";  // fully below viewport
        return "in";                                // at least partially in viewport
      }
    """, selector)


def click(page: Page, selector: str, timeout: int = 30):
    start = time()
    while True:
        if time() - start > timeout:
            raise TimeoutError(f"Could not click {selector}")

        try:
            while True:
                timer = Timer(timeout, 'Element not found')
                while True:
                    pos = in_viewport(page, selector)
                    if pos == "in":
                        break
                    if pos == "above":
                        page.mouse.wheel(0, randint(-5, -1))
                    elif pos == "below":
                        page.mouse.wheel(0, randint(1, 5))
                    timer()

                element = page.wait_for_selector(selector)
                box = element.bounding_box()

                x_element = box['x'] + box['width'] / 2
                y_element = box['y'] + box['height'] / 2

                position = mouse_position(page)
                in_x = box['x'] < position['x'] < box['x'] + box['width']
                in_y = box['y'] < position['y'] < box['y'] + box['height']

                if in_x and in_y:
                    page.mouse.click(position['x'], position['y'])
                    return

                if x_element - position['x'] > 0:
                    x_new = position['x'] + randint(1, 5)
                else:
                    x_new = position['x'] - randint(1, 5)

                if y_element - position['y'] > 0:
                    y_new = position['y'] + randint(1, 5)
                else:
                    y_new = position['y'] - randint(1, 5)

                page.mouse.move(x_new, y_new)
        except Error:
            pass


def fill(page: Page, selector: str, text: str):
    click(page, selector)
    click(page, selector)
    page.keyboard.press('Backspace')
    page.keyboard.type(text)


def show_mouse(page):
    style = """
      .playwright-mouse {
        position: absolute;
        background: red;
        border: 1px solid white;
        border-radius: 50%;
        width: 10px;
        height: 10px;
        margin: -5px 0 0 -5px;
        z-index: 2147483647;
        pointer-events: none;
      }
    """
    page.add_style_tag(content=style)

    script = """
      () => {
        if (window.__mouseHelperInstalled) return;
        window.__mouseHelperInstalled = true;

        const mouse = document.createElement('div');
        mouse.classList.add('playwright-mouse');
        document.body.appendChild(mouse);

        document.addEventListener('mousemove', e => {
          mouse.style.left = e.pageX + 'px';
          mouse.style.top = e.pageY + 'px';
        });
      }
    """
    # attach for all future navigations
    page.add_init_script(script)
    # also run once immediately
    page.evaluate(script)
