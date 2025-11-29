# Formal Operational Semantics for StreamDataGenerator DSL

## 1. Abstract Syntax

### 1.1 Syntactic Domains

```
d ∈ Dataset
p ∈ Parameter
f ∈ Feature
t ∈ Target
φ ∈ Formula
δ ∈ Drift
v ∈ Value ::= Int | Float | String | Bool
```

### 1.2 Abstract Syntax Trees

```
Dataset ::= ⟨name: ID, desc: String?, params: Parameter*, features: Feature*, target: Target, runConfig: RunConfig?⟩

Parameter ::= ⟨name: ID, description: String⟩

Feature ::= ⟨name: ID, description: String, formula: Formula, drift: Drift?⟩

Target ::= ⟨name: ID, description: String, type: ClassType, formula: Formula, drift: Drift?⟩

ClassType ::= Binary | Scalar

Drift ::= ⟨type: ID, formulas: DriftFormula*⟩

DriftFormula ::= ⟨name: ID?, value: Formula⟩

RunConfig ::= ⟨arguments: Argument*⟩

Argument ::= ⟨name: ID, value: Value⟩

Formula ::= Expression
```

## 2. Semantic Domains

### 2.1 Environments

```
Γ ∈ Env = ID → Value          (Parameter environment)
Σ ∈ State = ID → Value        (Feature state)
Δ ∈ DriftState = ID → ℕ       (Drift function index)
```

### 2.2 Evaluation Functions

```
⟦·⟧_param : Parameter → Env → Env           (Parameter evaluation)
⟦·⟧_feat  : Feature → Env × State → Value   (Feature evaluation)
⟦·⟧_targ  : Target → Env × State → Value    (Target evaluation)
⟦·⟧_form  : Formula → Env × State → Value   (Formula evaluation)
```

## 3. Operational Semantics

### 3.1 Dataset Initialization

```
────────────────────────────────────────────────────────── [INIT]
⟨Dataset d, RunConfig r⟩ ⇒ ⟨Γ₀, Σ₀, Δ₀⟩

where:
  Γ₀ = {pᵢ.name ↦ rⱼ.value | pᵢ ∈ d.params, rⱼ ∈ r.arguments, pᵢ.name = rⱼ.name}
  Σ₀ = ∅
  Δ₀ = {v.name ↦ 0 | v ∈ (d.features ∪ {d.target}), v.drift ≠ null}
```

### 3.2 Feature Evaluation

#### 3.2.1 Feature without Drift

```
f.drift = null    ⟦f.formula⟧_form(Γ, Σ) = v
─────────────────────────────────────────────── [FEAT-NODRIFT]
⟨f, Γ, Σ⟩ ⇒ ⟨v, Σ[f.name ↦ v]⟩
```

#### 3.2.2 Feature with Drift

```
f.drift = δ    i = Δ(f.name)    δ.formulas[i] = φᵢ
⟦φᵢ.value⟧_form(Γ, Σ) = v
─────────────────────────────────────────────── [FEAT-DRIFT]
⟨f, Γ, Σ, Δ⟩ ⇒ ⟨v, Σ[f.name ↦ v], Δ⟩
```

### 3.3 Target Evaluation

#### 3.3.1 Binary Target without Drift

```
t.type = Binary    t.drift = null
⟦t.formula⟧_form(Γ, Σ) = b
─────────────────────────────────────────────── [TARGET-BIN-NODRIFT]
⟨t, Γ, Σ⟩ ⇒ if b then 1 else 0
```

#### 3.3.2 Scalar Target without Drift

```
t.type = Scalar    t.drift = null
⟦t.formula⟧_form(Γ, Σ) = v
─────────────────────────────────────────────── [TARGET-SCALAR-NODRIFT]
⟨t, Γ, Σ⟩ ⇒ v
```

#### 3.3.3 Target with Drift

```
t.drift = δ    i = Δ(t.name)    δ.formulas[i] = φᵢ
⟦φᵢ.value⟧_form(Γ, Σ) = v'
─────────────────────────────────────────────── [TARGET-DRIFT]
⟨t, Γ, Σ, Δ⟩ ⇒ ⟨v', Δ⟩

where v' = if t.type = Binary then (if v' then 1 else 0) else v'
```

