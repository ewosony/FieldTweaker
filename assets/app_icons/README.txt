FIELD 1.2 brand icons

This folder includes actual branded vector-path PNGs for eight applications.
Other icons are retrieved at runtime (if connected) and saved under
%LOCALAPPDATA%\FIELD\brand_icons_v2.

To bundle remote icons into FIELD.exe, run:
  python download_app_icons.py --bundle

To force refresh and bundle all available icons:
  python download_app_icons.py --refresh --bundle

See ATTRIBUTION.md for licenses and source details.
