from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import sys
from types import GenericAlias
from typing import Any, Callable, Protocol, Self, TypeVar, get_type_hints

import inspect

import pytest


MOD_NAME = "speclike"

T = TypeVar("T", bound = Callable)

_TARGET_KIND = f"_{MOD_NAME}_target_kind"
_PARAMS_UNIT = f"_{MOD_NAME}_params_unit"
_REF_DISPATCHER = f"_{MOD_NAME}_dispatcher"
_NAME_ON_NS = f"_{MOD_NAME}_name_on_namespace"
_OWNER = f"_{MOD_NAME}_owner"
_ACT_SIGNATURE = f"_{MOD_NAME}_act_signature"

class TargetKind(Enum):
    _UNDETERMINED = 0 # not used at current implementation.
    EX_SPEC_ACT = auto()
    EX_SPEC_DISPATCHER = auto()
    EX_SPEC_DISPATCHER_IN_CLASS = auto()
    INDIVIDUAL_TEST_BODY = auto()


class _TailDecorator(Protocol):
    def __call__(self, target: T) -> T:
        ...

class _ExActorDecorator(_TailDecorator, Protocol):
    pass


@dataclass(slots = True)
class _Decorator:
    """
    single-use decorator.

    Each instance is disposable and cannot be reused once applied.  
    A function named "_" is treated as an actor of an externally defined spec.
    """
    
    label: object | None = field(default = None)
    label_as_pytestmark: bool = field(default = False)
    _params: tuple[tuple, dict] | None = field(init = False, default = None)
    _ptms: list = field(init = False, default_factory = list)
    # Lazy initialization until __call__.
    _ref_dispatcher: Callable | None = field(init = False, default = None)
    _returns_target_already: bool = field(init = False, default = False)

    def __call__(self, target: T) -> T:
        if self._returns_target_already:
            raise RuntimeError(
                f"Attempted to process {target.__qualname__}, "
                f"but the decorator has already finished."
            )
        if target.__name__ == "_":
            # If the name is "_", treat it as an actor and set reference to dispatcher.
            if self._ref_dispatcher is None:
                raise RuntimeError(
                    f"Missing dispatcher correspond to {target.__qualname__}."
                )
            if hasattr(target, "pytestmark"):
                raise ValueError(
                    f"Pytestmark can not be applied to actor. " + 
                    f"Actor name {target.__qualname__}"
                )
            setattr(target, _TARGET_KIND, TargetKind.EX_SPEC_ACT)
            setattr(target, _REF_DISPATCHER, self._ref_dispatcher)
            self._returns_target_already = True
            return target
        
        # Otherwise, treat it as either the individual test target or 
        # the dispatcher itself.
        self._prepare_pytestmark_attr_as_list(target)
        
        # May have been marked by CaseBase.actsig as TargetKind.EX_SPEC_DISPATCHER
        if not hasattr(target, _TARGET_KIND):
            setattr(target, _TARGET_KIND, TargetKind.INDIVIDUAL_TEST_BODY)
        
        if self.label_as_pytestmark and self.label is not None:
            if isinstance(self.label, str):
                target.pytestmark.append(getattr(pytest.mark, self.label))
            else:
                target.pytestmark.append(self.label)
        if self._params:
            setattr(target, _PARAMS_UNIT, self._params)
        target.pytestmark.extend(self._ptms)

        self._returns_target_already = True
        return target

    def follows(self, *argvalues, **options) -> Self:
        self._params = argvalues, options
        return self
    
    @property
    def skip(self) -> Self:
        return self.ptm(pytest.mark.skip("User specified."))
    
    @property
    def SKIP(self) -> Self:
        return self.skip

    def ptm(self, *pytestmark) -> Self:
        self._ptms.extend(pytestmark)
        return self
    
    def _get_ex_actor_decorator(self, ex_dispatcher: Callable) -> _ExActorDecorator:
        m = getattr(ex_dispatcher, _TARGET_KIND, None)
        error = m is None
        # None leaves the result unchanged (below).
        error |= m not in (
            TargetKind.EX_SPEC_DISPATCHER, TargetKind.EX_SPEC_DISPATCHER_IN_CLASS
        )
        if error:
            raise TypeError(
                "ex_dispatcher function must be decorated as dispatcher. " +
                (f"but decorated '{m.name}'." if isinstance(m, TargetKind) else "")
            )
        self._ref_dispatcher = ex_dispatcher

        def ex_actor_decorator(target: T) -> T:
            return self.__call__(target)
        
        return ex_actor_decorator

    def _prepare_pytestmark_attr_as_list(self, target: Callable) -> None:
        ptm = getattr(target, "pytestmark", None)
        if ptm:
            if not isinstance(ptm, list):
                ptm = list(ptm)
        else:
            ptm = []
        setattr(target, "pytestmark", ptm)

