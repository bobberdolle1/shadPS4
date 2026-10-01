// SPDX-FileCopyrightText: Copyright 2024-2026 shadPS4 Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include "common/alignment.h"
#include "common/arch.h"
#include "core/libraries/kernel/threads/pthread.h"
#include "thread.h"
#ifdef _WIN64
#include <windows.h>
#include "common/ntapi.h"
#else
#include <csignal>
#include <pthread.h>
#include <unistd.h>
#ifdef ARCH_X86_64
#include <xmmintrin.h>
#endif
#endif

namespace Core {

static constexpr u32 ORBIS_MXCSR = 0x9fc0;
static constexpr u32 ORBIS_FPUCW = 0x037f;

NativeThread::NativeThread() : native_handle{0} {}

NativeThread::~NativeThread() {
    WaitForExit();
}

int NativeThread::Create(ThreadFunc func, void* arg) {
    std::scoped_lock lock{completion_mutex};
    ASSERT_MSG(!native_handle, "Native thread already owns a completion handle");
#ifndef _WIN64
    pthread_t thread{};
    const int result = pthread_create(&thread, nullptr, func, arg);
    if (result == 0) {
        native_handle = static_cast<uintptr_t>(thread);
        native_joinable = true;
    }
    return result;
#else
    const auto handle = CreateThread(nullptr, 0, func, arg, 0, nullptr);
    if (handle == nullptr) {
        return GetLastError();
    }
    native_handle = handle;
    completion_handle = handle;
    return 0;
#endif
}

void NativeThread::WaitForExit() {
    std::scoped_lock lock{completion_mutex};
#ifdef _WIN64
    if (completion_handle) {
        ASSERT_MSG(WaitForSingleObject(completion_handle, INFINITE) == WAIT_OBJECT_0,
                   "Unable to wait for native thread completion: {}", GetLastError());
        CloseHandle(completion_handle);
        completion_handle = nullptr;
        native_handle = nullptr;
    }
#else
    if (native_joinable) {
        const int result = pthread_join(static_cast<pthread_t>(native_handle), nullptr);
        ASSERT_MSG(result == 0, "Unable to join native thread: {}", result);
        native_joinable = false;
        native_handle = 0;
    }
#endif
}

void NativeThread::Exit() {
    // Do not inspect or clear the completion handle here. Create may still be publishing it,
    // and a collector must retain ownership until the OS observes this thread's termination.
    tid = 0;

#ifdef _WIN64
    ExitThread(0);
#else
    // Disable and free the signal stack.
    constexpr stack_t sig_stack = {
        .ss_flags = SS_DISABLE,
    };
    sigaltstack(&sig_stack, nullptr);

    if (sig_stack_ptr) {
        free(sig_stack_ptr);
        sig_stack_ptr = nullptr;
    }
    pthread_exit(nullptr);
#endif
}

void NativeThread::Initialize() {
#ifdef ARCH_X86_64
    // Set MXCSR and FPUCW registers to the values used by Orbis.
    _mm_setcsr(ORBIS_MXCSR);
    asm volatile("fldcw %0" : : "m"(ORBIS_FPUCW));
#endif
#if _WIN64
    tid = GetCurrentThreadId();
#else
    tid = (u64)pthread_self();

    // Set up an alternate signal handler stack to avoid overflowing small thread stacks.
    const size_t page_size = getpagesize();
    const size_t sig_stack_size = Common::AlignUp(std::max<size_t>(64_KB, MINSIGSTKSZ), page_size);
    ASSERT_MSG(posix_memalign(&sig_stack_ptr, page_size, sig_stack_size) == 0,
               "Failed to allocate signal stack: {}", errno);

    stack_t sig_stack;
    sig_stack.ss_sp = sig_stack_ptr;
    sig_stack.ss_size = sig_stack_size;
    sig_stack.ss_flags = 0;
    ASSERT_MSG(sigaltstack(&sig_stack, nullptr) == 0, "Failed to set signal stack: {}", errno);
#endif
}

} // namespace Core
