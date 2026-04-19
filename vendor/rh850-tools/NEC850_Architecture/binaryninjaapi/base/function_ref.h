// Copyright (c) 2025-2026 Vector 35 Inc
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.

#pragma once

#include <type_traits>
#include <utility>
#include <functional>

namespace bn::base {

template <typename Sig>
class function_ref;

// A non-owning reference to a callable object, inspired by C++26's std::function_ref.
// If the callable needs to be stored or copied, use std::function instead.
template <typename R, typename... Args>
class function_ref<R(Args...)>
{
private:
    union Storage
    {
        const void* object = nullptr;
        R (*func)(Args...);
    };

    Storage m_storage;
    R (*m_invoker)(const Storage&, Args...) = nullptr;
    
    static R invoke_function(const Storage& storage, Args... args)
    {
        auto fn = storage.func;
        return fn(std::forward<Args>(args)...);
    }
    
    template <typename T>
    static R invoke_callable(const Storage& storage, Args... args)
    {
        return std::invoke(*static_cast<const T*>(storage.object), std::forward<Args>(args)...);
    }
    
public:
    function_ref() = delete;

    // Constructor that accepts a function pointer
    function_ref(R (*f)(Args...)) noexcept
        : m_storage{.func = f}
        , m_invoker(&invoke_function)
    {
    }

    // Constructor that accepts any callable object that is not function_ref
    template<typename F>
        requires (!std::is_same_v<std::remove_cvref_t<F>, function_ref>) &&
                 std::is_invocable_r_v<R, F&, Args...>
    function_ref(const F& f) noexcept
        : m_storage{.object = &f}
        , m_invoker(&invoke_callable<std::remove_cvref_t<F>>)
    {
    }
    
    R operator()(Args... args) const
    {
        return m_invoker(m_storage, std::forward<Args>(args)...);
    }

    function_ref(const function_ref&) noexcept = default;
    function_ref(function_ref&&) noexcept = default;
    function_ref& operator=(const function_ref&) noexcept = default;
    function_ref& operator=(function_ref&&) noexcept = default;
};

} // namespace bn::base
