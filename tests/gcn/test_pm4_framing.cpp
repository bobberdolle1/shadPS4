// SPDX-FileCopyrightText: Copyright 2026 shadPS4 Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include <array>
#include <gtest/gtest.h>

#include "video_core/amdgpu/pm4_cmds.h"

namespace {
using AmdGpu::PM4Header;
using AmdGpu::PM4ItOpcode;
using AmdGpu::PM4PacketFramer;

TEST(Pm4Framing, ThreeFragmentsDoNotTurnNopPayloadIntoCommands) {
    // Eight-word NOP followed by SET_SH_REG. Payload deliberately resembles invalid headers.
    const std::array<u32, 11> stream{0xc0061000, 0, 0x40000000, 0xffffffff, 0x10, 0xa, 0, 0,
                                     0xc0017600, 0x240, 0x12345678};
    PM4PacketFramer framer;
    const auto first = framer.Read(std::span{stream}.first(2));
    ASSERT_TRUE(first.words.empty());
    const auto second = framer.Read(std::span{stream}.subspan(2, 2));
    ASSERT_TRUE(second.words.empty());
    const auto third = framer.Read(std::span{stream}.subspan(4));
    ASSERT_EQ(third.words.size(), 8);
    EXPECT_EQ(PM4Header{.raw = third.words.front()}.type3.opcode, PM4ItOpcode::Nop);
    ASSERT_EQ(third.consumed_dwords, 4);
    const auto next = framer.Read(std::span{stream}.subspan(4 + third.consumed_dwords));
    ASSERT_EQ(next.words.size(), 3);
    EXPECT_EQ(PM4Header{.raw = next.words.front()}.type3.opcode, PM4ItOpcode::SetShReg);
}

TEST(Pm4Framing, TerminalType2DoesNotConsumeNextSubmissionHeader) {
    const std::array<u32, 1> padding{0x80000000};
    const std::array<u32, 3> registers{0xc0017600, 0x240, 1};
    PM4PacketFramer framer;
    const auto pad = framer.Read(padding);
    ASSERT_EQ(pad.words.size(), 1);
    ASSERT_EQ(pad.consumed_dwords, 1);
    const auto next = framer.Read(registers);
    ASSERT_EQ(next.words.size(), 3);
    EXPECT_EQ(PM4Header{.raw = next.words.front()}.type3.opcode, PM4ItOpcode::SetShReg);
}

TEST(Pm4Framing, IndirectPaddingDoesNotCompletePendingRingPacket) {
    const std::array<u32, 4> ring{0xc0023f02, 0x2046b528, 0x10, 0x01800157};
    const std::array<u32, 1> indirect_padding{0x80000000};
    PM4PacketFramer framer;
    ASSERT_TRUE(framer.Read(std::span{ring}.first(2)).words.empty());
    ASSERT_EQ(PM4PacketFramer::ReadComplete(indirect_padding).consumed_dwords, 1);
    const auto completed = framer.Read(std::span{ring}.subspan(2));
    ASSERT_EQ(completed.words.size(), 4);
    EXPECT_EQ(PM4Header{.raw = completed.words.front()}.type3.opcode, PM4ItOpcode::IndirectBuffer);
    EXPECT_EQ(completed.consumed_dwords, 2);
}

TEST(Pm4Framing, MaximumPacketPreservesFollowingPacketBoundary) {
    std::array<u32, PM4PacketFramer::MaxPacketDwords + 3> stream;
    stream.fill(0x40000000);
    stream[0] = 0xfffe1000;
    stream[PM4PacketFramer::MaxPacketDwords] = 0xc0017600;
    stream[PM4PacketFramer::MaxPacketDwords + 1] = 0x240;
    stream[PM4PacketFramer::MaxPacketDwords + 2] = 1;
    PM4PacketFramer framer;
    u32 offset = 0;
    while (offset < PM4PacketFramer::MaxPacketDwords - 17) {
        const u32 count = std::min<u32>(127, PM4PacketFramer::MaxPacketDwords - 17 - offset);
        const auto partial = framer.Read(std::span{stream}.subspan(offset, count));
        ASSERT_TRUE(partial.words.empty());
        offset += partial.consumed_dwords;
    }
    const auto completed = framer.Read(std::span{stream}.subspan(offset));
    ASSERT_EQ(completed.words.size(), PM4PacketFramer::MaxPacketDwords);
    offset += completed.consumed_dwords;
    const auto next = framer.Read(std::span{stream}.subspan(offset));
    ASSERT_EQ(next.words.size(), 3);
    EXPECT_EQ(PM4Header{.raw = next.words.front()}.type3.opcode, PM4ItOpcode::SetShReg);
}
} // namespace
