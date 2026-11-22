"""FIELD: repair missing app icons using branded SVGs and Throne GitHub avatar.
Run from FIELD project root: python fix_field_icons.py
Requires PySide6 (the same dependency as FIELD).
"""
from __future__ import annotations

import io
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "assets" / "app_icons"
DEST.mkdir(parents=True, exist_ok=True)

# For the first three logos use Simple Icons' brand vectors; multiple hosts for resiliency.
# The Throne image is the official project GitHub organization avatar.
SOURCES = {
    "Google.Chrome": (
        "svg", "#4285F4", (
            "https://cdn.jsdelivr.net/npm/simple-icons@15/icons/googlechrome.svg",
            "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/googlechrome.svg",
            "https://cdn.simpleicons.org/googlechrome/4285F4",
        )
    ),
    "Mozilla.Firefox": (
        "svg", "#FF7139", (
            "https://cdn.jsdelivr.net/npm/simple-icons@15/icons/firefoxbrowser.svg",
            "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/firefoxbrowser.svg",
            "https://cdn.simpleicons.org/firefoxbrowser/FF7139",
        )
    ),
    "EpicGames.EpicGamesLauncher": (
        "svg", "#FFFFFF", (
            "https://cdn.jsdelivr.net/npm/simple-icons@15/icons/epicgames.svg",
            "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/epicgames.svg",
            "https://cdn.simpleicons.org/epicgames/FFFFFF",
        )
    ),
    "Throneproj.Throne": (
        "image", None, (
            "https://github.com/throneproj.png?size=256",
            "https://avatars.githubusercontent.com/throneproj?s=256",
        )
    ),
}


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (FIELD installer icon repair)",
        "Accept": "image/svg+xml,image/png,image/webp,image/*;q=0.8,*/*;q=0.1",
    })
    with urllib.request.urlopen(request, timeout=18) as response:
        data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("Image is too large")
        return data


def render_svg(data: bytes, tint: str, size: int = 192) -> QImage:
    root = ET.fromstring(data)
    if not root.tag.endswith("svg"):
        raise ValueError("Response is not SVG")
    # The Simple Icons SVG paths have no fill: apply the chosen brand color.
    root.set("fill", tint)
    if root.get("xmlns") is None:
        root.set("xmlns", "http://www.w3.org/2000/svg")
    svg = ET.tostring(root, encoding="utf-8")
    renderer = QSvgRenderer(QByteArray(svg))
    if not renderer.isValid():
        raise ValueError("SVG renderer rejected the image")
    canvas = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    return canvas


def decode_image(data: bytes, size: int = 192) -> QImage:
    image = QImage.fromData(data)
    if image.isNull() or image.width() < 8 or image.height() < 8:
        raise ValueError("Response is not a usable image")
    return image.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)


def main() -> int:
    # QImage + SVG rendering needs a Qt application in some Qt installations.
    qt = QGuiApplication.instance() or QGuiApplication(sys.argv)
    failed = []
    for package, (kind, tint, urls) in SOURCES.items():
        output = DEST / f"{package}.png"
        problems = []
        for url in urls:
            try:
                data = download(url)
                image = render_svg(data, tint) if kind == "svg" else decode_image(data)
                if not image.save(str(output), "PNG"):
                    raise OSError("Could not save PNG")
                print(f"[OK] {package}: {output}")
                break
            except Exception as error:
                problems.append(f"{url}: {error}")
        else:
            failed.append(package)
            print(f"[FAIL] {package}")
            for item in problems:
                print(f"    {item}")
    print(f"\nFinished: {len(SOURCES) - len(failed)}/{len(SOURCES)} icons saved to {DEST}")
    if failed:
        print("Missing: " + ", ".join(failed))
        return 1
    print("Restart FIELD to reload the icons.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
