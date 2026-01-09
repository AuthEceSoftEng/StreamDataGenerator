# Operational Semantics of Stream Data Generator DSL

## 1. Introduction

This document provides a formal mathematical specification of the Stream Data Generator Domain-Specific Language (SDG-DSL). The semantics are defined using denotational semantics, operational semantics, and type theory to ensure rigorous and unambiguous interpretation of DSL programs.

---

## 2. Syntax

### 2.1 Abstract Syntax

Let **ID** be the set of identifiers, **ℝ** the set of real numbers, **ℤ** the set of integers, **𝔹** = {true, false} the set of booleans, and **String** the set of strings.

#### Grammar

```
D ∈ Dataset    ::= dataset id : Desc? Params? Features Target RunConfig?
Desc           ::= description: string
Params         ::= parameters P* end
P ∈ Parameter  ::= id : string
Features       ::= features F* end
F ∈ Feature    ::= τ? id : φ (, string)? Drift?
τ ∈ Type       ::= int | float | string | bool | object
φ ∈ Formula    ::= e
T ∈ Target     ::= id : TargetType
                   description: string
                   formula: φ
                   Drift?
                   end
TargetType     ::= Binary | Float | Integer | Categorical
Drift          ::= drift id DF* end
DF ∈ DriftForm ::= τ? id : φ
RunConfig      ::= run Args
Args           ::= Arg (, Arg)*
Arg            ::= id = v
v ∈ Value      ::= n | r | string | b
                   where n ∈ ℤ, r ∈ ℝ, b ∈ 𝔹
```

#### Expression Language

```
e ∈ Expr ::= v                          (value)
           | id                         (variable reference)
           | e₁ op e₂                   (binary operation)
           | if e₁ then e₂ else e₃      (conditional)
           | f(e₁, ..., eₙ)             (function application)

op ∈ BinOp ::= + | - | * | / | < | <= | > | >= | == | != | and | or

f ∈ Function ::= UniformFloat | UniformInteger | Gaussian | UniformCategorical
```

---

## 3. Type System

### 3.1 Type Judgments

We define a type system with judgment **Γ ⊢ e : τ** meaning "in context Γ, expression e has type τ".

#### Type Rules

**[T-Var]**
```
x : τ ∈ Γ
─────────
Γ ⊢ x : τ
```

**[T-Int]**
```
n ∈ ℤ
───────────
Γ ⊢ n : int
```

**[T-Float]**
```
r ∈ ℝ
─────────────
Γ ⊢ r : float
```

**[T-Bool]**
```
b ∈ 𝔹
────────────
Γ ⊢ b : bool
```

**[T-String]**
```
s ∈ String
──────────────
Γ ⊢ s : string
```

**[T-BinOp]**
```
Γ ⊢ e₁ : τ₁    Γ ⊢ e₂ : τ₂    τ₁ ⊕ τ₂ = τ
────────────────────────────────────────────
Γ ⊢ e₁ op e₂ : τ
```

where ⊕ is the type compatibility function for binary operations.

**[T-If]**
```
Γ ⊢ e₁ : bool    Γ ⊢ e₂ : τ    Γ ⊢ e₃ : τ
──────────────────────────────────────────
Γ ⊢ if e₁ then e₂ else e₃ : τ
```

**[T-UniformFloat]**
```
Γ ⊢ e₁ : float    Γ ⊢ e₂ : float
─────────────────────────────────────
Γ ⊢ UniformFloat(e₁, e₂) : float
```

**[T-UniformInteger]**
```
Γ ⊢ e₁ : int    Γ ⊢ e₂ : int
───────────────────────────────
Γ ⊢ UniformInteger(e₁, e₂) : int
```

**[T-Gaussian]**
```
Γ ⊢ e₁ : float    Γ ⊢ e₂ : float
─────────────────────────────────
Γ ⊢ Gaussian(e₁, e₂) : float
```

**[T-UniformCategorical]**
```
Γ ⊢ e₁ : string    ...    Γ ⊢ eₙ : string
──────────────────────────────────────────
Γ ⊢ UniformCategorical(e₁, ..., eₙ) : string
```