class _ExSpecNamespace(dict):
    def __init__(self, cls_name: str):
        self.__cls_name = cls_name

    def __setitem__(self, key, value):
        if hasattr(value, _TARGET_KIND):
            kind = getattr(value, _TARGET_KIND)
            if  kind is TargetKind.EX_SPEC_DISPATCHER:
                setattr(value, _TARGET_KIND, TargetKind.EX_SPEC_DISPATCHER_IN_CLASS)
                setattr(value, _NAME_ON_NS, key)
            else:
                raise TypeError(
                    f"Marked method in {self.__cls_name} " + 
                    f"must be marked '{TargetKind.EX_SPEC_DISPATCHER.name}'. " + 
                    f"but it marked with '{kind.name}"
                )
        super().__setitem__(key, value)
            

class _ExSpecMeta(type):

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs) -> _ExSpecNamespace:
        return _ExSpecNamespace(name)

    def __new__(mcls, name, bases, namespace: _ExSpecNamespace):
        cls = super().__new__(mcls, name, bases, namespace)
        for v in cls.__dict__.values():
            if hasattr(v, _TARGET_KIND):
                if getattr(v, _TARGET_KIND) in (
                    TargetKind.EX_SPEC_DISPATCHER,
                    TargetKind.EX_SPEC_DISPATCHER_IN_CLASS
                ):
                    setattr(v, _OWNER, cls)
        return cls

class ExSpec(metaclass = _ExSpecMeta):
    """
    Base class for externally defined spec dispatchers.

    "Ex" stands for "externally defined" (not "external test").
    Inherit this when grouping dispatcher functions defined
    outside of a Spec class.
    """
    pass

    


class CaseBase:
    """
    Base provider of decorator instances.

    Inherit this class when implementing a custom decorator factory.
    """
    __slots__ = ("_as_pytestmark", "_passes", "_blocks")

    def __init__(
        self, as_pytestmark: bool = False, passes: tuple = (), blocks: tuple = ()
    ):
        if as_pytestmark and passes:
            raise ValueError(
                "passes can not be specified when as_pytestmark is True."
            )
        self._as_pytestmark = as_pytestmark
        self._passes = passes
        self._blocks = blocks
    
    def __call__(self, target: T) -> T:
        return self._d(None)(target)
    
    def follows(self, *argvalues, **options) -> _Decorator:
        return self._d(None).follows(*argvalues, **options)
    
    @property
    def skip(self) -> _Decorator:
        return self._d(None).skip
    
    @property
    def SKIP(self) -> _Decorator:
        return self.skip

    def ptm(self, *pytestmark) -> _Decorator:
        return self._d(None).ptm(*pytestmark)

    def ex(self, ex_dispatcher: Callable) -> _ExActorDecorator:
        return self._d(None)._get_ex_actor_decorator(ex_dispatcher)
    
    def actsig(self, **kwargs) -> _TailDecorator:
        for k, v in kwargs.items():
            if not isinstance(v, (type, GenericAlias)):
                raise TypeError(
                    f"Invalid type definition for act parameter '{k}': " + 
                    f"expected a type or generic type alias (e.g. list[int]), " + 
                    f"but received '{type(v).__name__}'."
                )
        def decorator(target: T) -> T:
            setattr(target, _TARGET_KIND, TargetKind.EX_SPEC_DISPATCHER)
            setattr(target, _ACT_SIGNATURE, kwargs)
            return target
        return decorator
    
    def _d(self, label_object: object | None) -> _Decorator:
        passes = self._as_pytestmark
        passes |= bool(self._passes and (label_object in self._passes))
        passes &= label_object not in self._blocks
        return _Decorator(label_object, passes)

