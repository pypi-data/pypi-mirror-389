"""
# speclike

`speclike` is a **pytest helper library** designed to define tests in a more structured and expressive way.  
It provides a declarative approach for building tests from two complementary perspectives:

- **Individual test bodies**, written as ordinary methods.
- **Externally defined dispatchers and actors**, representing scenario-driven or behavior-based tests.

The framework automatically generates executable pytest test functions (`test_...`) from decorated functions and classes.

---

## 🧩 Core Concepts

### 1. `Spec` and `ExSpec` Classes
- **`Spec`** — the main base class for declarative test specifications.  
  It manages auto-generated tests and delegates execution through `dispatch()` or `dispatch_async()`.
- **`ExSpec`** — groups externally defined dispatchers (functions that control test flow outside of the class).

Both are implemented using metaclasses (`_SpecMeta`, `_ExSpecMeta`) that synthesize pytest-compatible test functions during class creation.

---

### 2. `Case` and `Ex` Decorators
- **`Case`** — marks individual test bodies or actor functions (`def _(...):`) within a `Spec` class.  
  It can attach pytest marks, parametrize data, or skip tests dynamically.
- **`Ex`** — marks dispatcher functions used in `ExSpec` or top-level definitions.  
  Dispatchers define parameter structure using `PRM`, and connect to actors via `@case.ex(dispatcher)`.

---

### 3. `PRM` (Parameter Prefix Rules)
Defines how test parameters behave and interact between dispatcher and actor.

| Prefix | Kind | Behavior |
|---------|------|-----------|
| `_` | AO (Actor-Only) | Created by dispatcher, passed to actor (not parametrized) |
| *(none)* | AP (Actor-Parametrized) | Parametrized and passed to actor |
| `__` | PO (Param-Only) | Parametrized but **not** passed to actor (used for assertions) |

Parameter ordering must follow `AO → AP → PO`.

`PRM` validates actor signatures, generates pytest parametrization, and bridges runtime values through `_ParamsBridge`.

---

### 4. `Dispatcher` and `Actor`
- **Dispatcher**: a function decorated with `@ex` that defines test input combinations using `PRM`.
- **Actor**: a function named `_` decorated with `@case.ex(dispatcher)` that performs the actual behavior under test.
- The library automatically links each actor to its dispatcher and generates a `test_<dispatcher>` method that executes the pair.

---

### 5. Test Generation Workflow
1. The metaclass scans for decorated functions (`TargetKind`).
2. Each test body or dispatcher/actor pair is converted into a pytest-visible `test_...` function.
3. Signatures, parametrization, and pytest marks are copied to preserve readability and IDE support.
4. For external specs (`ExSpec`), tests are created dynamically based on defined dispatchers.

---

### 6. Highlights
- Strong signature validation for actors against their `PRM` definitions.
- Automatic propagation of `pytest.mark.parametrize` and other pytest marks.
- Source location (`co_firstlineno`) is preserved for accurate traceback references.
- Supports both sync and async test execution paths.

---

### Example

```python
from speclike import Spec, PRM

# Example domain object
class Context:
    def compute(self, x: int) -> int:
        return x * 10

# Get decorators
case, ex = Spec.get_decorators()

# Dispatcher (external). Parameters are NOT taken as direct function args.
# Access AP/PO values via the bridge `p`, and call the actor via `p.act(...)`.
@ex.follows(
    [(1, 10), (2, 20), (3, 30)],  # (value, __expected)
    ids=["x1", "x2", "x3"]
)
def check(p = PRM(_ctx=Context, value=int, __expected=int)):
    ctx = Context()                             # AO: create here
    result = p.act(_ctx=ctx, value=p.value)     # call actor with AO/AP
    assert result == p.__expected               # PO: only used in dispatcher

# Spec class with actor method named "_"
class TestCompute(Spec):
    @case.ex(check)
    def _(self, _ctx: Context, value: int) -> int:
        # Actor receives AO/AP only, in the declared order.
        return _ctx.compute(value)
````

At runtime, this generates:

* `test_check` — a parametrized pytest function executing the dispatcher.
* `act_for_check` — an internal bound actor function used by the dispatcher.

---

---

## 🧱 Decorator Creation Layer

### Overview

The *Decorator Creation Layer* defines how decorators are generated, labeled, and applied in **speclike**.
It provides the foundation for `@case` and `@ex`, ensuring that both ordinary test bodies and dispatcher-driven actors can be declared in a unified, readable form.

This layer is responsible for:

* Generating consistent decorator instances for tests and actors.
* Providing label-based classification (`api`, `feature`, `edge`, etc.).
* Managing scenario-oriented labeling (`scenario.init`, `scenario.cleanup_fail`, etc.).
* Linking external dispatchers and actors through structured decorators.

---

### Label-Based Test Definitions

Labels are used to categorize test functions according to their role or context.
They can be attached to any regular test method defined inside a `Spec` class.

```python
from speclike import Spec

case, ex = Spec.get_decorators()

class TestCalculation(Spec):
    @case.api
    def verifies_public_interface(self):
        ...

    @case.feature
    def handles_standard_case(self):
        ...

    @case.edge_fail
    def fails_on_invalid_input(self):
        ...
```

Each label corresponds to a specific internal decorator that `speclike` translates into a standard pytest test function.
This labeling mechanism helps organize test intent without introducing extra configuration or naming conventions.

---

### Scenario Labels

The `scenario` namespace provides additional labeling for multi-phase or behavior-driven test organization.
It is useful when tests represent stages of a process or parts of a workflow.

```python
class TestLifecycle(Spec):
    @case.scenario.init
    def initializes_resource(self):
        ...

    @case.scenario.feature
    def performs_normal_operation(self):
        ...

    @case.scenario.cleanup
    def releases_resources(self):
        ...
```

Scenario-prefixed labels (`scenario.init`, `scenario.feature`, `scenario.cleanup`, etc.) behave like standard labels, but emphasize the role of the test within a broader execution flow.

---

* The dispatcher (`check`) defines parameter pairs `(value, __expected)` and invokes the actor via `p.act(...)`.
* The actor (decorated with `@case.ex(check)`) implements the tested operation.
* Both are automatically combined into a pytest test function (`test_check`).

---

### Summary

The *Decorator Creation Layer* unifies labeling, test generation, and dispatcher–actor linking into a single mechanism.
It allows consistent use of descriptive decorators while maintaining compatibility with pytest.
Developers can structure tests declaratively — defining **what** to test (`Ex`) and **how** to test it (`Case`) — without additional configuration.


"""

from speclike.impl import Spec, ExSpec, PRM

__all__ = [
    "Spec", "ExSpec", "PRM"
]

