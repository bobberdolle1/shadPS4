// SPDX-FileCopyrightText: Copyright 2024-2026 shadPS4 Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

#include <mutex>
#include "common/types.h"

namespace Libraries::Kernel {
struct PthreadAttr;
} // namespace Libraries::Kernel

namespace Core {
#ifdef WIN32
using ThreadFunc = DWORD (*)(void*);
#else
using ThreadFunc = void* (*)(void*);
#endif

class NativeThread {
public:
    NativeThread();
    ~NativeThread();

    NativeThread(const NativeThread&) = delete;
    NativeThread& operator=(const NativeThread&) = delete;

    int Create(ThreadFunc func, void* arg);
    void Exit();
    void WaitForExit();

    void Initialize();

    uintptr_t GetHandle() {
        std::scoped_lock lock{completion_mutex};
        return reinterpret_cast<uintptr_t>(native_handle);
    }

    u64 GetTid() {
        return tid;
    }

private:
    // Create publishes completion ownership before a collector can wait for it.
    // Exit never takes this mutex: the waiter holds it until native termination.
    std::mutex completion_mutex;
#ifdef _WIN64
    void* native_handle;
    void* completion_handle = nullptr;
#else
    uintptr_t native_handle;
    void* sig_stack_ptr = nullptr;
    bool native_joinable = false;
#endif
    u64 tid = 0;
};

} // namespace Core