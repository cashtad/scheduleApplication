# Build and Startup Benchmark

## What is included

- `schedule_analyzer.spec` - onedir build (default)
- `schedule_analyzer.onefile.spec` - onefile build
- `build_exe.bat` - build matrix wrapper
- `installer/schedule_analyzer.iss` - Inno Setup script (Czech installer UI)
- `build_installer.bat` - installer build wrapper
- `tools/benchmark_startup.py` - startup benchmark helper (`--smoke-startup` mode)

## Quick start

```bat
build_exe.bat onedir 3
build_exe.bat onefile 3
build_exe.bat all 3
```

Second argument is number of benchmark runs.

## Build installer (recommended for end users)

Prerequisite: install Inno Setup 6 (contains `ISCC.exe`).

```bat
build_installer.bat
```

This command reuses `dist/schedule_analyzer` if present; otherwise it builds onedir first.

Installer output:

- `artifacts/installer/schedule_analyzer_setup.exe`

## Output

- `dist/schedule_analyzer/schedule_analyzer.exe` (onedir)
- `dist/schedule_analyzer_onefile.exe` (onefile)
- `artifacts/builds/startup_metrics.csv`
- `artifacts/builds/onedir_startup.json`
- `artifacts/builds/onefile_startup.json`

## Notes

- App creates `rules_config.yaml` automatically if it is missing.
- Build script copies `src/rules_config.yaml` near executables only as optional fallback (when source file exists).
- Startup benchmark uses `--smoke-startup` to initialize Qt and main window, then exits immediately.
- This allows comparing onefile unpacking overhead vs onedir startup latency.
- Installer is configured as per-user install (`{localappdata}`), so app can create `rules_config.yaml` next to `.exe` without admin rights.