### 3.2 Type Compatibility

The type compatibility function ⊕ : Type × Type → Type is defined as:

```
int ⊕ int = int
float ⊕ float = float
int ⊕ float = float
float ⊕ int = float
bool ⊕ bool = bool
string ⊕ string = string
τ₁ ⊕ τ₂ = ⊥  (otherwise, type error)
```

---

## 4. Denotational Semantics

### 4.1 Semantic Domains

```
⟦Dataset⟧   : Dataset → (Params → Stream)
⟦Feature⟧   : Feature → (Env → Dist(Value))
⟦Formula⟧   : Formula → (Env → Value)
⟦Target⟧    : Target → (Env → Value)
⟦Drift⟧     : Drift → (Env → List(Env → Value))
```

where:
- **Env** = ID → Value (environment mapping identifiers to values)
- **Dist(A)** = probability distribution over A
- **Stream** = ℕ → (List(Value) × Value) (infinite sequence of (features, target) pairs)

### 4.2 Expression Semantics

The semantic function ⟦·⟧ₑ : Expr → (Env → Value) is defined inductively:

**Values:**
```
⟦v⟧ₑ(ρ) = v
```

**Variables:**
```
⟦x⟧ₑ(ρ) = ρ(x)
```

**Binary Operations:**
```
⟦e₁ op e₂⟧ₑ(ρ) = ⟦e₁⟧ₑ(ρ) ⊙ ⟦e₂⟧ₑ(ρ)
```

where ⊙ is the semantic interpretation of op.

**Conditionals:**
```
⟦if e₁ then e₂ else e₃⟧ₑ(ρ) = {
    ⟦e₂⟧ₑ(ρ)  if ⟦e₁⟧ₑ(ρ) = true
    ⟦e₃⟧ₑ(ρ)  if ⟦e₁⟧ₑ(ρ) = false
}
```

**Distribution Functions:**
```
⟦UniformFloat(e₁, e₂)⟧ₑ(ρ) = sample from Uniform(⟦e₁⟧ₑ(ρ), ⟦e₂⟧ₑ(ρ))
⟦UniformInteger(e₁, e₂)⟧ₑ(ρ) = sample from DiscreteUniform(⟦e₁⟧ₑ(ρ), ⟦e₂⟧ₑ(ρ))
⟦Gaussian(μ, σ)⟧ₑ(ρ) = sample from 𝒩(⟦μ⟧ₑ(ρ), ⟦σ⟧ₑ(ρ)²)
⟦UniformCategorical(e₁,...,eₙ)⟧ₑ(ρ) = sample from Categorical({⟦eᵢ⟧ₑ(ρ) : 1/n})
```

### 4.3 Feature Semantics

For a feature **F = τ? id : φ (, desc)?**:

```
⟦F⟧(ρ) = (id, ⟦φ⟧ₑ(ρ))
```

If F has drift **drift dtype DF₁ ... DFₙ end**, then:

```
⟦F⟧ᵈʳⁱᶠᵗ(ρ, i) = (id, ⟦DFᵢ⟧ₑ(ρ))
```

where i ∈ {1, ..., n} is the current drift state.

### 4.4 Target Semantics

For a target **T = id : type description: desc formula: φ**:

```
⟦T⟧(ρ) = {
    1  if type = Binary ∧ ⟦φ⟧ₑ(ρ) = true
    0  if type = Binary ∧ ⟦φ⟧ₑ(ρ) = false
    ⟦φ⟧ₑ(ρ)  otherwise
}
```

### 4.5 Dataset Semantics

For a dataset **D = dataset id : Desc? Params? Features Target RunConfig?**:

```
⟦D⟧(params) = λn. generate(n, params)
```

where **generate : ℕ → Params → (List(Value) × Value)** is defined as:

```
generate(n, params) = 
    let ρ₀ = initialize_env(params)
    let ρₙ = ρ₀
    for each feature Fᵢ in Features:
        let (name, value) = ⟦Fᵢ⟧(ρₙ)
        ρₙ₊₁ = ρₙ[name ↦ value]
    let target_value = ⟦Target⟧(ρₙ)
    return ([ρₙ(f₁), ..., ρₙ(fₘ)], target_value)
```

