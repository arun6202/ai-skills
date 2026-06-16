---
name: idiomatic-cpp
description: >-
  Write, refactor, or review modern, type-driven C++ (C++17, C++20, C++23).
  Use this to tame the multi-paradigm complexity of C++ by sticking to a strict,
  functional-leaning subset: std::variant for sum types, std::optional over
  nullptr, std::expected over exceptions/error codes, const auto for immutability,
  and std::ranges for data pipelines. Counters the reflexes of classic C-style
  mutation, raw pointers, out-parameters, and deep OOP inheritance hierarchies.
---

# Idiomatic C++ (Modern Type-Driven C++)

C++ is a massive, multi-paradigm language that will happily let you write C-style procedural code, 90s-style deep OOP inheritance, or wild template metaprogramming. 

However, modern C++ (C++17 through C++23) has quietly added all the tools needed to write **safe, functional, type-driven code**. By restricting yourself to a specific subset of the language, you can achieve the same mathematical correctness as Rust or F#, but you have to actively enforce the discipline because the compiler won't force you by default.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Classic C++ Reflex                                   | Modern Idiomatic C++                                               |
|-----------------------------------------------------|---------------------------------------------------------------------|
| Raw pointers (`*`) and `new`/`delete`               | Stack allocation (values) or `std::unique_ptr`                      |
| `nullptr` / `NULL` checks everywhere                | `std::optional<T>`                                                  |
| Out-parameters (`bool TryGet(int* out)`)            | Return `std::optional<T>` or `std::pair`                            |
| Class inheritance for data/variants                 | `std::variant<T1, T2>` + `std::visit`                               |
| Throwing exceptions for expected errors             | `std::expected<T, E>` (C++23) or `std::variant`                     |
| Mutable `auto` or `int x = 0;`                      | `const auto` (Immutability by default)                              |
| `for` loop accumulating into a vector               | `std::ranges::views::transform` / `filter` (C++20)                  |
| `#define` macros for constants                      | `constexpr` / `consteval`                                           |
| Magic string states                                 | `enum class` or `std::variant`                                      |
| Unconstrained templates causing massive errors      | C++20 `Concepts` (e.g., `template <std::integral T>`)               |

If you genuinely need dynamic polymorphism across an unknown set of types, use virtual classes. Make it a decision, not a default.

## The C++ Creed

1. **Make illegal states unrepresentable.** Model data with `std::variant` so bad combinations can't compile. A wrong program should fail to compile.
2. **`std::optional`, never `nullptr`.** A raw pointer should only ever mean "I am observing this memory," never "this might not exist." Use `std::optional` to explicitly signal absence.
3. **`const` by default.** Bind everything as `const auto` unless you explicitly need to mutate it. The stricter the `const` correctness, the fewer the bugs.
4. **Value semantics.** Default to passing and returning by value. Let move semantics (`std::move`) and Return Value Optimization (RVO) handle the performance. Avoid heap allocations unless strictly necessary.
5. **Errors as values.** Use C++23 `std::expected<T, E>` for domain errors (like validation failures or missing files). Reserve C++ exceptions *only* for true catastrophic failure (like running out of memory).
6. **Pipelines over loops.** Use C++20 `<ranges>` to transform data rather than manually writing index loops with mutable accumulators.
7. **Exhaustive matching.** When unpacking a `std::variant`, use `std::visit` with an overloaded lambda struct. The compiler will enforce that you handle every possible type in the variant.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| "One of N shapes" / a state               | `std::variant<A, B>` + `std::visit`                              |
| A data bundle                             | `struct` with `const` fields                                     |
| "Maybe absent"                            | `std::optional<T>`                                               |
| "Succeeds or fails with a reason"         | `std::expected<T, E>` (C++23)                                    |
| Transform a collection                    | `std::views::transform` / `filter`                               |
| Constrain a template                      | C++20 `concept` and `requires` clauses                           |
| Own memory uniquely                       | `std::unique_ptr<T>`                                             |

## A taste

```cpp
#include <iostream>
#include <variant>
#include <string>

// Boilerplate needed in C++ to make std::visit elegant
template<class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template<class... Ts> overloaded(Ts...) -> overloaded<Ts...>;

// 1. Model states perfectly with std::variant (Sum Type)
struct Approved { double amount; std::string auth_code; };
struct Declined { std::string reason; };
struct Failed { std::string exception_msg; };

using PaymentResult = std::variant<Approved, Declined, Failed>;

// 2. Total function using std::visit (Compiler proves exhaustiveness)
std::string describe_payment(const PaymentResult& result) {
    return std::visit(overloaded {
        [](const Approved& a) { return "Approved: $" + std::to_string(a.amount); },
        [](const Declined& d) { return "Declined: " + d.reason; },
        [](const Failed& f)   { return "Error: " + f.exception_msg; }
    }, result);
}
```

No `new/delete`, no virtual inheritance, no pointers, no unhandled edge cases. If you add a new state to `PaymentResult`, the compiler will throw an error inside `describe_payment` until you handle it. This is the goal of Modern Idiomatic C++.
