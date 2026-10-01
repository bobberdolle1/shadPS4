<!--
SPDX-FileCopyrightText: 2026 shadPS4 Emulator Project
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Development environment layout

This describes the layout the CUSA49696 work used. Nothing here is hardcoded in the
tooling — `autonomous_tools/paths.py` resolves paths from environment variables and falls
back to defaults derived from its own location:

| Variable | Meaning |
|---|---|
| `SHADPS4_REPO` | git checkout |
| `SHADPS4_BUILD` | out-of-source build directory |
| `SHADPS4_GAMES` | parent of `roms/` |
| `SHADPS4_EBOOT` | extracted `eboot.bin` |
| `SHADPS4_USERDATA` | emulator user data, defaults to `%APPDATA%/shadPS4` |

A typical layout, with everything on one fast NVMe:

```
<repo>/                       git checkout (branch cusa49696-xhigh-progress)
<repo>-build/                 out-of-source CMake/Ninja build -> shadps4.exe + .pdb
<games>/roms/CUSA49696/       My First Gran Turismo base game
<games>/roms/CUSA49696-patch/ its update
<games>/pkgs/                 original source PKGs, never touched by the emulator
```

Keep the checkout, the build directory and the game on the **same fast SSD**. The game was
moved off an HDD during this work, which mattered a great deal for load times.

Emulator user data (settings, logs, screenshots, shader cache) is per-user under
`%APPDATA%\shadPS4\`. The shader cache is several GB — keep it on an SSD or shader
recompilation will dominate startup.

## Building

```sh
cmake -S <repo> -B <build> -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang-cl.exe" \
      -DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang-cl.exe" \
      -DCMAKE_AR="C:/Program Files/LLVM/bin/llvm-lib.exe" \
      -DCMAKE_LINKER="C:/Program Files/LLVM/bin/lld-link.exe" \
      -DCMAKE_MT="C:/Program Files/LLVM/bin/llvm-mt.exe" \
      -DCMAKE_RC_COMPILER="C:/Program Files/LLVM/bin/llvm-rc.exe" \
      -DHAVE_ENDIAN_H=OFF
cmake --build <build> --target shadps4 -j 4
```

`-DHAVE_ENDIAN_H=OFF` is required on Windows with this toolchain: CMake's probe finds an
`endian.h` that is not the BSD one libressl needs, and enabling it breaks the
`externals/libressl` build.

Build at `-j 4`. Higher parallelism buys little for this codebase and does contend with the
emulator if it is running; a full rebuild takes roughly 10 minutes.

## Harness scripts

`autonomous_tools/paths.py` is the single source of truth for paths. The run scripts import
it, so relocating something means editing that one file (or setting an environment
variable), never the scripts individually.

Per-run captures and traces land in `autonomous_logs/`, which is gitignored and large
(hundreds of MB to a few GB per investigation). Delete it freely; regenerate by re-running.

`autonomous_tools/RenderDoc_1.46_64/` holds a RenderDoc build used for GPU capture. It is
fetched separately and gitignored — it is third-party and must not be committed.

## Running the game

`%APPDATA%\shadPS4\config.json` has `install_dirs[0].path` pointing at the `roms/` directory.