---
name: idiomatic-java
description: >-
  Write, refactor, or review modern, functional-leaning Java (Java 17-21+).
  Use this to break free from classic Enterprise Java (deep inheritance, massive
  service classes, null checks, and mutable beans) and embrace modern Java features:
  records, sealed interfaces for sum types, switch pattern matching, Streams, and 
  Optional. Counters the reflexes of traditional Java OOP and brings Java closer
   to the mathematical correctness of Kotlin or F#.
---

# Idiomatic Java (Modern Functional Java)

For decades, Java was the poster child for classic Object-Oriented Programming—characterized by deep inheritance hierarchies, mutable JavaBeans, pervasive `null` checks, and massive service classes.

However, starting around Java 14 and solidifying in Java 17 and 21, the language underwent a massive architectural shift. With the introduction of **records**, **sealed interfaces**, **switch pattern matching**, and **Virtual Threads**, modern Java has acquired the necessary tools to write highly robust, functional, type-driven code.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column (Classic Enterprise Java), write the right column instead.

| Classic Java Reflex                                   | Modern Idiomatic Java (17-21+)                                      |
|-------------------------------------------------------|---------------------------------------------------------------------|
| `class` with getters, setters, `equals()`, `hashCode()`| `record` (Immutability and value semantics by default)              |
| Deep class inheritance (`extends`)                    | `sealed interface` + composition (or `implements`)                  |
| `if (x instanceof Type) { Type t = (Type)x; }`        | Pattern matching: `switch (x) { case Type t -> ... }`               |
| Throwing checked exceptions for domain failures       | Returning a sealed `Result<T, E>` interface or using `Vavr`         |
| Returning `null` to indicate absence                  | Returning `Optional<T>`                                             |
| `for` loop modifying an external `List`               | `Stream.of().map().filter().toList()`                               |
| Giant `*Service` classes holding all business logic   | Small pure functions composed together                              |
| `new Thread()` or blocking `ExecutorService`          | Java 21 **Virtual Threads** (`Executors.newVirtualThreadPerTaskExecutor()`) |
| Passing primitives with rules (e.g., `String email`)  | Constrained records (`record Email(String value) { public Email { ... } }`) |

If you genuinely need encapsulated mutable state (e.g., a stateful cache) or specific framework requirements (like JPA entities requiring zero-arg constructors), use a classic `class`. Make it a decision, not a default.

## The Java Creed

1. **Make illegal states unrepresentable.** Model data using `sealed interface` (for "one of N" states) and `record` (for immutable data bundles). A wrong program should fail to compile.
2. **`Optional`, never `null`.** Never return `null`. Use `Optional<T>` to explicitly signal absence. Avoid `.get()` unless preceded by `.isPresent()`; prefer `.map()` or `.orElse()`.
3. **Immutability by default.** Bind variables as `final var`. Use `record`s to ensure data cannot be mutated after creation. If you need to "mutate", write a `.withX()` method on the record that returns a new copy.
4. **Exhaustive matching.** When unpacking a `sealed interface`, use Java 21's `switch` expression. The Java compiler will enforce that you handle every possible implementation of the sealed interface.
5. **Errors as values.** Exceptions are for system failures (database down, out of memory). For domain failures (invalid input, insufficient funds), return a custom sealed `Result<T,E>` interface (or use a library like Vavr `Either`).
6. **Pipelines over loops.** Use the `Stream` API to transform collections rather than manually writing index loops with mutable accumulators.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| A data bundle ("Product Type")            | `record Person(String name, int age) {}`                         |
| "One of N shapes" ("Sum Type")            | `sealed interface Shape permits Circle, Rect {}`                 |
| "Maybe absent"                            | `Optional<T>`                                                    |
| Constrain a primitive (e.g., Email)       | `record Email(String val) { public Email { requireValid(val); } }`|
| Transform a collection                    | `list.stream().filter(...).map(...).toList()`                    |
| Branch based on type                      | `switch (obj) { case Circle c -> ...; case Rect r -> ...; }`     |

## A taste

```java
// 1. Model states perfectly with sealed interfaces and records (Sum Type + Product Type)
public sealed interface PaymentResult permits Approved, Declined, Failed {}

public record Approved(double amount, String authCode) implements PaymentResult {}
public record Declined(String reason) implements PaymentResult {}
public record Failed(String exceptionMsg) implements PaymentResult {}

// 2. Total function using switch expressions (Compiler proves exhaustiveness)
public String describePayment(PaymentResult result) {
    return switch (result) {
        case Approved a -> "Approved: $" + a.amount() + " (Auth: " + a.authCode() + ")";
        case Declined d -> "Declined: " + d.reason();
        case Failed f   -> "Error: " + f.exceptionMsg();
        // No 'default' branch needed! The compiler knows these are the only 3 possible states.
    };
}
```

No `null` checks, no class casting (`(Approved) result`), no massive `if/else` chains, and no unhandled edge cases. If you add a new `Pending` state to `PaymentResult`, the compiler will throw an error inside `describePayment` until you handle it. This is Modern Idiomatic Java.