---

## 4.3 Built-in runtime variables

The DSL exposes a small set of built-in runtime variables that may be referenced in feature, target, and drift formulas. These variables represent runtime state maintained by the generated generator and are read-only from the DSL perspective.

- `_instance_count` (integer)
  - Description: The zero-based index of the current instance being produced by the generator. The first yielded instance has `_instance_count == 0`.
  - Evaluation timing: When a feature or target formula is evaluated for an instance, `_instance_count` refers to the index of that instance (the generator increments its internal counter after producing the instance).
  - Runtime mapping: In generated Python code `_instance_count` is mapped to `self._instance_count`.
  - Example usage:

```
features:
    float time_of_day : (_instance_count % 96) / 96
```

  - Notes: Avoid referencing `_instance_count` inside string literals. The variable is intended for numeric calculations (indexing, periodic patterns, offsets) and is provided for convenience when expressing instance-dependent behavior.

## 5. Operational Semantics

### 5.1 Small-Step Semantics

We define a small-step operational semantics using configurations **⟨e, ρ, σ⟩** where:
- **e** is the expression being evaluated
- **ρ** is the environment (variable bindings)
- **σ** is the random state (seed)

The transition relation **→** is defined by the following rules:

**[E-Var]**
```
⟨x, ρ, σ⟩ → ⟨ρ(x), ρ, σ⟩
```

**[E-BinOp]**
```
⟨e₁ op e₂, ρ, σ⟩ → ⟨v₁ ⊙ v₂, ρ, σ⟩
    where ⟨e₁, ρ, σ⟩ →* ⟨v₁, ρ, σ⟩
    and   ⟨e₂, ρ, σ⟩ →* ⟨v₂, ρ, σ⟩
```

**[E-If-True]**
```
⟨if true then e₂ else e₃, ρ, σ⟩ → ⟨e₂, ρ, σ⟩
```

**[E-If-False]**
```
⟨if false then e₂ else e₃, ρ, σ⟩ → ⟨e₃, ρ, σ⟩
```

**[E-UniformFloat]**
```
⟨UniformFloat(v₁, v₂), ρ, σ⟩ → ⟨r, ρ, σ'⟩
    where (r, σ') = random_uniform_float(v₁, v₂, σ)
```

**[E-UniformInteger]**
```
⟨UniformInteger(v₁, v₂), ρ, σ⟩ → ⟨n, ρ, σ'⟩
    where (n, σ') = random_uniform_int(v₁, v₂, σ)
```

### 5.2 Big-Step Semantics

The big-step evaluation relation **⇓** is defined as:

```
ρ, σ ⊢ e ⇓ v, σ'
```

meaning "in environment ρ with random state σ, expression e evaluates to value v with new state σ'".

**[B-Value]**
```
ρ, σ ⊢ v ⇓ v, σ
```

**[B-Var]**
```
ρ, σ ⊢ x ⇓ ρ(x), σ
```

**[B-BinOp]**
```
ρ, σ ⊢ e₁ ⇓ v₁, σ₁    ρ, σ₁ ⊢ e₂ ⇓ v₂, σ₂
──────────────────────────────────────────
ρ, σ ⊢ e₁ op e₂ ⇓ v₁ ⊙ v₂, σ₂
```

**[B-If-True]**
```
ρ, σ ⊢ e₁ ⇓ true, σ₁    ρ, σ₁ ⊢ e₂ ⇓ v, σ₂
────────────────────────────────────────────
ρ, σ ⊢ if e₁ then e₂ else e₃ ⇓ v, σ₂
```

**[B-If-False]**
```
ρ, σ ⊢ e₁ ⇓ false, σ₁    ρ, σ₁ ⊢ e₃ ⇓ v, σ₂
──────────────────────────────────────────────
ρ, σ ⊢ if e₁ then e₂ else e₃ ⇓ v, σ₂
```

---

## 6. Drift Semantics

### 6.1 Drift State Machine

