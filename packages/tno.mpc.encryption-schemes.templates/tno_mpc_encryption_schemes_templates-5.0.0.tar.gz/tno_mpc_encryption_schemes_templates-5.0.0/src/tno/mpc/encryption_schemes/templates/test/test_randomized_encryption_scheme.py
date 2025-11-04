"""
File containing all tests regarding the RandomizedEncryptionScheme functionalities.
"""

# pylint: disable=missing-function-docstring,protected-access

from __future__ import annotations

import copy
from collections.abc import Generator
from typing import Any

import pytest
from pytest import FixtureRequest, WarningsRecorder

from tno.mpc.encryption_schemes.templates import (
    RandomizableCiphertext,
    RandomizedEncryptionSchemeWarning,
    TooLittleRandomnessWarning,
    TooMuchRandomnessWarning,
)
from tno.mpc.encryption_schemes.templates.random_sources import ContextlessSource
from tno.mpc.encryption_schemes.templates.randomized_encryption_scheme import (
    RandomizableCT,
    RandomizedES,
)
from tno.mpc.encryption_schemes.templates.test.conftest import (
    DummyRandomizableCiphertext,
    DummyRandomizedScheme,
    _assert_no_es_warnings,
)


class BaseTestRandomizableCiphertext:
    """
    Tests for randomizable ciphertexts.
    """

    @pytest.fixture(name="fresh_ciphertext", scope="function")
    def fixture_fresh_ciphertext(self, ciphertext: RandomizableCT) -> RandomizableCT:
        """
        Fixture that returns a fresh ciphertext.

        :param ciphertext: Ciphertext with arbitrary freshness.
        :return: Ciphertext that is forced to be fresh.
        """
        ciphertext_copy = copy.deepcopy(ciphertext)
        # Use original scheme to prevent issues in the scheme's RandomnessManager administration
        ciphertext_copy.scheme = ciphertext.scheme
        ciphertext_copy._fresh = True
        return ciphertext_copy

    @pytest.fixture(name="unfresh_ciphertext", scope="function")
    def fixture_unfresh_ciphertext(self, ciphertext: RandomizableCT) -> RandomizableCT:
        """
        Fixture that returns an unfresh ciphertext.

        :param ciphertext: Ciphertext with arbitrary freshness.
        :return: Ciphertext that is forced to be unfresh.
        """
        ciphertext_copy = copy.deepcopy(ciphertext)
        # Use original scheme to prevent issues in the scheme's RandomnessManager administration
        ciphertext_copy.scheme = ciphertext.scheme
        ciphertext_copy._fresh = False
        return ciphertext_copy

    @pytest.fixture(
        name="fixed_freshness_ciphertext",
        params=["fresh_ciphertext", "unfresh_ciphertext"],
    )
    def fixture_fixed_freshness_ciphertext(
        self, request: FixtureRequest
    ) -> RandomizableCiphertext[Any, Any]:
        """
        Fixture that returns ciphertext with fixed freshness.

        Parametrized for a fresh and an unfresh ciphertext.

        :param request: Pytest request fixture.
        :return: Ciphertext.
        """
        return request.getfixturevalue(request.param)  # type: ignore[no-any-return]

    def test_given_ciphertext_if_peak_value_then_unaltered_ciphertext_freshness(
        self, fixed_freshness_ciphertext: RandomizableCT
    ) -> None:
        """
        Test that peeking a ciphertext's value does not alter the ciphertext's freshness.

        :param fixed_freshness_ciphertext: Ciphertext under test.
        """
        freshness = fixed_freshness_ciphertext.fresh
        fixed_freshness_ciphertext.peek_value()
        assert fixed_freshness_ciphertext.fresh is freshness

    def test_given_ciphertext_if_get_value_then_ciphertext_unfresh(
        self, fixed_freshness_ciphertext: RandomizableCT
    ) -> None:
        """
        Test that a ciphertext becomes unfresh if its value is retrieved.

        :param fixed_freshness_ciphertext: Ciphertext under test.
        """
        fixed_freshness_ciphertext.get_value()
        assert not fixed_freshness_ciphertext.fresh

    def test_given_ciphertext_if_randomized_then_has_new_raw_value(
        self, fixed_freshness_ciphertext: RandomizableCT
    ) -> None:
        """
        Test that randomizing a ciphertext changes its raw value.

        :param fixed_freshness_ciphertext: Ciphertext under test.
        """
        raw_value = copy.deepcopy(fixed_freshness_ciphertext.peek_value())
        new_raw_value = fixed_freshness_ciphertext.randomize().peek_value()
        assert raw_value != new_raw_value

    def test_given_ciphertext_if_randomized_then_ciphertext_fresh(
        self, fixed_freshness_ciphertext: RandomizableCT
    ) -> None:
        """
        Test that randomizing a ciphertext makes it fresh.

        :param fixed_freshness_ciphertext: Ciphertext under test.
        """
        assert fixed_freshness_ciphertext.randomize().fresh

    def test_given_fresh_ciphertext_if_randomized_then_efficiency_warning(
        self, fresh_ciphertext: RandomizableCT
    ) -> None:
        """
        Test that randomizing a fresh ciphertext generates an inefficiency warning.

        :param fresh_ciphertext: Ciphertext under test.
        """
        with pytest.warns(RandomizedEncryptionSchemeWarning):
            fresh_ciphertext.randomize()


