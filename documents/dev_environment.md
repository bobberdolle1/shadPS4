# Development environment layout

Everything for this project lives on **F:**, which is the NVMe SSD. E: is an HDD and was the
old location; nothing should be built or run from it any more.

```
F:\dev\shadPS4\           git checkout (branch cusa49696-xhigh-progress, tag cusa49696-first-race)
F:\dev\shadPS4-build\     out-of-source CMake/Ninja build, produces shadps4.exe + shadps4.pdb
F:\games\ps4\roms\       extracted games the emulator reads
F:\games\ps4\roms\CUSA49696\        My First Gran Turismo base game
F:\games\ps4\roms\CUSA49696-patch\  its update
F:\games\ps4\pkgs\       original source PKGs, never touched by the emulator
F:\games\ps4\addons\     add-ons
```

Emulator user data (settings, logs, screenshots, shader cache) stays per-user on C:
under `%APPDATA%\shadPS4\`. C: is also an NVMe SSD, so the 5 GB shader cache is not a
disk bottleneck and does not need moving.

## Building

```sh
cmake -S F:/dev/shadPS4 -B F:/dev/shadPS4-build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang-cl.exe" \
      -DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang-cl.exe" \
      -DCMAKE_AR="C:/Program Files/LLVM/bin/llvm-lib.exe" \
      -DCMAKE_LINKER="C:/Program Files/LLVM/bin/lld-link.exe" \
      -DCMAKE_MT="C:/Program Files/LLVM/bin/llvm-mt.exe" \
      -DCMAKE_RC_COMPILER="C:/Program Files/LLVM/bin/llvm-rc.exe" \
      -DHAVE_ENDIAN_H=OFF
cmake --build F:/dev/shadPS4-build --target shadps4 -j 12
```

`-DHAVE_ENDIAN_H=OFF` is required: CMake's probe finds an `endian.h` on this machine, but it
is not the BSD one libressl needs, and enabling it breaks the `externals/libressl` build.

## Harness scripts

`autonomous_tools/paths.py` is the single source of truth for the paths above. The run
scripts import it, so relocating something means editing that one file.

## Running the game

`%APPDATA%\shadPS4\config.json` has `install_dirs[0].path` set to `F:\games\ps4\roms`.
