"""speclike

A helper library for pytest designed to make test code clearer and more structured.

It divides tests into two conceptual types:
    - Externally defined tests  (intended for **test logic reuse** across multiple cases)
    - Individual tests

Externally defined tests are composed of two function definitions that together form a single test:
    Dispatcher:
        Describes the Arrange and Assert phases of AAA testing.  
        Serves as a kind of test logic template.
    Actor:
        Describes the Act phase.  
        It is called from within the dispatcher template and contains the code that exercises the target behavior.

The placement of these functions is as follows:
    Dispatcher:
        Defined either at the top level or inside a class inheriting from `ExSpec`.  
        Must declare the arguments given to the actor by using `@case.actsig(...)`.
    Actor:
        Defined inside a class inheriting from `Spec`.  
        Uses `@case.ex(...)` to specify its corresponding dispatcher.  
        The method name must be `"_"`.
    Individual tests:
        Defined inside a class inheriting from `Spec`.

All of these definitions use decorators provided by the `Case` class,
which also handles labeling tests (for example: `@case.feature`, `@case.edge`, `@case.error`, etc.).

Two notable helpers are skipping and parametrization.  
Parametrization is provided through `.follows`, which automatically combines
the given parameters with the function’s argument information to generate a
corresponding `pytest.mark.parametrize`.

The decorator order and interaction with unrelated decorators are not yet finalized.  
In particular, when labeling or marking a dispatcher, place `@case.actsig` **inside** other decorators.

Example:
    ```python
    @case.edge_pass.follows(-1, 0, 1)
    @case.actsig(value=int)
    def check_near_zero(act, value):
        act(value)  # expect success, no exception.
    ```

Currently, test generation only occurs for classes inheriting from `Spec`.  
The system is still under development and may be unstable, though the API is mostly settled.


AI generated sample code:

# ------------------------------------------------------------
# Test target (user_service.py)
# ------------------------------------------------------------

class UserAlreadyExistsError(Exception):
    pass

class UserService:
    '''A simple service that registers users in memory.'''

    def __init__(self):
        self._users = {}

    def register(self, username: str, email: str):
        if username in self._users:
            raise UserAlreadyExistsError(f'{username} already exists')
        if '@' not in email:
            raise ValueError('Invalid email')
        self._users[username] = email
        return {'username': username, 'email': email}

    def get_user(self, username: str):
        return self._users.get(username)

    
# ------------------------------------------------------------
# Test module
# ------------------------------------------------------------
import pytest
from speclike import Case, Spec, ExSpec
from user_service import UserService, UserAlreadyExistsError

# ============================================================
# Case instance (decorator entry point)
# ============================================================
case = Case(as_pytestmark=True)

# ============================================================
# Dispatcher definitions (Arrange + Assert)
# ============================================================
@case.feature
@case.actsig(username=str, email=str)
def register_success(act, username, email):
    '''Dispatcher for successful user registration.'''
    # Arrange
    svc = UserService()
    # Act
    result = act(svc, username, email)
    # Assert
    assert result['username'] == username
    assert result['email'] == email
    assert svc.get_user(username) == email

@case.error
@case.actsig(username=str, email=str)
def register_failures(act, username, email):
    '''Dispatcher for expected registration failures.'''
    svc = UserService()
    # Act & Assert
    with pytest.raises(Exception) as e:
        act(svc, username, email)
    # Verify the raised error type
    assert isinstance(e.value, (ValueError, UserAlreadyExistsError))


# ============================================================
# Grouping dispatchers in an ExSpec class
# ============================================================
class UserDispatchers(ExSpec):

    @case.critical
    @case.actsig(username=str)
    def duplicate_registration(self, act, username):
        '''Dispatcher to check duplicate registration scenario.'''
        svc = UserService()
        svc.register(username, 'first@example.com')
        with pytest.raises(UserAlreadyExistsError):
            act(svc, username)


# ============================================================
# Spec: defines concrete Actors (Act phase)
# ============================================================
class UserRegistration(Spec):

    @case.ex(register_success)
    def _(self, svc: UserService, username: str, email: str):
        '''Actor for successful registration.'''
        return svc.register(username, email)

    @case.ex(register_failures)
    def _(self, svc: UserService, username: str, email: str):
        '''Actor for invalid or duplicate registration.'''
        return svc.register(username, email)

    @case.ex(UserDispatchers.duplicate_registration)
    def _(self, svc: UserService, username: str):
        '''Actor for duplicate registration test.'''
        svc.register(username, 'second@example.com')

    @case.edge.follows((['foo'],), (['bar', 'baz'],))
    def test_user_list_invariant(self, usernames):
        '''Individual test to ensure invariant of user list.'''
        svc = UserService()
        for name in usernames:
            svc.register(name, f'{name}@example.com')
        assert all('@' in v for v in svc._users.values())

$ pytest -v
=========================== test session starts ===========================
collected 5 items

test_user_service.py::TestUserRegistration::test_register_success PASSED
test_user_service.py::TestUserRegistration::test_register_failures PASSED
test_user_service.py::TestUserRegistration::test_duplicate_registration PASSED
test_user_service.py::TestUserRegistration::test_user_list_invariant[foo] PASSED
test_user_service.py::TestUserRegistration::test_user_list_invariant[bar,baz] PASSED
============================ 5 passed in 0.05s ============================

                
"""

from speclike.speclike import Spec, ExSpec, Case, CaseBase

__all__ = [
    "Spec", "ExSpec", "CaseBase", "Case"
]

