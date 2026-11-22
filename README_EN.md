# FIELD 

**FIELD** is a portable system utility for Windows 10 and Windows 11. It brings system information, selective configuration, optional built-in app cleanup, startup management, a process viewer, and a file lock inspector into one interface.

## Run FIELD

Download `FIELD.exe` from the repository's **Releases** page and double-click it. **No installer is required.** The finished EXE does not require Python, PySide6, or other Python packages to be installed separately on the user's PC.

> Build and test the Windows EXE on Windows before publishing it. The source repository alone does not include a prebuilt Windows executable.

## Features

- **System information:** Windows edition and version, CPU, GPU, and installed RAM.
- **Tweaks:** individual configuration changes with review and confirmation.
- **Applications:** selective removal of optional preinstalled Appx packages.
- **Startup:** viewing and management of supported user startup entries.
- **Processes:** process listing, search, and limited confirmed actions.
- **Lock Inspector:** file lock discovery using Windows Restart Manager.
- **Profiles and history:** configuration presets and action history.
- **Interface:** light/dark themes, Russian/English language, automatic Windows-language detection.

## Compatibility

Target versions are Windows 10 22H2 and Windows 11 24H2/25H2. Some functionality depends on the Windows build and available permissions. Compatibility must be tested on actual Windows machines.

## Portable behavior

- No installer or separate Python runtime is needed on the end-user's computer.
- A one-file PyInstaller executable temporarily extracts bundled components to the system temp folder at startup.
- FIELD **may write settings or logs to AppData**; a single EXE is not the same as zero local files.
- Some system actions require appropriate permissions. FIELD does not bypass Windows security.
- An unsigned executable may trigger a SmartScreen warning; do not disable security protections to run unfamiliar files.

## For developers

To build a single `FIELD.exe` **on Windows**, open the source in VS Code and run `build_FIELD.bat`. It installs build dependencies **on the developer's machine** and outputs `dist\FIELD.exe`.

See [BUILD.md](BUILD.md). Russian documentation: [README.md](README.md).

## Safety and limitations

FIELD does not aim to disable Defender, Windows Update, or other essential Windows protections. Removed Appx packages are not restored by a one-click undo; rollback applies only to supported operations. Back up important data before making changes.

**Status:** FIELD 1.0 is an early release and its GUI and system operations require testing on real Windows machines. FIELD is an independent project, not affiliated with Microsoft.

## License

No license has been chosen yet. Decide on licensing terms before publishing the source for reuse.