class BaseTestRandomizedHomomorphicEncryptionScheme:
    """
    Tests for randomized homomorphic encryption schemes.
    """

    def test_unsafe_encrypt_applies_no_randomness(self, scheme: RandomizedES) -> None:
        """
        Test that scheme encryption applies no randomness to the ciphertext in unsafe mode.

        :param scheme: Encryption scheme under test.
        """
        plaintext = 1
        nr_encryptions = 10
        ciphertexts_raw_values = (
            scheme.unsafe_encrypt(plaintext).peek_value() for _ in range(nr_encryptions)
        )
        reference_raw_value = next(ciphertexts_raw_values)
        assert all(
            map(
                lambda rv: reference_raw_value == rv,
                ciphertexts_raw_values,
            )
        )

    def test_encrypt_applies_randomness(self, scheme: RandomizedES) -> None:
        """
        Test that scheme encryption applies randomness to the ciphertext.

        :param scheme: Encryption scheme under test.
        """
        plaintext = 1
        nr_encryptions = 10
        ciphertexts_raw_values = (
            scheme.encrypt(plaintext).peek_value() for _ in range(nr_encryptions)
        )
        # Cannot leverage sets as peek_value has return type Any
        unique_ciphertext_values = []
        for c in ciphertexts_raw_values:
            if c not in unique_ciphertext_values:
                unique_ciphertext_values.append(c)
        assert nr_encryptions == len(unique_ciphertext_values)


class TestRandomizableCiphertext(BaseTestRandomizableCiphertext):
    @pytest.fixture(name="ciphertext")
    def fixture_ciphertext(self) -> Generator[DummyRandomizableCiphertext]:
        scheme = DummyRandomizedScheme()
        ct = DummyRandomizableCiphertext(raw_value=0, scheme=scheme)
        yield ct
        scheme.shut_down()


class TestRandomizedHomomorphicES(BaseTestRandomizedHomomorphicEncryptionScheme):
    @pytest.fixture(name="scheme", scope="class")
    def fixture_scheme(self) -> Generator[DummyRandomizedScheme]:
        scheme = DummyRandomizedScheme()
        yield scheme
        scheme.shut_down()


def test_when_no_source_defined_if_custom_randomness_source_added_then_yield_from_that_source() -> (
    None
):
    scheme = DummyRandomizedScheme()
    source = ContextlessSource([1, 2, 3])
    scheme.register_randomness_source(source)

    values = [scheme.get_randomness() for _ in range(3)]
    assert values == [1, 2, 3]


def test_when_process_source_defined_if_custom_randomness_source_added_then_yield_from_both_sources_in_order() -> (
    None
):
    scheme = DummyRandomizedScheme()
    source = ContextlessSource([1, 2, 3])
    scheme.boot_randomness_generation(7)
    scheme.register_randomness_source(source)

    values = [scheme.get_randomness() for _ in range(10)]
    assert len(values) == 10
    assert values[:3] == [1, 2, 3]


def test_if_too_little_randomness_generation_then_raise_userwarning() -> None:
    """
    Test whether the bounded randomness generation sends a warning when surpassing bound.
    """
    scheme = DummyRandomizedScheme()
    scheme.get_randomness()
    with pytest.warns(TooLittleRandomnessWarning):
        scheme.shut_down()


def test_if_exactly_enough_randomness_generation_then_no_warning(
    recwarn: WarningsRecorder,
) -> None:
    scheme = DummyRandomizedScheme()
    scheme.boot_randomness_generation(1)
    scheme.get_randomness()
    scheme.shut_down()
    assert _assert_no_es_warnings(recwarn)


def test_if_too_much_randomness_generation_then_raise_userwarning() -> None:
    scheme = DummyRandomizedScheme()
    scheme.boot_randomness_generation(1)
    with pytest.warns(TooMuchRandomnessWarning):
        scheme.shut_down()


def test_if_call_boot_randomness_then_processes_are_activated_immediately() -> None:
    scheme = DummyRandomizedScheme()

    scheme.boot_randomness_generation(1)
    process_source = scheme._get_existing_process_source()
    assert process_source is not None
    scheme.get_randomness()

    assert scheme._randomness._is_active(process_source)


def test_if_boot_randomness_twice_then_adds_correctly() -> None:
    scheme = DummyRandomizedScheme()

    scheme.boot_randomness_generation(1)
    scheme.boot_randomness_generation(2)
    values = [scheme.get_randomness() for _ in range(3)]
    assert len(values) == 3


def test_if_shut_down_then_randomness_manager_is_also_shut_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scheme = DummyRandomizedScheme()
    manager = scheme._randomness
    is_closed = False

    def closer() -> None:
        nonlocal is_closed
        is_closed = True

    monkeypatch.setattr(manager, "shutdown", closer)

    scheme.shut_down()
    assert is_closed
