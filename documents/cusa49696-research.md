<!--
SPDX-FileCopyrightText: 2026 shadPS4 Emulator Project
SPDX-License-Identifier: GPL-2.0-or-later
-->

# CUSA49696 research notes — My First Gran Turismo v01.01

Subject: `CUSA49696` (*My First Gran Turismo*), base PKG + update, extracted with the
ShadPs4Plus PKG Extractor 1.1 into `roms/CUSA49696` and `roms/CUSA49696-patch`. A third
`Backport/CUSA49696_(1.01)_9.00.pkg` exists in the source set and was **deliberately not
used**; nothing from the patch tree was copied over the base tree by hand.

This document records what works, what does not, and what was measured, so the work can be
picked up later without repeating it.

---

## Current capabilities

The title boots, reaches the menus, and reaches a race. Confirmed working:

- title screen, menus, track flyover, race start;
- sky with clouds, tree/vegetation geometry with textures, asphalt and markings, lighting
  and shadows, UI text;
- no crashes in the last verified runs (0 unhandled exceptions, 0 failed assertions).

## Current broken rendering

Large surfaces render as flat untextured white or grey, and UI panels draw over empty
geometry (text is visible but its background is missing). Streaked/shaded banding artefacts
appear on some ground surfaces — a separate, uninvestigated issue that looks like UV
interpolation rather than descriptor resolution.

Crashes are fixed; the texture loss is **not**. It is the main open item.

## Measured performance

| Scene | FPS |
|---|---|
| Menus / track flyover | 22–28 |
| In race | ~6.5 |

The menus figure was ~5 before the DMA-sync work. `SynchronizeDmaBuffers` was walking all
5390 mapped guest ranges and 65293 cached blocks on every DMA draw; it now only processes
what the CPU actually wrote, via a dirty log (commits `4fafc362`, `9e6364dd`). The in-race
figure is unchanged and is the dominant remaining bottleneck. After that fix, DMA sync is
~60% of the race frame; the other ~40% has not been profiled.

Note that the game also moved from a SATA HDD to an NVMe SSD during this work. The
contribution of the code change and the drive change was not isolated.

## Root-cause research: the crash chain

This was found and fixed, and it is the reason textures were being lost in the first place.

```
SRT walker cannot compute a descriptor offset (Phi)
  -> the descriptor slot is never written
  -> the later read falls through to flatbuf[0], which is a live shader SGPR
  -> "T#" strings in the UI are shader uniforms, not a texture id
  -> an SGPR holding 1.0f yields address 0x3f80000000
  -> that descriptor decodes to layers = 32768
  -> image.cpp walks 32768 subresources and writes past the end  -> 0xC0000005
```

Fixed in two parts:

- `f39a160e` — zero the flattened-userdata buffer before running the walker, so a slot the
  walker cannot resolve reads as a null descriptor instead of a previous dispatch's
  contents; and bound the barrier loop by the real subresource count rather than the
  descriptor's claim.
- `ae26c3ee` — opt-in provenance dump for rejected texture descriptors, which is what made
  the chain above visible.

## Root-cause research: why textures are still missing

`ComputeOffset` in `src/shader_recompiler/ir/passes/flatten_extended_userdata_pass.cpp`
compiles an IR expression tree into x86 that computes a descriptor's byte offset into the
SRT buffer. It is evaluated **once, statically, when the walker is generated**.

Two unsupported opcodes reach it:

| Opcode | Hits per run | Meaning |
|---|---|---|
| `IR::Opcode::Phi` | 6580 | merge of two control-flow-dependent values |
| `IR::Opcode::GetAttributeU32` | 65 | **index taken from a vertex attribute** |

`GetAttributeU32` is the blocker. The descriptor index varies per vertex, so no static
arithmetic can fold it — the offset is only known at draw time. Supporting `Phi` would not
help, because the same applies once the value is threaded through real control flow.

How much this costs was measured by adding per-shader counters around `ComputeOffset`
(commit `650d0db1`):