class Case(CaseBase):
    __slots__ = ()

    @property
    def api(self) -> _Decorator:
        return self._d("api")

    @property
    def feature(self) -> _Decorator:
        return self._d("feature")
    
    @property
    def default(self) -> _Decorator:
        return self._d("default")
    
    @property
    def init(self) -> _Decorator:
        return self._d("init")
    
    @property
    def init_fail(self) ->_Decorator:
        return self._d("init_fail")
    
    @property
    def cleanup(self) -> _Decorator:
        return self._d("cleanup")
    
    @property
    def cleanup_fail(self) -> _Decorator:
        return self._d("cleanup_fail")
    
    @property
    def edge(self) -> _Decorator:
        return self._d("edge")

    @property
    def edge_pass(self) -> _Decorator:
        return self._d("edge_pass")
    
    @property
    def edge_fail(self) -> _Decorator:
        return self._d("edge_fail")
    
    @property
    def legacy(self) -> _Decorator:
        return self._d("legacy")
    
    @property
    def legacy_fail(self) -> _Decorator:
        return self._d("legacy_fail")
    
    @property
    def violation(self) -> _Decorator:
        return self._d("violation")
    
    @property
    def raises(self) -> _Decorator:
        return self._d("raises")
    
    @property
    def recovers(self) -> _Decorator:
        return self._d("recovers")
    
    @property
    def error(self) -> _Decorator:
        return self._d("error")
    
    @property
    def critical(self) -> _Decorator:
        return self._d("critical")
    
    @property
    def silent(self) -> _Decorator:
        return self._d("silent")
    
    @property
    def NOTE(self) -> _Decorator:
        return self._d("NOTE")
    
    @property
    def IMPORTANT(self) -> _Decorator:
        return self._d("IMPORTANT")


class _SpecNamespace(dict):
    def __init__(self, cls_name: str):
        self.__cls_name = cls_name
        self.__actors = []
    
    def __setitem__(self, key, value):
        if hasattr(value, _TARGET_KIND):
            kind = getattr(value, _TARGET_KIND)
            if  kind is TargetKind.INDIVIDUAL_TEST_BODY:
                setattr(value, _NAME_ON_NS, key)
            elif kind is TargetKind.EX_SPEC_ACT:
                self.__actors.append(value)
                return
            else:
                raise TypeError(
                    f"Marked method in {self.__cls_name} " + 
                    f"must be marked '{TargetKind.INDIVIDUAL_TEST_BODY.name}'. " + 
                    f"but it marked with '{kind.name}"
                )
        super().__setitem__(key, value)
    
    def get_actors(self) -> list[Callable]:
        return list(self.__actors)

    def get_as_dict(self) -> dict[str, Any]:
        return dict(self)

    # override dict.clear()
    def clear(self):
        super().clear()
        self.__actors.clear()

class _ActorDefinitionError(TypeError):
    pass