### 3.4 Data Generation (Main Loop)

```
∀fᵢ ∈ d.features : ⟨fᵢ, Γ, Σᵢ₋₁, Δ⟩ ⇒ ⟨vᵢ, Σᵢ, Δ⟩
⟨d.target, Γ, Σₙ, Δ⟩ ⇒ ⟨y, Δ'⟩
─────────────────────────────────────────────── [GEN]
⟨d, Γ, Σ₀, Δ⟩ ⇒ ⟨[v₁, v₂, ..., vₙ], y, Σₙ, Δ'⟩
```

This rule generates one data instance as a tuple `([features], target)`.

### 3.5 Drift Application

```
v.drift = δ    |δ.formulas| = k
i' = select_random({0, 1, ..., k-1})    i' ≠ Δ(v.name)
─────────────────────────────────────────────── [DRIFT]
⟨drift(v.name), Δ⟩ ⇒ Δ[v.name ↦ i']
```

## 4. Formula Semantics

### 4.1 Distribution Functions

```
⟦UniformFloat(min, max)⟧_form(Γ, Σ) = 
  sample from Uniform(⟦min⟧, ⟦max⟧)

⟦UniformInteger(min, max)⟧_form(Γ, Σ) = 
  sample from DiscreteUniform(⟦min⟧, ⟦max⟧)

⟦Gaussian(μ, σ)⟧_form(Γ, Σ) = 
  sample from 𝒩(⟦μ⟧, ⟦σ⟧²)

⟦UniformCategorical(v₁, ..., vₙ)⟧_form(Γ, Σ) = 
  sample uniformly from {⟦v₁⟧, ..., ⟦vₙ⟧}
```

### 4.2 Variable References

```
x ∈ dom(Σ)
─────────────────────────────────────────────── [VAR-STATE]
⟦x⟧_form(Γ, Σ) = Σ(x)

x ∈ dom(Γ)    x ∉ dom(Σ)
─────────────────────────────────────────────── [VAR-PARAM]
⟦x⟧_form(Γ, Σ) = Γ(x)
```

### 4.3 Arithmetic Expressions

```
⟦e₁⟧_form(Γ, Σ) = v₁    ⟦e₂⟧_form(Γ, Σ) = v₂
─────────────────────────────────────────────── [ARITH]
⟦e₁ ⊕ e₂⟧_form(Γ, Σ) = v₁ ⊕ v₂

where ⊕ ∈ {+, -, *, /, **, %}
```

### 4.4 Comparison Expressions

```
⟦e₁⟧_form(Γ, Σ) = v₁    ⟦e₂⟧_form(Γ, Σ) = v₂
─────────────────────────────────────────────── [CMP]
⟦e₁ ⊙ e₂⟧_form(Γ, Σ) = v₁ ⊙ v₂

where ⊙ ∈ {<, <=, >, >=, ==, !=}
```

### 4.5 Logical Expressions

```
⟦e₁⟧_form(Γ, Σ) = b₁    ⟦e₂⟧_form(Γ, Σ) = b₂
─────────────────────────────────────────────── [LOGIC]
⟦e₁ ⊛ e₂⟧_form(Γ, Σ) = b₁ ⊛ b₂

where ⊛ ∈ {and, or}
```

### 4.6 Conditional Expressions

```
⟦c⟧_form(Γ, Σ) = true    ⟦e₁⟧_form(Γ, Σ) = v₁
─────────────────────────────────────────────── [IF-TRUE]
⟦e₁ if c else e₂⟧_form(Γ, Σ) = v₁

⟦c⟧_form(Γ, Σ) = false    ⟦e₂⟧_form(Γ, Σ) = v₂
─────────────────────────────────────────────── [IF-FALSE]
⟦e₁ if c else e₂⟧_form(Γ, Σ) = v₂
```

## 5. Type System

### 5.1 Type Judgments

```
Γ, Σ ⊢ e : τ
```

Where τ ∈ {Int, Float, Bool, String}

### 5.2 Typing Rules