A dataset with drift is modeled as a state machine:

```
State = (ρ : Env, δ : DriftState)
DriftState = Feature → ℕ
```

where **DriftState** maps each driftable feature to its current drift formula index.

### 6.2 Drift Transitions

The drift transition function **drift : State → Feature → State** is defined as:

```
drift((ρ, δ), f) = (ρ, δ')
    where δ'(f) = (δ(f) + 1) mod |formulas(f)|
          δ'(g) = δ(g) for g ≠ f
```

### 6.3 Concept Drift

For concept drift on the target variable:

```
concept_drift((ρ, δ)) = (ρ, δ')
    where δ'(target) = (δ(target) + 1) mod |formulas(target)|
```

---

## 7. Correctness Properties

### 7.1 Type Safety

**Theorem (Type Preservation):** If **Γ ⊢ e : τ** and **ρ, σ ⊢ e ⇓ v, σ'**, then **v : τ**.

**Proof Sketch:** By structural induction on the derivation of **Γ ⊢ e : τ**.

### 7.2 Determinism (modulo randomness)

**Theorem (Deterministic Evaluation):** For any expression **e**, environment **ρ**, and random state **σ**, there exists a unique **v** and **σ'** such that **ρ, σ ⊢ e ⇓ v, σ'**.

**Proof Sketch:** By induction on the structure of **e**, showing that each evaluation rule is deterministic given the random state.

### 7.3 Termination

**Theorem (Strong Normalization):** For any well-typed expression **e** and environment **ρ**, the evaluation **ρ, σ ⊢ e ⇓ v, σ'** terminates.

**Proof Sketch:** The DSL does not support recursion or unbounded loops. All expressions have finite depth, ensuring termination.

---

## 8. Probabilistic Semantics

### 8.1 Probability Measures

Let **(Ω, ℱ, ℙ)** be a probability space where:
- **Ω** is the sample space (all possible random outcomes)
- **ℱ** is the σ-algebra of events
- **ℙ** is the probability measure

### 8.2 Distribution Semantics

Each distribution function induces a probability measure:

**Uniform Distribution:**
```
UniformFloat(a, b) ~ U(a, b)
ℙ(X ∈ [c, d]) = (d - c) / (b - a)  for c, d ∈ [a, b]
```

**Discrete Uniform:**
```
UniformInteger(a, b) ~ DiscreteUniform(a, b)
ℙ(X = k) = 1 / (b - a + 1)  for k ∈ {a, ..., b}
```

**Gaussian Distribution:**
```
Gaussian(μ, σ) ~ 𝒩(μ, σ²)
ℙ(X ∈ [a, b]) = ∫ₐᵇ (1/(σ√(2π))) exp(-(x-μ)²/(2σ²)) dx
```

**Categorical Distribution:**
```
UniformCategorical(v₁, ..., vₙ) ~ Categorical({vᵢ : 1/n})
ℙ(X = vᵢ) = 1/n  for i ∈ {1, ..., n}
```

### 8.3 Independence

Features are generated independently given the environment:

```
ℙ(F₁ = v₁, ..., Fₙ = vₙ | ρ) = ∏ᵢ ℙ(Fᵢ = vᵢ | ρ)
```

---

## 9. Code Generation Semantics

### 9.1 Translation Function

The code generation is formalized as a translation function:

```
⟦·⟧ᶜᵒᵈᵉ : Dataset → PythonCode
```

This function preserves the operational semantics:

**Theorem (Semantic Preservation):** For any dataset **D** and parameters **p**:

```
⟦D⟧(p) ≡ execute(⟦D⟧ᶜᵒᵈᵉ, p)
```

where **≡** denotes observational equivalence (same probability distributions over outputs).

---

## 10. References

1. Pierce, B. C. (2002). *Types and Programming Languages*. MIT Press.
2. Plotkin, G. D. (2004). *A Structural Approach to Operational Semantics*. Journal of Logic and Algebraic Programming.
3. Goodman, N. D., & Stuhlmüller, A. (2014). *The Design and Implementation of Probabilistic Programming Languages*.