# Operational Semantics
This is a single, compact, authoritative reference for implementers and readers,
which must be kept up to date when the language or generator behavior changes.

## Syntax at a glance
- Dataset definition: `dataset <name>` ... `end_dataset`
- Parameters: `parameters` ... `end_parameters` --> `key: "description"`
- Features: `features` ... `end_features` --> `[type] name: formula[, "desc"]` (type can be: `int`, `float`, `string`, `bool`)
- Target: `target <name>: <ClassType>` ... `end_target` --> description and formula (ClassType can be: `Binary`, `Categorical`, `Scalar`)
- Drifts: `drifts` ... `end_drifts` --> drift section with:
  - Drift: `drift on <variable>` ... `end_drift` --> drift definition (drift type can be `sudden`, `gradual`, `incremental`, `recurring`), with:
    - Scenarios: `scenarios` ... `end_scenarios` --> drift condition formulas

Valid formulas include python expressions (possibly referencing parameters and previously defined features) and calls to supported distributions: `UniformFloat(a,b)`, `UniformInteger(a,b)`, `Gaussian(mu,sigma)`, `UniformCategorical(v1,...)`.

## Evaluation model
- Per instance: evaluate features in declaration order; each result stored in `features_dict`.
- After all features, evaluate target using `features_dict`.
- Binary target → `1 if (boolean_expr) else 0`.
- Drifts: each driftable variable has scenario indices; scenario 0 = default. Generator activates scenarios per drift type.
- `_instance_count` is incremented after producing an instance (zero-based).

## Formal specification
1) Abstract syntax
- Let I be identifiers, E be Python-compatible expressions (formulas), V primitive values.
- Dataset D ::= ⟨id, Desc?, P*, F*, T?, Δ*⟩
- Parameter p ::= ⟨id, v ∈ V⟩
- Feature f ::= ⟨τ ∈ {int,float,bool,str}, id, φ ∈ E⟩
- Target t ::= ⟨id, type ∈ ID, φ ∈ E⟩  # common types: Binary, Float, Integer, Categorical, Scalar
- Drift δ ::= ⟨id ∈ I, types ⊆ {sudden,gradual,incremental,recurring}, Φ ∈ E^n⟩

Note: formulas are Python-compatible expressions and may call standard library functions (for example, `math.sin`, `math.exp`).

2) Semantic domain (state)
- State S = ⟨κ, Σ, Ω, Δσ⟩ where
  - κ ∈ ℕ: instance counter (`_instance_count`)
  - Σ: I → V: environment (params + feature values)
  - Ω: PRNG state
  - Δσ: I → DriftMeta (start t_s, active index j, progress α)

3) Evaluation function
- V(φ, Σ) evaluates expression φ under environment Σ and returns a value v. Distribution and randomness are produced by calls to the generator's PRNG `self._rng` inside the generated code; the runtime PRNG state is not threaded through evaluation steps in the specification (implementations use `self._rng` internally).

4) Feature evaluation (value v_i for feature f_i)
- Evaluate formulas using the generated evaluation `V(φ, Σ)` which returns a value; randomness inside formulas is produced by `self._rng` calls emitted by the generator. Informally:
  - If a drift scenario j is active (sudden/recurring):
    - v_i = V(Φ_{f_i}[j], Σ)
  - If incremental/gradual with progress α ∈ [0,1]:
    - v_def = V(φ_i, Σ)
    - v_j = V(Φ_{f_i}[j], Σ)
    - v_i = (1-α) * v_def + α * v_j
  - Otherwise (default):
    - v_i = V(φ_i, Σ)
- Note: Σ is extended only after v_i is computed (i.e., features are appended to the environment in declaration order). The generator emits `self._rng.*` calls for distributions (no explicit PRNG threading is required in the generated code).

5) Target evaluation
- After computing Σ_final with all features:
  - v_t = V(φ_target, Σ_final)
  - If Target.type = Binary: y = 1 if v_t is true else 0
  - Else: y = v_t

6) Transition (produce one instance)
- For features f_1..f_n evaluated in order producing v_1..v_n, and target y:
  - the generator emits code that uses `self._rng` for sampling; implementations update their internal PRNG state as needed.
  - ⟨κ, Σ, Δσ⟩ --next--> ⟨(v_1..v_n), y⟩ ⊢ ⟨κ+1, Σ', Δσ'⟩ where Σ' = Σ_params ∪ {f_i ↦ v_i}.
  
7) State updates (rules)
- κ' = κ + 1
- Recurring drift removal: if (κ - t_s) ≥ duration then remove/disable that drift entry
- Gradual progress α = min(1, (κ - t_s)/steps) for interpolation or probabilistic switching

8) Constraints (must hold)
- Acyclic dependency: each feature's formula may reference parameters and earlier features only.
- Scenario safety: requested scenario indices j must satisfy 0 ≤ j < len(Φ_x).
Note: a drift definition's `scenarios` block may contain one or more comma-separated formulas (a single formula is allowed). Scenario formulas are evaluated like regular formulas.
- Type soundness: value returned by V must be compatible with declared feature type τ.

## Minimal example (merged)

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
  drifts
    drift on salary
      type: sudden
      scenarios
        UniformFloat(10000, 40000),
        UniformFloat(30000, 80000)
      end_scenarios
    end_drift
  end_drifts
end_dataset
```

Conceptual generated intent:
```
# setup (conceptual): drift_configs['salary'] = [default, scenario1, scenario2]
features_dict = {}
# feature `int age: UniformInteger(20,80)`
features_dict['age'] = self._rng.randint(20, 80)

# feature `float salary: UniformFloat(20000,150000)` with sudden drift support
# drift_state['salary'] contains the active scenario index (0 = default)
salary_scn = drift_state.get('salary', 0)
if salary_scn == 0:
    val = self._rng.uniform(20000, 150000)
elif salary_scn == 1:
    val = self._rng.uniform(10000, 40000)
elif salary_scn == 2:
    val = self._rng.uniform(30000, 80000)
features_dict['salary'] = val

# target `approved:Binary` mapping (after features computed)
v_t = (features_dict['age'] < 25 and features_dict['salary'] >= 50000)
return 1 if v_t else 0
```
