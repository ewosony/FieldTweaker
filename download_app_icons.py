"""Download refreshed application logos for FIELD (not web page favicons only)."""
from __future__ import annotations
import argparse
from pathlib import Path
from personal_lite.brand_icons import download_icons, icon_cache_dir, ICON_SOURCES


def main():
    parser = argparse.ArgumentParser(description='Prepare branded app icons for FIELD.')
    parser.add_argument('--refresh', action='store_true', help='Redownload even existing icons')
    parser.add_argument('--bundle', action='store_true', help='Copy downloaded icons to assets/app_icons before building the EXE')
    args = parser.parse_args()
    bundled = Path(__file__).resolve().parent / 'assets' / 'app_icons'
    ok, total = download_icons(list(ICON_SOURCES), refresh=args.refresh,
                               bundled_dir=None if args.refresh else bundled)
    print(f'Available logos: {ok}/{total}; cache: {icon_cache_dir()}')
    if args.bundle:
        import shutil
        bundled.mkdir(parents=True, exist_ok=True)
        count = 0
        for path in icon_cache_dir().iterdir():
            if path.suffix in ('.png', '.svg', '.ico', '.jpg') and path.is_file():
                shutil.copy2(path, bundled / path.name)
                count += 1
        print(f'Copied {count} downloaded logos into {bundled}')
    print('Missing logos will use bundled brand marks or reserve icons.')

if __name__ == '__main__':
    main()