class _SpecMeta(type):

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs) -> _SpecNamespace:
        return _SpecNamespace(name)

    def __new__(mcls, name, bases, namespace: _SpecNamespace):

        if bases == (object,):
            return super().__new__(mcls, name, bases, namespace)

        generated_funcs: dict[str, Callable] = {}
        
        for v in namespace.values():
            if hasattr(v, _TARGET_KIND):
                kind = getattr(v, _TARGET_KIND)
                if kind is TargetKind.INDIVIDUAL_TEST_BODY:
                    test_body = v
                    test_body_name = getattr(test_body, _NAME_ON_NS)
                    test_name = mcls._get_test_name(test_body_name)
                    test = mcls._create_in_test(test_body)
                    # An individual test body is assumed to already have 
                    # a valid signature in the form of fn(self, p1, p2, ...).
                    test = mcls._copy_signature(test_body, test)
                    test = mcls._init_and_copy_pytestmark_attr(test_body, test)
                    test = mcls._synth_and_set_parametrize_mark(test_body, test)
                    test = mcls._copy_defined_lineno(test_body, test)
                    
                    generated_funcs[test_name] = test
        
        for act in namespace.get_actors():
            dispatcher = getattr(act, _REF_DISPATCHER)
            expected_actsig = getattr(dispatcher, _ACT_SIGNATURE)
            disp_name = mcls._get_dispatcher_name(dispatcher)
            act_name = mcls._get_act_name(disp_name)
            test_name = mcls._get_test_name(disp_name)

            try:
                # passes dipatcher name for structing error message. 
                mcls._ensure_act_has_correct_signature(
                    expected_actsig, disp_name, act
                )
            except _ActorDefinitionError as e:
                try:
                    fftest = mcls._create_force_fail_test_function(e)
                    fftest = mcls._copy_defined_lineno(act, fftest)
                    generated_funcs[test_name] = fftest
                    continue
                except Exception as e:
                    raise e

            # Create a bridge to enable act_name to retrieve a bound method 
            # from the owner instance.
            act_bridge = mcls._create_act_bridge(act)
            generated_funcs[act_name] = act_bridge
            test = mcls._create_ex_test(disp_name, act_name, dispatcher, act)
            #Passing through this method (below) normalizes 
            # the function signature to fn(self, p1, p2, ...).
            test = mcls._set_signature_for_ex_test(dispatcher, test)
            test = mcls._init_and_copy_pytestmark_attr(dispatcher, test)
            test = mcls._synth_and_set_parametrize_mark(dispatcher, test)
            test = mcls._copy_defined_lineno(act, test)
            
            generated_funcs[test_name] = test
        
        namespace_for_type = namespace.get_as_dict()
        namespace.clear()

        namespace_for_type.update(generated_funcs)
        # Add "Test" to class name if class name does not start with "Test".
        gen_cls_name = mcls._get_spec_class_name(name)
        
        cls = super().__new__(mcls, gen_cls_name, bases, namespace_for_type)

        if gen_cls_name != name:
            module = sys.modules[cls.__module__]
            setattr(module, gen_cls_name, cls)
            if name in module.__dict__:
                delattr(module, name)
            
        return cls
    
    @classmethod
    def _create_force_fail_test_function(mcls, e: Exception):
        def generated_force_fail_test(self):
            pytest.fail(f"This is FORCE FAILED test reason as below.\n{e}")
        return generated_force_fail_test

    @classmethod
    def _get_dispatcher_name(mcls, dispatcher: Callable):
        name_on_ns = getattr(dispatcher, _NAME_ON_NS, None)
        return name_on_ns if name_on_ns else dispatcher.__name__

    @classmethod
    def _get_test_name(mcls, name) -> str:
        return f"test_{name}"
    
    @classmethod
    def _get_act_name(mcls, disp_name) -> str:
        return f"act_for_{disp_name}"
    
    @classmethod
    def _get_spec_class_name(mcls, cls_name: str) -> str:
        if cls_name.startswith("Test"):
            return cls_name
        return f"Test{cls_name}"
    
    @classmethod
    def _ensure_act_has_correct_signature(
        mcls, form: dict[str, type], disp_name: str, act: Callable
    ) -> None:
        error_prefix = f"Invalid actor definition for '{disp_name}': "
        sig = inspect.signature(act)
        hints = get_type_hints(act)
        params = list(sig.parameters.values())[1:]  # skip 'self'

        # signatures string for error messages
        actual_sig = mcls._format_signature_with_types(act)
        expected_sig = (
            "fn(self, " + ", ".join(
                f"{name}: {tp.__name__}" for name, tp in form.items()
            ) + ")"
        )
        if expected_sig == "fn(self, )":
            expected_sig = "fn(self)"

        for index, (expected_name, expected_type) in enumerate(form.items()):
            if index >= len(params):
                raise _ActorDefinitionError(
                    error_prefix +
                    f"It has fewer parameters " +
                    f"than expected (missing index {index}).\n" +
                    f"Expected signature: {expected_sig}\n" +
                    f"Actual signature: {actual_sig}"
                )

            param = params[index]

            # name check
            if param.name != expected_name:
                raise _ActorDefinitionError(
                    error_prefix +
                    f"Parameter name mismatch: " +
                    f"expected '{expected_name}', but received '{param.name}'.\n" +
                    f"Expected signature: {expected_sig}\n" +
                    f"Actual signature: {actual_sig}"
                )

            # type check (only if act annotates it)
            actual_type = hints.get(param.name)
            if actual_type is not None and actual_type != expected_type:
                raise _ActorDefinitionError(
                    error_prefix +
                    f"Type mismatch at parameter '{param.name}': " +
                    f"expected '{expected_type.__name__}', " +
                    f"but received '{actual_type.__name__}'.\n" +
                    f"Expected signature: {expected_sig}\n" +
                    f"Actual signature: {actual_sig}"
                )
        
        if len(params) > len(form):
            extra_params = [p.name for p in params[len(form):]]
            raise _ActorDefinitionError(
                error_prefix +
                f"It has unexpected extra parameter(s): " +
                f"{', '.join(extra_params)}.\n"
                f"Expected signature: {expected_sig}\n" + 
                f"Actual signature: {actual_sig}"
            )

    @classmethod
    def _format_signature_with_types(mcls, func: Callable) -> str:
        sig = inspect.signature(func)
        hints = get_type_hints(func)

        formatted_params = []
        for name in sig.parameters.keys():
            if name in hints:
                tp = hints[name]
                # Handle type or GenericAlias
                if isinstance(tp, type):
                    type_str = tp.__name__
                else:
                    type_str = repr(tp).replace("typing.", "")
                formatted_params.append(f"{name}: {type_str}")
            else:
                formatted_params.append(name)

        return f"fn({', '.join(formatted_params)})"
    
    @classmethod
    def _create_act_bridge(mcls, act: Callable) -> Callable:
        if inspect.iscoroutinefunction(act):
            async def act_for_dispatcher_async(self, *args, **kwargs):
                act(self, *args, **kwargs)
            generated_act = act_for_dispatcher_async
        else:
            def act_for_dispatcher(self, *args, **kwargs):
                act(self, *args, **kwargs)
            generated_act = act_for_dispatcher
        
        return generated_act

    @classmethod
    def _create_ex_test(
            mcls, disp_name: str, act_name: str, dispatcher: Callable, act: Callable
    ) -> Callable:
        is_d_async = inspect.iscoroutinefunction(dispatcher)
        is_a_async = inspect.iscoroutinefunction(act)
        if not is_d_async and is_a_async:
            raise TypeError("Ex test actor must be sync function.")
        disp_owner = getattr(dispatcher, _OWNER, None)
        if disp_owner:
            bound_disp_getter = lambda: getattr(disp_owner(), disp_name)
        else:
            # For dispatcher defined on top-level.
            bound_disp_getter = lambda: dispatcher
        generated_test = None
        if is_d_async:
            async def ex_test_async(self, *args, **kwargs):
                bound_act = getattr(self, act_name)
                await bound_disp_getter()(bound_act, *args, **kwargs)
            generated_test = ex_test_async
        else:
            # def ex_test(self, *args, **kwargs):
            def ex_test(self, *args, **kwargs):
                bound_act = getattr(self, act_name)
                bound_disp_getter()(bound_act, *args, **kwargs)
            generated_test = ex_test

        return generated_test
    
    @classmethod
    def _set_signature_for_ex_test(
        mcls, dispatcher: Callable, target: Callable
    ) -> Callable:
        
        kind = getattr(dispatcher, _TARGET_KIND)
        disp_sig = inspect.signature(dispatcher)
        test_params = list(disp_sig.parameters.values())

        # Strict positional rule, name is arbitrary
        len_required = 2 if kind is TargetKind.EX_SPEC_DISPATCHER_IN_CLASS else 1
        if len(test_params) < len_required:
            raise TypeError(
                f"Dispatcher '{dispatcher.__qualname__}' must define an argument " +
                "in the 'act' position."
            )
        
        if kind is TargetKind.EX_SPEC_DISPATCHER:
            test_params = test_params[1:] # remove first param ('act')
            test_params.insert(
                0, inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ) 
        elif kind is TargetKind.EX_SPEC_DISPATCHER_IN_CLASS:
            test_params.pop(1) # remove second param ('act'), keep 'self'
        else:
            raise RuntimeError(f"Unexpected kind found '{kind}'.")
        
        target.__signature__ = inspect.Signature(parameters = test_params)
        return target
        
    
    @classmethod
    def _create_in_test(mcls, test_body: Callable):
        test_body_ns_name = getattr(test_body, _NAME_ON_NS)
        generated_test = None
        if inspect.iscoroutinefunction(test_body):
            async def in_test_async(self, *args, **kwargs):
                bound_act = getattr(self, test_body_ns_name)
                await self.dispatch_async(
                    test_body_ns_name, bound_act, *args, **kwargs
                )
            generated_test = in_test_async
        else:
            def in_test(self, *args, **kwargs):
                bound_act = getattr(self, test_body_ns_name)
                self.dispatch(
                    test_body_ns_name, bound_act, *args, **kwargs
                )
            generated_test = in_test
        
        return generated_test

    @classmethod
    def _copy_signature(mcls, src: Callable, dst: Callable) -> Callable:
        dst.__signature__ = inspect.signature(src)
        return dst
    
    @classmethod
    def _synth_and_set_parametrize_mark(mcls, src: Callable, dst: Callable) -> Callable:
        unit = getattr(src, _PARAMS_UNIT, ())
        if unit:
            valueargs, options = unit
            sig = inspect.signature(dst)
            params = list(sig.parameters.keys())[1:]
            argnames = ",".join(params)

            dst.pytestmark.append(
                pytest.mark.parametrize(argnames, valueargs, **options)
            )
        return dst

    @classmethod
    def _copy_defined_lineno(mcls, src: Callable, dst: Callable) -> Callable:
        code = dst.__code__.replace(
            co_firstlineno=src.__code__.co_firstlineno,
            co_filename=src.__code__.co_filename,
        )
        dst.__code__ = code
        dst.__module__ = dst.__module__
        return dst
    
    @classmethod
    def _init_and_copy_pytestmark_attr(mcls, src: Any, dst: Callable) -> Callable:
        setattr(dst, "pytestmark", getattr(src, "pytestmark").copy())
        return dst


class Spec(metaclass = _SpecMeta):
    """
    Base class for generated spec tests.

    Subclass this to customize how individual tests are invoked.
    Override `dispatch()` or `dispatch_async()` to change
    call signatures or invocation behavior of generated tests.
    """
    __slots__ = ()

    async def dispatch_async(self, name: str, actor: Callable, *args, **kwargs):
        await actor(*args, **kwargs)
    
    def dispatch(self, name: str, actor: Callable, *args, **kwargs):
        actor(*args, **kwargs)