| Offsets failed | Log lines |
|---|---|
| 21% | 12 |
| **22%** | **2157** |
| 23% | 1087 |
| 24–25% | 742 |
| 26% | 719 |
| 27–28% | 718 |
| 33% | 359 |

**Roughly 22% of descriptor offsets fail on every shader**, with no shader near 0% or near
100%. That is enough to explain what is on screen: statically-indexed descriptors (sky,
trees, road) resolve, dynamically-indexed ones do not.

The consequence is that **this cannot be fixed with a small patch to `ComputeOffset`**. It
requires moving descriptor reads to the GPU for the affected shaders, which is the work
that was queued when this archive was made.

### How the flatten path actually fits together

Mapped after the archive was published; worth recording because it corrects two earlier
conclusions. All paths relative to the repository root.

Descriptor dwords are copied on the **host**, at compile time, into
`Shader::Info::flattened_ud_buf`, by an x86-64 "walker" emitted into a global arena
(`flatten_extended_userdata_pass.cpp:32,43-47`). Its signature is
`void PS4_SYSV_ABI (*)(const u32* user_data, u32* flat_dst)` (`ir/passes/srt.h:16`) — so
**`rdi` is `user_data` and `rsi` is the flat destination**. It is invoked from
`Info::RefreshFlatBuf()` (`info.h:167-183`), which memsets the buffer, copies live
user_data, then calls `srt_info.walker_func(user_data, flat_dst)`.

Each `ReadConst` then carries its assigned flat slot **baked into its flags** as a
compile-time-constant dword offset, and **slot 0 means "unresolved"**. The end of the chain:

```
scalar_memory.cpp:43-87   S_LOAD_DWORD / S_BUFFER_LOAD_DWORD
                          index = Imm32 | ShiftRightLogical(GetScalarReg(off_sgpr), 2)
resource_discover_pass.cpp:244-352   records the descriptor, tags bindless producers
flatten_extended_userdata_pass.cpp   builds the host walker, assigns flat slots
resource_patching_pass.cpp:164-203   SharpReference -> SharpFetch<T>{offsets, immediates}
emit_spirv_context_get_set.cpp:54-60 flatbuf_off_dw == 0 ? read_const_dynamic
                                                          : EmitFlatbufferLoad(const)
vk_rasterizer.cpp:731-737            uploads flattened_ud_buf as the Flatbuf SSBO
resource.h:96-215 / vk_rasterizer    SharpFetch::Fetch -> real Vulkan images/samplers
```

Two corrections to what this document previously said:

1. **`read_const_dynamic` already exists** (`spirv_emit_context.cpp:1246`, registered at
   `:1273-1297`). It is already the fallback for unresolved slots, so "build GPU-side
   descriptor reads" was the wrong framing — the GPU path is present. The open question is
   why the fallback does not yield valid descriptors for these shaders. Unresolved slots
   degrade to the BDA path or to `SharpFetch::summary == Invalid`, i.e. a null Vulkan
   descriptor, which is the missing texture.
2. There is **no `FlattenedUserData` struct** in the tree. `srt.h` holds only
   `PersistentSrtInfo` (`{walker_func, walker_func_size, flattened_bufsize_dw = 16}`, lines
   19-33) and the `PFN_SrtWalker` typedef.

### Two concrete leads, in order of cost

**A. Reorder the passes — cheap, and it may remove most of the `Phi` load.**
`recompiler.cpp` runs them in this order: `ResourceDiscoverPass` (109),
`FlattenExtendedUserdataPass` (110), `ResourcePatchingPass` (112),
`PhiSimplificationPass` (117), `LowerPhisToRegsPass` (126), `CollectShaderInfoPass` (143).
**The flatten pass runs before the two Phi passes.** So the walker is asked to resolve
values while Phis are still live in the IR. Running the flatten after
`LowerPhisToRegsPass` — or at least letting those passes simplify the offset expression
first — could collapse a large share of the 6580 `Phi` hits with no new infrastructure at
all. This should be tried before anything else; it is the cheapest thing on the list and
the hypothesis is well supported by the pass ordering.