```
─────────────────────────────────────────────── [T-INT]
Γ, Σ ⊢ n : Int

─────────────────────────────────────────────── [T-FLOAT]
Γ, Σ ⊢ r : Float

─────────────────────────────────────────────── [T-BOOL]
Γ, Σ ⊢ b : Bool

─────────────────────────────────────────────── [T-STRING]
Γ, Σ ⊢ s : String

x ∈ dom(Σ) ∪ dom(Γ)
─────────────────────────────────────────────── [T-VAR]
Γ, Σ ⊢ x : typeof(Σ(x)) ∨ typeof(Γ(x))

Γ, Σ ⊢ e₁ : Float    Γ, Σ ⊢ e₂ : Float
─────────────────────────────────────────────── [T-UNIFORM-FLOAT]
Γ, Σ ⊢ UniformFloat(e₁, e₂) : Float

Γ, Σ ⊢ e₁ : Int    Γ, Σ ⊢ e₂ : Int
─────────────────────────────────────────────── [T-UNIFORM-INT]
Γ, Σ ⊢ UniformInteger(e₁, e₂) : Int

Γ, Σ ⊢ e : Bool    Γ, Σ ⊢ e₁ : τ    Γ, Σ ⊢ e₂ : τ
─────────────────────────────────────────────── [T-COND]
Γ, Σ ⊢ e₁ if e else e₂ : τ
```

## 6. Well-Formedness Constraints

### 6.1 Variable Scoping

A formula φ in a feature fᵢ can reference:
1. Parameters from Γ
2. Features fⱼ where j < i (previously defined features)

A formula φ in the target can reference:
1. Parameters from Γ
2. All features in d.features

Formally:
```
FreeVars(φ) ⊆ dom(Γ) ∪ {fⱼ.name | j < i}  (for feature fᵢ)
FreeVars(φ) ⊆ dom(Γ) ∪ {f.name | f ∈ d.features}  (for target)
```

### 6.2 Drift Consistency

If a variable v has drift δ, then:
```
|δ.formulas| ≥ 1
∀φᵢ ∈ δ.formulas : typeof(⟦φᵢ.value⟧) = typeof(⟦v.formula⟧)
```

### 6.3 Target Type Consistency

For binary targets:
```
t.type = Binary ⟹ Γ, Σ ⊢ t.formula : Bool
```

For scalar targets:
```
t.type = Scalar ⟹ Γ, Σ ⊢ t.formula : Float ∨ Int
```

## 7. Example Denotational Trace

For the dataset:
```
Dataset Example {
    parameters {
        seed: "Random seed"
    }
    features {
        x: "Feature X" = UniformFloat(0, 1)
        y: "Feature Y" = 2 * x
    }
    target label: "Target" {
        type: Binary
        formula: y > x
    }
    run seed=42
}
```

Trace:
1. Initialize: `Γ₀ = {seed ↦ 42}, Σ₀ = ∅`
2. Evaluate `x`: `⟦UniformFloat(0, 1)⟧_form(Γ₀, Σ₀) = 0.37` (example)
   - Update: `Σ₁ = {x ↦ 0.37}`
3. Evaluate `y`: `⟦2 * x⟧_form(Γ₀, Σ₁) = 2 * Σ₁(x) = 0.74`
   - Update: `Σ₂ = {x ↦ 0.37, y ↦ 0.74}`
4. Evaluate target: `⟦y > x⟧_form(Γ₀, Σ₂) = 0.74 > 0.37 = true`
   - Convert: `if true then 1 else 0 = 1`
5. Output: `([0.37, 0.74], 1)`

## 8. Implementation Mapping

The DSL semantics map to Python as follows:

| DSL Construct              | Python Implementation                 |
| -------------------------- | ------------------------------------- |
| `UniformFloat(a, b)`       | `random.Random(seed).uniform(a, b)`   |
| `UniformInteger(a, b)`     | `random.Random(seed).randint(a, b)`   |
| `Gaussian(μ, σ)`           | `random.Random(seed).gauss(μ, σ)`     |
| `UniformCategorical(...)`  | `random.Random(seed).choice([...])`   |
| Feature evaluation         | Assignment in `__iter__` method       |
| Target evaluation (Binary) | Conditional assignment (0 or 1)       |
| Target evaluation (Scalar) | Direct assignment                     |
| Drift application          | Function pointer swap in drift method |
| Data generation            | Infinite generator via `yield`        |
