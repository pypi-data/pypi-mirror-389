"""RealTimeX PyAutoGUI MCP server with deterministic waits."""

from __future__ import annotations

import io
import os
import time
from typing import Dict, List

import pyautogui
from fastmcp import FastMCP, Image
from pydantic import Field

DEFAULT_PAUSE = 0.3
MAX_WAIT_SECONDS = 30.0


def _configure_pyautogui() -> None:
    pause = os.getenv("REALTIMEX_PAUSE")
    try:
        pyautogui.PAUSE = float(pause) if pause is not None else DEFAULT_PAUSE
    except ValueError:
        pyautogui.PAUSE = DEFAULT_PAUSE

    failsafe_env = os.getenv("REALTIMEX_FAILSAFE")
    if failsafe_env is None:
        pyautogui.FAILSAFE = True
    else:
        pyautogui.FAILSAFE = failsafe_env not in {"0", "false", "False"}


_configure_pyautogui()

mcp = FastMCP(
    "RealTimeX PyAutoGUI Server",
    description="Deterministic desktop automation using PyAutoGUI with explicit wait tooling.",
    dependencies=["pyautogui", "Pillow"],
)


def _success(message: str) -> Dict[str, str]:
    return {"status": "success", "message": message}


def _failure(reason: str) -> Dict[str, str]:
    return {"status": "error", "message": reason}


@mcp.tool(
    description="Pause execution for the specified number of seconds without sending keystrokes."
)
def wait(
    seconds: float = Field(
        default=1.0,
        gt=0.0,
        le=MAX_WAIT_SECONDS,
        description="Duration to pause in seconds (0 < seconds ≤ 30).",
    ),
) -> Dict[str, str]:
    try:
        time.sleep(seconds)
    except Exception as exc:
        return _failure(f"Failed to wait {seconds} seconds: {exc}")
    return _success(f"Waited {seconds} seconds.")


@mcp.tool()
def get_screen_size() -> Dict[str, str]:
    """Get the size of the primary screen."""
    size = pyautogui.size()
    return _success(f"Screen size: {size.width}x{size.height}")


@mcp.tool()
def get_mouse_position() -> Dict[str, str]:
    """Get the current position of the mouse."""
    pos = pyautogui.position()
    return _success(f"Mouse position: ({pos.x}, {pos.y})")


@mcp.tool()
def move_mouse(
    x: int = Field(description="The x-coordinate on the screen to move the mouse to."),
    y: int = Field(description="The y-coordinate on the screen to move the mouse to."),
) -> Dict[str, str]:
    """Move the mouse to the given coordinates."""
    try:
        pyautogui.moveTo(x, y)
        return _success(f"Mouse moved to coordinates ({x}, {y}).")
    except pyautogui.FailSafeException:
        return _failure(
            "Operation cancelled - mouse moved to screen corner (failsafe)."
        )
    except Exception as exc:
        return _failure(f"Failed to move mouse: {exc}")


@mcp.tool()
def click_mouse() -> Dict[str, str]:
    """Click the mouse at its current position."""
    try:
        pyautogui.click()
        return _success("Mouse clicked at current position.")
    except pyautogui.FailSafeException:
        return _failure("Operation cancelled - mouse in screen corner (failsafe).")
    except Exception as exc:
        return _failure(f"Failed to click mouse: {exc}")


@mcp.tool()
def double_click_mouse() -> Dict[str, str]:
    """Double-click the mouse at its current position."""
    try:
        pyautogui.doubleClick()
        return _success("Mouse double-clicked at current position.")
    except pyautogui.FailSafeException:
        return _failure("Operation cancelled - mouse in screen corner (failsafe).")
    except Exception as exc:
        return _failure(f"Failed to double-click mouse: {exc}")


@mcp.tool()
def drag_mouse(
    x: int = Field(description="The x-coordinate to drag to."),
    y: int = Field(description="The y-coordinate to drag to."),
    duration: float = Field(
        default=0.5,
        ge=0.0,
        le=10.0,
        description="Duration of the drag in seconds.",
    ),
) -> Dict[str, str]:
    """Drag the mouse to a target location."""
    try:
        pyautogui.dragTo(x, y, duration=duration)
        return _success(f"Mouse dragged to ({x}, {y}) over {duration} seconds.")
    except pyautogui.FailSafeException:
        return _failure("Operation cancelled - mouse in screen corner (failsafe).")
    except Exception as exc:
        return _failure(f"Failed to drag mouse: {exc}")


@mcp.tool()
def hotkey(
    keys: List[str] = Field(
        description="List of key names to press together (e.g. ['command', 'c'] for copy)."
    ),
) -> Dict[str, str]:
    """Press a sequence of keys simultaneously."""
    try:
        pyautogui.hotkey(*keys)
        return _success(f"Pressed hotkey combination: {' + '.join(keys)}.")
    except pyautogui.FailSafeException:
        return _failure("Operation cancelled - mouse in screen corner (failsafe).")
    except Exception as exc:
        return _failure(f"Failed to press hotkey: {exc}")


@mcp.tool()
def press_key(
    key: str = Field(
        description="Name of the key to press (e.g. 'enter', 'tab', 'a')."
    ),
) -> Dict[str, str]:
    """Press a single key."""
    try:
        pyautogui.press(key)
        return _success(f"Pressed key: {key}.")
    except pyautogui.FailSafeException:
        return _failure("Operation cancelled - mouse in screen corner (failsafe).")
    except Exception as exc:
        return _failure(f"Failed to press key: {exc}")


@mcp.tool()
def type_text(
    text: str = Field(description="The text string to type out verbatim."),
    interval: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Delay between characters to mimic natural typing.",
    ),
) -> Dict[str, str]:
    """Type a string of characters."""
    try:
        pyautogui.typewrite(text, interval=interval)
        return _success(f"Typed string of length {len(text)} characters.")
    except pyautogui.FailSafeException:
        return _failure("Operation cancelled - mouse in screen corner (failsafe).")
    except Exception as exc:
        return _failure(f"Failed to type string: {exc}")


@mcp.tool()
def screenshot() -> Image | Dict[str, str]:
    """Take a screenshot of the current screen."""
    try:
        buffer = io.BytesIO()
        shot = pyautogui.screenshot()
        shot.convert("RGB").save(buffer, format="JPEG", quality=60, optimize=True)
        return Image(data=buffer.getvalue(), format="jpeg")
    except pyautogui.FailSafeException:
        return _failure("Operation cancelled - mouse in screen corner (failsafe).")
    except Exception as exc:
        return _failure(f"Failed to take screenshot: {exc}")


@mcp.tool()
def scroll(
    clicks: int = Field(
        description="Number of scroll units (positive to scroll up, negative to scroll down)."
    ),
) -> Dict[str, str]:
    """Scroll the mouse wheel."""
    try:
        pyautogui.scroll(clicks)
        direction = "up" if clicks > 0 else "down" if clicks < 0 else "no movement"
        return _success(f"Scrolled {direction} by {abs(clicks)} units.")
    except Exception as exc:
        return _failure(f"Failed to scroll: {exc}")


def main() -> None:
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
