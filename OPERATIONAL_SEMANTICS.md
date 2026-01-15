# Operational Semantics

This is a single, compact, authoritative reference for implementers and readers,
kept up to date when the language or generator behavior changes.

## Syntax at a glance
- dataset NAME ... `end_dataset`
- parameters: `parameters ... end_parameters` (key: description)
- features: `type name: formula[, "Description"]` ... `end_features` (types: `int`, `float`, `string`, `bool`)
- target: `target name:ClassType` then `description:` / `formula:` ... `end_target` (ClassType is an identifier; common values: `Binary`, `Float`, `Integer`, `Categorical`, `Scalar`)
- drifts: `drifts` ... `end_drifts` with `drift on <variable>` ... `end_drift`
- distributions: `UniformFloat(a,b)`, `UniformInteger(a,b)`, `Gaussian(mu,sigma)`, `UniformCategorical(v1,...)`

## Evaluation model (what to expect)
- Per instance: evaluate features in declaration order; each result stored in `features_dict`.
- After all features, evaluate target using `features_dict`.
- Binary target → `1 if (boolean_expr) else 0`.
- Drifts: each driftable variable has scenario indices; scenario 0 = default. Generator activates scenarios per drift type.
- `_instance_count` is incremented after producing an instance (zero-based).

## Logic (brief formalization)

1) Abstract syntax
- Let I be identifiers, E be Python-compatible expressions (formulas), V primitive values.
- Dataset D ::= ⟨id, Desc?, P*, F*, T?, Δ*⟩
- Parameter p ::= ⟨id, v ∈ V⟩
- Feature f ::= ⟨τ ∈ {int,float,bool,str}, id, φ ∈ E⟩
- Target t ::= ⟨id, type ∈ ID, φ ∈ E⟩  # common types: Binary, Float, Integer, Categorical, Scalar
- Drift δ ::= ⟨id ∈ I, types ⊆ {sudden,gradual,incremental,recurring}, Φ ∈ E^n⟩

2) Semantic domain (state)
- State S = ⟨κ, Σ, Ω, Δσ⟩ where
  - κ ∈ ℕ: instance counter (`_instance_count`)
  - Σ: I → V: environment (params + feature values)
  - Ω: PRNG state
  - Δσ: I → DriftMeta (start t_s, active index j, progress α)

3) Evaluation function
- V(φ, Σ, Ω) evaluates expression φ under Σ with RNG Ω and returns a pair (v, Ω').

4) Feature evaluation (value v_i for feature f_i)
- Evaluate formulas by pairing returned values and threading the PRNG state. Informally:
  - If a drift scenario j is active (sudden/recurring):
    - let (v_j, Ω1) = V(Φ_{f_i}[j], Σ, Ω)
    - v_i = v_j and Ω := Ω1
  - If incremental/gradual with progress α ∈ [0,1]:
    - let (v_def, Ω1) = V(φ_i, Σ, Ω)
    - let (v_j, Ω2) = V(Φ_{f_i}[j], Σ, Ω1)
    - v_i = (1-α) * v_def + α * v_j and Ω := Ω2
  - Otherwise (default):
    - let (v_def, Ω1) = V(φ_i, Σ, Ω)
    - v_i = v_def and Ω := Ω1
- Note: Σ is extended only after v_i is computed (i.e., features are appended to the environment in declaration order).

5) Target evaluation
- After computing Σ_final with all features:
  - let (v_t, Ω1) = V(φ_target, Σ_final, Ω)
  - If Target.type = Binary: y = 1 if v_t is true else 0, and set Ω := Ω1
  - Else: y = v_t, and set Ω := Ω1

6) Transition (produce one instance)
- For features f_1..f_n evaluated in order producing v_1..v_n, and target y:
  - the PRNG Ω is threaded through each feature evaluation and the target evaluation; let Ω' be the final PRNG state after the last evaluation.
  - ⟨κ, Σ, Ω, Δσ⟩ --next--> ⟨(v_1..v_n), y⟩ ⊢ ⟨κ+1, Σ', Ω', Δσ'⟩
  where Σ' = Σ_params ∪ {f_i ↦ v_i} and Ω' is the final PRNG state after all samplings.

7) State updates (rules)
- κ' = κ + 1
- Ω' is the final PRNG state after all sampling calls (as threaded above)
- Recurring drift removal: if (κ - t_s) ≥ duration then remove/disable that drift entry
- Gradual progress α = min(1, (κ - t_s)/steps) for interpolation or probabilistic switching

8) Constraints (must hold)
- Acyclic dependency: each feature's formula may reference parameters and earlier features only.
- Scenario safety: requested scenario indices j must satisfy 0 ≤ j < len(Φ_x).
- Type soundness: value returned by V must be compatible with declared feature type τ.

## Minimal example (intent)

DSL:
```
dataset LoanGen
  parameters
    seed: "The seed"
  end_parameters
  features
    int age: UniformInteger(20,80)
    float salary: UniformFloat(20000,150000)
  end_features
  target approved:Binary
    description: "Loan approval"
    formula: age < 25 and salary >= 50000
  end_target
end_dataset
```

Intent (generated):
```
# conceptual generated code for one instance
features_dict = {}
# feature `int age: UniformInteger(20,80)`
features_dict['age'] = self._rng.randint(20, 80)
# feature `float salary: UniformFloat(20000,150000)`
features_dict['salary'] = self._rng.uniform(20000, 150000)
# target `approved:Binary` -> binary mapping
return 1 if (features_dict['age'] < 25 and features_dict['salary'] >= 50000) else 0
```

Change log
- 2026-01-15: Aligned cheat-sheet with grammar and examples; kept concise.