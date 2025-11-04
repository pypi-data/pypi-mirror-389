"""speclike

A helper library for pytest that aims to make test code clearer, more structured,  
and easier to reuse.

It divides tests into two conceptual types:
    - Externally defined tests — intended for **reusing test logic** across multiple cases
    - Individual tests — written directly as single, self-contained test methods

Externally defined tests are composed of **two function definitions** that together form a single test:

    Dispatcher:
        Defines the *Arrange* and *Assert* phases of the AAA testing pattern.  
        Acts as a reusable test logic template.  
        Declares its expected *Act* function (the behavior under test)  
        using a `Sig` object as the default value of one parameter.

    Actor:
        Defines the *Act* phase.  
        It is invoked from within the dispatcher and contains the code that exercises the target behavior.  
        The actor explicitly specifies which dispatcher it belongs to by using `@case.ex(...)`.

The placement of these functions is as follows:

    Dispatcher:
        - Defined either at the module level or inside a class inheriting from `ExSpec`.
        - Must have one parameter whose default value is a `Sig(...)` object.  
          The keys of `Sig` specify the argument names and their expected types.

    Actor:
        - Defined inside a class inheriting from `Spec`.
        - Decorated with `@case.ex(dispatcher)` to bind it to a dispatcher.
        - The method name must be `"_"` (underscore).  
          The generated test name is automatically derived from the dispatcher name.

    Individual tests:
        - Defined inside a class inheriting from `Spec`.
        - They behave as normal pytest-compatible test methods.

All of these definitions use decorators provided by the `_Case` and `_Ex` classes,
which handle labeling and parametrization.

---

### Signature Definition via `Sig`

`Sig` defines the expected signature of the actor function.
Each keyword argument represents a parameter name and its type.

Example:
    ```python
    from speclike import ExSpec, Spec, Sig

    case, ex = Spec.get_decorators()

    # Dispatcher definition
    @ex.edge_pass.follows(-1, 0, 1)
    def check_near_zero(act = Sig(value=int)):
        act(value)  # expect success, no exception
    ```

This declares that the corresponding actor must have a method signature:
    `def _(self, value: int): ...`

If the actor’s parameters differ from those declared by `Sig`,
a descriptive error message is automatically generated during test collection.

---

### Actor Definition

The actor provides the *Act* behavior and is bound to a dispatcher via `@case.ex`.

Example:
    ```python
    class SpecCheckNearZero(Spec):
        @case.ex(check_near_zero)
        def _(self, value: int):
            target_func(value)
    ```

This actor is automatically paired with the dispatcher `check_near_zero`
and generates a pytest-compatible test function named `test_check_near_zero`.

---

### Labeling and Parametrization

Both `_Case` and `_Ex` decorators provide convenient labeling and parametrization helpers:
- Labels such as `@ex.edge`, `@case.feature`, `@case.error`, etc.
- Parametrization through `.follows()`, which generates
  `pytest.mark.parametrize` based on the function’s parameters.

Example:
    ```python
    @ex.feature.follows(-10, 0, 10)
    def within_bounds(act = Sig(value=int)):
        act(value)
    ```

---

### Notes

- `@case.ex(...)` must be used on methods named `"_"`.
- Automatic test generation currently applies only to classes inheriting from `Spec`.
- The API is still under development and may change, though most semantics are now stable.

"""

from speclike.speclike import Spec, ExSpec, Sig

__all__ = [
    "Spec", "ExSpec", "Sig"
]