**B. `GetAttributeU32` is the real floor.** Whatever is done about `Phi`, an index taken
from a vertex attribute still cannot be folded statically. That one genuinely needs the
GPU-side window read.

### Two side notes for whoever continues

- `SrtGvnTable::IsArgHashInst` (`ir/srt_gvn_table.h:41-58`) whitelists exactly the sixteen
  opcodes `ComputeOffset` supports. Anything outside that set gets a fresh value number
  and is never deduplicated. **Any opcode added to `ComputeOffset` must be added here too**,
  or the dedup assumptions silently diverge.
- There are **two** failure sites, not one. The inner one is `ComputeOffset` returning
  false; the outer one is `PushPtr` (line 604), which leaves `rdi` pushed and half-emitted
  code in the stream when the inner call fails. That is a stack imbalance in the emitted
  walker and is worth auditing independently of the descriptor problem.
- The walker is serialised raw and re-registered on load
  (`vk_pipeline_serialization.cpp:425-446`), so any change to emitted code needs the
  pipeline cache invalidated or stale walkers will keep running.

## Relation to nikmparis217-ux/shadPS4

The GT7 research tree at `github.com/nikmparis217-ux/shadPS4` is where the mechanism for
the remaining problem lives. Its SRT walker does not resolve a single offset at generation
time; instead it **copies a window of descriptors into a flat buffer** and lets the shader
read that window with a runtime index — base and size both taken from userdata, with
flags in the upper bits (`CopyDynrCnWindwClamped`, and the related `CopyDynrWindwCntrctv`
mixing step).

Pieces from that tree have already been ported here, including the `tile_manager`
soft-clamp work (commit `41da2ad1`) and the `SRT provenance` tracking. The conclusion
reached in this fork is that its window-copy approach is not optional for CUSA49696: it is
the only mechanism that can produce a per-vertex descriptor index.

A note on earlier reasoning, since it cost time: the window was at one point dismissed
because descriptors are resolved CPU-side in this tree. That was true and misleading —
CPU-side resolution is precisely why per-vertex indices cannot work.

## Dead ends — do not repeat

- **The SRT walker window alone.** It fixes GPU-side reads, but in this tree images are
  resolved CPU-side at bind time, so a window changes nothing on its own.
- **Patching `ComputeOffset` for `Phi`.** Superset of a real problem, but `GetAttributeU32`
  makes static resolution impossible regardless.
- **Inferring state from harness screenshots.** The harness spams Enter/X/Space every two
  seconds, which drives the game into transitions it does not finish, producing black
  frames and garbage geometry that do not occur in normal play. Two wrong conclusions came
  from this: a phantom DMA-sync regression, and a phantom input-hook regression.
- **Automated input as a substitute for the user.** The user is the tester.

Also investigated and **ruled out**: the host PC crashes (`0xD1`,
`DRIVER_IRQL_NOT_LESS_OR_EQUAL`, dated before this work began) are a driver fault, not an
emulator fault. They stopped after a driver update.

## Reproducing the measurements

Paths come from `autonomous_tools/paths.py`, which reads `SHADPS4_REPO`, `SHADPS4_BUILD`,
`SHADPS4_EBOOT` and `SHADPS4_USERDATA`, and otherwise derives defaults from its own
location.

```sh
# boot the game and capture PNGs on a schedule
python autonomous_tools/race_capture.py <out-dir> <seconds>

# per-thread CPU time
pwsh -File autonomous_tools/thread_cpu.ps1 -Seconds 60
```

Descriptor-offset failure rates are logged by `ComputeOffset` itself; the per-shader
percentage appears in the `Unexpected instruction for offset computation` line.

`autonomous_logs/` holds per-run captures and is gitignored — it is large (multi-GB) and is
regenerated rather than shared.

## Tags

| Tag | Commit | State |
|---|---|---|
| `cusa49696-first-race` | `51a08a61` | first race reached |
| `cusa49696-perf-27fps` | `9e6364dd` | DMA-sync performance work |
| `cusa49696-final-research` | final | archived state, descriptor root cause measured |