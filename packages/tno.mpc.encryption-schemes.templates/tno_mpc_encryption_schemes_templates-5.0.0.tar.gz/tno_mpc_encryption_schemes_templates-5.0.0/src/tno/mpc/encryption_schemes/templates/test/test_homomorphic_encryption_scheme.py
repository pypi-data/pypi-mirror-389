"""
Module for testing functionalities of a HomomorphicEncryptionScheme and HomomorphicCiphertext.
"""

# pytest: disable=pointless-statement

from __future__ import annotations

import copy
from contextlib import nullcontext as no_raises
from typing import Any, Protocol, cast

import pytest
from pytest import FixtureRequest, WarningsRecorder

from tno.mpc.encryption_schemes.templates.encryption_scheme import PT
from tno.mpc.encryption_schemes.templates.exceptions import (
    RandomizedEncryptionSchemeWarning,
)
from tno.mpc.encryption_schemes.templates.homomorphic_encryption_scheme import (
    AdditiveHomomorphicCT,
    AdditiveHomomorphicES,
    HomomorphicCiphertext,
    HomomorphicCT,
    HomomorphicEncryptionScheme,
    HomomorphicES,
    MultiplicativeHomomorphicCT,
    MultiplicativeHomomorphicES,
)
from tno.mpc.encryption_schemes.templates.test.conftest import (
    DummyHomomorphicCiphertext,
    DummyHomomorphicScheme,
    _assert_no_es_warnings,
)


# region multiplication classes for typing
# Helper classes for type checking that capture multiplication capabilities of both additive and multiplicative schemes
class _SupportsDunderMul(Protocol):
    def __mul__(self, other: HomomorphicCT | PT) -> HomomorphicCT: ...
    def __rmul__(self, other: HomomorphicCT | PT) -> HomomorphicCT: ...


class _SupportsMultiplicationCT(
    _SupportsDunderMul, HomomorphicCiphertext[Any, Any, Any]
):
    pass


class _SupportsMul(Protocol):
    def mul(
        self, ciphertext: HomomorphicCT, other: HomomorphicCT | PT
    ) -> HomomorphicCT: ...


class _SupportsMultiplicationES(
    _SupportsMul, HomomorphicEncryptionScheme[Any, Any, Any, Any, Any]
):
    pass


# endregion


class BaseTestHomomorphicCiphertext:
    """
    Tests for homomorphic ciphertexts.

    This class contains generic tests for homomorphic ciphertexts. Implementors of custom ciphertext
    classes can leverage those tests as follows:

    ```python
    # test_my_homomorphic_ciphertext.py
    class TestMyHomomorphicCiphertext(BaseTestHomomorphicCiphertext):
        @pytest.fixture(name="ciphertext", scope="class")
        def fixture_ciphertext(self) -> MyHomomorphicCiphertext:
            ...
    ```

    The implementing test classes may *additionally* inherit from specialized homomorphic base test
    classes (e.g. `BaseTestAdditiveHomomorphicCiphertext` and
    `BaseTestMultiplicativeHomomorphicCiphertext`) to add testing functionality (e.g. addition
    and multiplication with scalars and ciphertexts).
    """

    def test_two_identical_ciphertexts_are_equal(
        self, ciphertext: HomomorphicCT
    ) -> None:
        """
        Test that a ciphertext and its copy are deemed equal.

        :param ciphertext: Ciphertext under test.
        """
        ciphertext_copy = copy.deepcopy(ciphertext)
        assert ciphertext == ciphertext_copy

    def test_two_ciphertexts_with_different_raw_value_are_not_equal(
        self, ciphertext: HomomorphicCT
    ) -> None:
        """
        Test that two ciphertexts with different raw value are deemed unequal.

        :param ciphertext: Ciphertext under test.
        """
        ciphertext_copy = copy.deepcopy(ciphertext)
        ciphertext_copy._raw_value -= 1
        assert ciphertext != ciphertext_copy

    def test_two_ciphertexts_with_different_scheme_are_not_equal(
        self, ciphertext: HomomorphicCT
    ) -> None:
        """
        Test that two ciphertexts with different schemes are deemed unequal.

        :param ciphertext: Ciphertext under test.
        """
        ciphertext_copy = copy.deepcopy(ciphertext)
        ciphertext_copy.scheme = 1  # type: ignore[assignment]
        assert ciphertext != ciphertext_copy


class _BaseTestHomomorphicCiphertextMul:
    def test_multiplication_with_plaintext_raises_no_error(
        self,
        ciphertext: _SupportsMultiplicationCT,
    ) -> None:
        """
        Test that `ciphertext.__mul__` raises no errors when applied to a plaintext value.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            ciphertext * 1

    def test_reflected_multiplication_with_plaintext_raises_no_error(
        self,
        ciphertext: _SupportsMultiplicationCT,
    ) -> None:
        """
        Test that `ciphertext.__rmul__` raises no errors when applied to a plaintext value.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            1 * ciphertext


class BaseTestAdditiveHomomorphicCiphertext(_BaseTestHomomorphicCiphertextMul):
    """
    Tests for additive homomorphic ciphertexts.

    Please refer to the documentation of `BaseTestHomomorphicCiphertext` for usage
    instructions.
    """

    def test_neg_raises_no_error(self, ciphertext: AdditiveHomomorphicCT) -> None:
        """
        Test that `ciphertext.__neg__` raises no errors.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            -ciphertext

    def test_addition_of_plaintext_raises_no_error(
        self,
        ciphertext: AdditiveHomomorphicCT,
    ) -> None:
        """
        Test that `ciphertext.__add__` raises no errors when applied to a plaintext value.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            ciphertext + 0

    def test_reflected_addition_of_plaintext_raises_no_error(
        self,
        ciphertext: AdditiveHomomorphicCT,
    ) -> None:
        """
        Test that `ciphertext.__radd__` raises no errors when applied to a plaintext value.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            0 + ciphertext

    def test_addition_of_ciphertext_raises_no_error(
        self,
        ciphertext: AdditiveHomomorphicCT,
    ) -> None:
        """
        Test that `ciphertext.__add__` raises no errors when applied to itself.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            ciphertext + ciphertext

    def test_subtraction_of_plaintext_raises_no_error(
        self,
        ciphertext: AdditiveHomomorphicCT,
    ) -> None:
        """
        Test that `ciphertext.__sub__` raises no errors when applied to a plaintext value.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            ciphertext - 0

    def test_reflected_subtraction_of_plaintext_raises_no_error(
        self,
        ciphertext: AdditiveHomomorphicCT,
    ) -> None:
        """
        Test that `ciphertext.__rsub__` raises no errors when applied to a plaintext value.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            0 - ciphertext

    def test_subtraction_of_ciphertext_raises_no_error(
        self,
        ciphertext: AdditiveHomomorphicCT,
    ) -> None:
        """
        Test that `ciphertext.__sub__` raises no errors when applied to itself.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            ciphertext - ciphertext


class BaseTestMultiplicativeHomomorphicCiphertext(_BaseTestHomomorphicCiphertextMul):
    """
    Tests for multiplicative homomorphic ciphertexts.

    Please refer to the documentation of `BaseTestHomomorphicCiphertext` for usage
    instructions.
    """

    def test_multiplication_of_ciphertext_raises_no_error(
        self,
        ciphertext: MultiplicativeHomomorphicCT,
    ) -> None:
        """
        Test that `ciphertext.__mul__` raises no errors when applied to itself.

        :param ciphertext: Ciphertext under test.
        """
        with no_raises():
            ciphertext * ciphertext


class BaseTestHomomorphicEncryptionScheme:
    """
    Tests for homomorphic encryption schemes.

    This class contains generic tests for homomorphic encryption schemes. Implementers of custom
    encryption scheme classes can leverage those tests as follows:

    ```python
    # test_my_homomorphic_ciphertext.py

    _TEST_VALUES = [-1, 0, 1]

    class TestMyHomomorphicEncryptionScheme(BaseTestHomomorphicEncryptionScheme):
        @pytest.fixture(name="scheme", scope="class")
        def fixture_scheme(self) -> DummyHomomorphicScheme:
            ...

        @pytest.fixture(name="same_scheme", scope="class")
        def fixture_same_scheme(self) -> DummyHomomorphicScheme:
            ...

        @pytest.fixture(name="different_scheme", scope="class")
        def fixture_different_scheme(self) -> DummyHomomorphicScheme:
            ...

        @pytest.fixture(name="value", scope="class", params=_TEST_VALUES)
        def fixture_value(self, request: FixtureRequest) -> int:
            ...

        @pytest.fixture(name="ciphertext", scope="class", params=_TEST_VALUES)
        def fixture_ciphertext(
            self, scheme: DummyHomomorphicScheme
        ) -> DummyHomomorphicCiphertext:
            ...

        @pytest.fixture(
            name="ciphertext_pair",
            scope="class",
            params=_TEST_VALUES,
        )
        def fixture_ciphertext_pair(
            self, request: FixtureRequest, scheme: DummyHomomorphicScheme
        ) -> tuple[DummyHomomorphicCiphertext, DummyHomomorphicCiphertext]:
            ...
    ```

    The implementing test classes may *additionally* inherit from specialized homomorphic base test
    classes (e.g. `BaseTestAdditiveHomomorphicEncryptionScheme` and
    `BaseTestMultiplicativeHomomorphicEncryptionScheme`) to add testing functionality (e.g. addition
    and multiplication with ciphertexts).
    """

    # region default fixtures

    @pytest.fixture(name="value_transform")
    def fixture_value_transform(self, value: PT) -> PT:
        """
        Plaintext value to use in transformation tests, e.g. encode, encrypt.

        :param value: Plaintext value to use.
        :return: Plaintext value.
        """
        return value

    @pytest.fixture(name="value_transform_no_encoding")
    def fixture_value_transform_no_encoding(self, value_transform: PT) -> PT:
        """
        Plaintext value to use in transformation tests that skip encoding.

        :param value_transform: Plaintext value to use.
        :return: Plaintext value.
        """
        return value_transform

    # endregion

    def test_two_similar_schemes_are_equal(
        self, scheme: HomomorphicES, same_scheme: HomomorphicES
    ) -> None:
        """
        Test that two similar schemes are deemed equal.

        :param scheme: Encryption scheme under test.
        :param same_scheme: Encryption scheme that should be deemed equal by scheme.__eq__.
        """
        assert scheme == same_scheme

    def test_two_different_schemes_are_not_equal(
        self, scheme: HomomorphicES, different_scheme: HomomorphicES
    ) -> None:
        """
        Test that two different schemes are deemed unequal.

        :param scheme: Encryption scheme under test.
        :param different_scheme: Encryption scheme that should be deemed unequal by scheme.__eq__.
        """
        assert scheme != different_scheme

    def test_encode_then_decode_returns_original_value(
        self, scheme: HomomorphicES, value_transform: PT
    ) -> None:
        """
        Test that scheme encoding and subsequent decoding returns in the original value.

        :param scheme: Encryption scheme under test.
        :param value_transform: Value that is to be encoded, and expected to then be decoded into
            the same value.
        """
        assert value_transform == scheme.decode(scheme.encode(value_transform))

    def test_encrypt_then_decrypt_with_encoding_returns_original_value(
        self, scheme: HomomorphicES, value_transform: PT
    ) -> None:
        """
        Test that scheme encryption and subsequent decryption returns in the original value if
        encoding is applied.

        :param scheme: Encryption scheme under test.
        :param value_transform: Value that is to be encrypted, and expected to then be decrypted
            into the same value.
        """
        assert value_transform == scheme.decrypt(
            scheme.encrypt(value_transform, apply_encoding=True), apply_encoding=True
        )

    def test_encrypt_then_decrypt_without_encoding_returns_original_value(
        self, scheme: HomomorphicES, value_transform_no_encoding: PT
    ) -> None:
        """
        Test that scheme encryption and subsequent decryption returns in the original value if
        encoding is not applied.

        :param scheme: Encryption scheme under test.
        :param value_transform_no_encoding: Value that is to be encrypted, and expected to then be
            decrypted into the same value.
        """
        assert value_transform_no_encoding == scheme.decrypt(
            scheme.encrypt(value_transform_no_encoding, apply_encoding=False),
            apply_encoding=False,
        )


class _BaseTestHomomorphicEncryptionSchemeMul:
    def test_multiplication_with_plaintext(
        self,
        scheme: _SupportsMultiplicationES,
        ciphertext_mul: HomomorphicCT,
        value_mul: PT,
    ) -> None:
        """
        Test that multiplication of a ciphertext with a plaintext yields the expected result.

        :param scheme: Encryption scheme under test.
        :param ciphertext_mul: Ciphertext under test.
        :param value_mul: Plaintext under test.
        """
        expected_prod = value_mul * scheme.decrypt(ciphertext_mul)
        assert expected_prod == scheme.decrypt(scheme.mul(ciphertext_mul, value_mul))

    def test_multiplication_with_unfresh_ciphertext_raises_no_efficiency_warning(
        self,
        recwarn: WarningsRecorder,
        scheme: _SupportsMultiplicationES,
    ) -> None:
        """
        Test that `mul(ct, pt)` raises no efficiency warning if `ct` is an unfresh ciphertext.

        :param recwarn: Pytest recwarn fixture.
        :param scheme: Encryption scheme under test.
        """
        unfresh_ct = scheme.unsafe_encrypt(0)
        scheme.mul(unfresh_ct, 0)
        assert _assert_no_es_warnings(recwarn)

    def test_multiplication_with_fresh_ciphertext_raises_efficiency_warning(
        self,
        scheme: _SupportsMultiplicationES,
    ) -> None:
        """
        Test that `mul(ct, pt)` raises an efficiency warning if `ct` is a fresh ciphertext.

        :param scheme: Encryption scheme under test.
        """
        fresh_ct = scheme.encrypt(0)
        with pytest.warns(RandomizedEncryptionSchemeWarning):
            scheme.mul(fresh_ct, 0)

    def test_multiplication_marks_first_input_ciphertext_as_unfresh(
        self, scheme: _SupportsMultiplicationES
    ) -> None:
        """
        Test that `mul(ct, pt)` marks `ct` ciphertext as unfresh.

        :param scheme: Scheme under test.
        """
        fresh_ct = scheme.encrypt(0)
        scheme.mul(fresh_ct, 0)
        assert not fresh_ct.fresh

    def test_multiplication_with_fresh_first_ciphertext_returns_fresh_ciphertext(
        self, scheme: _SupportsMultiplicationES
    ) -> None:
        """
        Test that `mul(ct, pt)` returns a fresh output ciphertext if `ct` is fresh.

        :param scheme: Scheme under test.
        """
        fresh_ct = scheme.encrypt(0)
        res = scheme.mul(fresh_ct, 0)
        assert res.fresh

    def test_multiplication_with_unfresh_first_ciphertext_returns_unfresh_ciphertext(
        self, scheme: _SupportsMultiplicationES
    ) -> None:
        """
        Test that `mul(ct, pt)` returns an unfresh output ciphertext if `ct `is unfresh.

        :param scheme: Scheme under test.
        """
        unfresh_ct = scheme.unsafe_encrypt(0)
        res = scheme.mul(unfresh_ct, 0)
        assert not res.fresh


class BaseTestAdditiveHomomorphicEncryptionScheme(
    _BaseTestHomomorphicEncryptionSchemeMul
):
    """
    Tests for additive properties of additive homomorphic encryption schemes.

    Please refer to the documentation of `BaseTestHomomorphicEncryptionScheme` for usage
    instructions.
    """

    # region default fixtures

    @pytest.fixture(name="value_add")
    def fixture_value_add(self, value: PT) -> PT:
        """
        Plaintext value to use in addition tests.

        :param value: Plaintext value to use.
        :return: Plaintext value.
        """
        return value

    @pytest.fixture(name="value_sub")
    def fixture_value_sub(self, value: PT) -> PT:
        """
        Plaintext value to use in subtraction tests.

        :param value: Plaintext value to use.
        :return: Plaintext value.
        """
        return value

    @pytest.fixture(name="value_mul")
    def fixture_value_mul(self, value: PT) -> PT:
        """
        Plaintext value to use in multiplication tests.

        :param value: Plaintext value to use.
        :return: Plaintext value.
        """
        return value

    @pytest.fixture(name="ciphertext_neg")
    def fixture_ciphertext_neg(self, ciphertext: HomomorphicCT) -> HomomorphicCT:
        """
        Ciphertext to use in negation tests.

        :param ciphertext: Ciphertext to use.
        :return: Ciphertext.
        """
        return ciphertext

    @pytest.fixture(name="ciphertext_add")
    def fixture_ciphertext_add(self, ciphertext: HomomorphicCT) -> HomomorphicCT:
        """
        Ciphertext to use in addition tests.

        :param ciphertext: Ciphertext to use.
        :return: Ciphertext.
        """
        return ciphertext

    @pytest.fixture(name="ciphertext_sub")
    def fixture_ciphertext_sub(self, ciphertext: HomomorphicCT) -> HomomorphicCT:
        """
        Ciphertext to use in subtraction tests.

        :param ciphertext: Ciphertext to use.
        :return: Ciphertext.
        """
        return ciphertext

    @pytest.fixture(name="ciphertext_mul")
    def fixture_ciphertext_mul(self, ciphertext: HomomorphicCT) -> HomomorphicCT:
        """
        Ciphertext to use in multiplication tests.

        :param ciphertext: Ciphertext to use.
        :return: Ciphertext.
        """
        return ciphertext

    @pytest.fixture(name="ciphertext_pair_add")
    def fixture_ciphertext_pair_add(
        self, ciphertext_pair: tuple[AdditiveHomomorphicCT, AdditiveHomomorphicCT]
    ) -> tuple[AdditiveHomomorphicCT, AdditiveHomomorphicCT]:
        """
        Ciphertext pair to use in addition tests.

        :param ciphertext_pair: Ciphertext pair to use.
        :return: Ciphertext pair.
        """
        return ciphertext_pair

    @pytest.fixture(name="ciphertext_pair_sub")
    def fixture_ciphertext_pair_sub(
        self, ciphertext_pair: tuple[AdditiveHomomorphicCT, AdditiveHomomorphicCT]
    ) -> tuple[AdditiveHomomorphicCT, AdditiveHomomorphicCT]:
        """
        Ciphertext pair to use in subtraction tests.

        :param ciphertext_pair: Ciphertext pair to use.
        :return: Ciphertext pair.
        """
        return ciphertext_pair

    # endregion

    def test_negation_of_ciphertext(
        self,
        scheme: AdditiveHomomorphicES,
        ciphertext_neg: AdditiveHomomorphicCT,
    ) -> None:
        """
        Test that negation of a ciphertext yields the expected result.

        :param scheme: Encryption scheme under test.
        :param ciphertext_neg: Ciphertext under test.
        """
        expected_negation = -scheme.decrypt(ciphertext_neg)
        assert expected_negation == scheme.decrypt(-ciphertext_neg)

    def test_addition_with_plaintext(
        self,
        scheme: AdditiveHomomorphicES,
        ciphertext_add: AdditiveHomomorphicCT,
        value_add: PT,
    ) -> None:
        """
        Test that addition of a ciphertext with a scalar (plaintext) value yields the expected result.

        :param scheme: Encryption scheme under test.
        :param ciphertext_add: Ciphertext under test.
        :param value_add: Plaintext under test.
        """
        expected_sum = scheme.decrypt(ciphertext_add) + value_add
        assert expected_sum == scheme.decrypt(ciphertext_add + value_add)

    def test_addition_with_ciphertext(
        self,
        scheme: AdditiveHomomorphicES,
        ciphertext_pair_add: tuple[AdditiveHomomorphicCT, AdditiveHomomorphicCT],
    ) -> None:
        """
        Test that addition of a ciphertext with another ciphertext value yields the expected result.

        :param scheme: Encryption scheme under test.
        :param ciphertext_pair_add: Ciphertext pair under test.
        """
        c1, c2 = ciphertext_pair_add
        expected_sum = scheme.decrypt(c1) + scheme.decrypt(c2)
        assert expected_sum == scheme.decrypt(c1 + c2)

    def test_subtraction_with_plaintext(
        self,
        scheme: HomomorphicES,
        ciphertext_sub: AdditiveHomomorphicCT,
        value_sub: PT,
    ) -> None:
        """
        Test that subtraction of a ciphertext and a plaintext yields the expected result.

        :param scheme: Encryption scheme under test.
        :param ciphertext_sub: Ciphertext under test.
        :param value_sub: Plaintext under test.
        """
        expected_diff = scheme.decrypt(ciphertext_sub) - value_sub
        assert expected_diff == scheme.decrypt(ciphertext_sub - value_sub)

    def test_subtraction_with_ciphertext(
        self,
        scheme: AdditiveHomomorphicES,
        ciphertext_pair_sub: tuple[AdditiveHomomorphicCT, AdditiveHomomorphicCT],
    ) -> None:
        """
        Test that subtraction of a ciphertext and a plaintext yields the expected result.

        :param scheme: Encryption scheme under test.
        :param ciphertext_pair_sub: Ciphertext pair under test.
        """
        c1, c2 = ciphertext_pair_sub
        expected_diff = scheme.decrypt(c1) - scheme.decrypt(c2)
        assert expected_diff == scheme.decrypt(c1 - c2)

    def test_addition_marks_first_input_ciphertext_as_unfresh(
        self, scheme: AdditiveHomomorphicES
    ) -> None:
        """
        Test that `add(arg1, 0)` marks arg1 unfresh.

        :param scheme: Scheme under test.
        """
        fresh_ct = scheme.encrypt(0)
        scheme.add(fresh_ct, 0)
        assert not fresh_ct.fresh

    def test_addition_marks_second_input_ciphertext_as_unfresh(
        self, scheme: AdditiveHomomorphicES
    ) -> None:
        """
        Test that `add(arg1, arg2)` marks ciphertext `arg2` as unfresh.

        :param scheme: Scheme under test.
        """
        fresh_ct_1 = scheme.encrypt(0)
        fresh_ct_2 = scheme.encrypt(0)
        scheme.add(fresh_ct_1, fresh_ct_2)
        assert not fresh_ct_2.fresh

    def test_addition_with_fresh_first_ciphertext_returns_fresh_ciphertext(
        self, scheme: AdditiveHomomorphicES
    ) -> None:
        """
        Test that `add(arg1, arg2)` returns a fresh output ciphertext if `arg1` is fresh.

        :param scheme: Scheme under test.
        """
        fresh_ct = scheme.encrypt(0)
        res = scheme.add(fresh_ct, 0)
        assert res.fresh

    def test_addition_with_fresh_first_ciphertext_raises_efficiency_warning(
        self,
        scheme: AdditiveHomomorphicES,
    ) -> None:
        """
        Test that `add(arg1, 0)` raises an efficiency warning if `arg1` is a fresh ciphertext.

        :param scheme: Encryption scheme under test.
        """
        fresh_ct = scheme.encrypt(0)
        with pytest.warns(RandomizedEncryptionSchemeWarning):
            scheme.add(fresh_ct, 0)

    def test_addition_with_fresh_second_ciphertext_returns_fresh_ciphertext(
        self, scheme: AdditiveHomomorphicES
    ) -> None:
        """
        Test that `add(arg1, arg2)` returns a fresh output ciphertext if `arg2` is fresh.

        :param scheme: Scheme under test.
        """
        unfresh_ct = scheme.unsafe_encrypt(0)
        fresh_ct = scheme.encrypt(0)
        res = scheme.add(unfresh_ct, fresh_ct)
        assert res.fresh

    def test_addition_with_fresh_second_ciphertext_raises_efficiency_warning(
        self,
        scheme: AdditiveHomomorphicES,
    ) -> None:
        """
        Test that `add(arg1, arg2)` raises an efficiency warning if `arg2` is a fresh ciphertext.

        :param scheme: Encryption scheme under test.
        """
        unfresh_ct = scheme.unsafe_encrypt(0)
        fresh_ct = scheme.encrypt(0)
        with pytest.warns(RandomizedEncryptionSchemeWarning):
            scheme.add(unfresh_ct, fresh_ct)

    def test_addition_with_unfresh_ciphertexts_returns_unfresh_ciphertext(
        self, scheme: AdditiveHomomorphicES
    ) -> None:
        """
        Test that `add(arg1, arg2)` returns an unfresh output ciphertext if both `arg1` and `arg2` are
        unfresh.

        :param scheme: Scheme under test.
        """
        unfresh_ct = scheme.unsafe_encrypt(0)
        res = scheme.add(unfresh_ct, 0)
        assert not res.fresh

    def test_addition_with_unfresh_ciphertext_raises_no_efficiency_warning(
        self,
        recwarn: WarningsRecorder,
        scheme: AdditiveHomomorphicES,
    ) -> None:
        """
        Test that `add(arg1, arg2)` raises no efficiency warning if `arg1` and `arg2` are both unfresh
        ciphertexts.

        :param recwarn: Pytest recwarn fixture.
        :param scheme: Encryption scheme under test.
        """
        unfresh_ct_1 = scheme.unsafe_encrypt(0)
        unfresh_ct_2 = scheme.unsafe_encrypt(0)
        scheme.add(unfresh_ct_1, unfresh_ct_2)
        assert _assert_no_es_warnings(recwarn)


class BaseTestMultiplicativeHomomorphicEncryptionScheme(
    _BaseTestHomomorphicEncryptionSchemeMul
):
    """
    Tests for multiplicative properties of multiplicative homomorphic encryption schemes.

    Please refer to the documentation of `BaseTestHomomorphicEncryptionScheme` for usage
    instructions.
    """

    # region default fixtures

    @pytest.fixture(name="value_mul")
    def fixture_value_mul(self, value: PT) -> PT:
        """
        Plaintext value to use in multiplication tests.

        :param value: Plaintext value to use.
        :return: Plaintext value.
        """
        return value

    @pytest.fixture(name="ciphertext_mul")
    def fixture_ciphertext_mul(self, ciphertext: HomomorphicCT) -> HomomorphicCT:
        """
        Ciphertext to use in multiplication tests.

        :param ciphertext: Ciphertext to use.
        :return: Ciphertext.
        """
        return ciphertext

    @pytest.fixture(name="ciphertext_pair_mul")
    def fixture_ciphertext_pair_mul(
        self,
        ciphertext_pair: tuple[
            MultiplicativeHomomorphicCT, MultiplicativeHomomorphicCT
        ],
    ) -> tuple[MultiplicativeHomomorphicCT, MultiplicativeHomomorphicCT]:
        """
        Ciphertext pair to use in multiplication tests.

        :param ciphertext_pair: Ciphertext pair to use.
        :return: Ciphertext pair.
        """
        return ciphertext_pair

    # endregion

    def test_multiplication_with_ciphertext(
        self,
        scheme: MultiplicativeHomomorphicES,
        ciphertext_pair_mul: tuple[
            MultiplicativeHomomorphicCT, MultiplicativeHomomorphicCT
        ],
    ) -> None:
        """
        Test that multiplication of a ciphertext with another ciphertext value yields the expected result.

        :param scheme: Encryption scheme under test.
        :param ciphertext_pair_mul: Ciphertext pair under test.
        """
        c1, c2 = ciphertext_pair_mul
        expected_prod = scheme.decrypt(c1) * scheme.decrypt(c2)
        assert expected_prod == scheme.decrypt(c1 * c2)

    def test_multiplication_marks_second_input_ciphertext_as_unfresh(
        self, scheme: MultiplicativeHomomorphicES
    ) -> None:
        """
        Test that `mul(arg1, arg2)` marks ciphertext `arg2` as unfresh.

        :param scheme: Scheme under test.
        """
        fresh_ct_1 = scheme.encrypt(0)
        fresh_ct_2 = scheme.encrypt(0)
        scheme.mul(fresh_ct_1, fresh_ct_2)
        assert not fresh_ct_2.fresh

    def test_multiplication_with_unfresh_second_ciphertext_raises_no_efficiency_warning(
        self,
        recwarn: WarningsRecorder,
        scheme: MultiplicativeHomomorphicES,
    ) -> None:
        """
        Test that `mul(arg1, arg2)` raises no efficiency warning if `arg1` and `arg2` are both unfresh
        ciphertexts.

        :param recwarn: Pytest recwarn fixture.
        :param scheme: Encryption scheme under test.
        """
        unfresh_ct_1 = scheme.unsafe_encrypt(0)
        unfresh_ct_2 = scheme.unsafe_encrypt(0)
        scheme.mul(unfresh_ct_1, unfresh_ct_2)
        assert _assert_no_es_warnings(recwarn)

    def test_multiplication_with_fresh_second_ciphertext_raises_efficiency_warning(
        self,
        scheme: MultiplicativeHomomorphicES,
    ) -> None:
        """
        Test that `mul(arg1, arg2)` raises an efficiency warning if `arg2` is a fresh ciphertext.

        :param scheme: Encryption scheme under test.
        """
        unfresh_ct = scheme.unsafe_encrypt(0)
        fresh_ct = scheme.encrypt(0)
        with pytest.warns(RandomizedEncryptionSchemeWarning):
            scheme.mul(unfresh_ct, fresh_ct)

    def test_multiplication_with_fresh_second_ciphertext_returns_fresh_ciphertext(
        self, scheme: MultiplicativeHomomorphicES
    ) -> None:
        """
        Test that `mul(arg1, arg2)` returns a fresh output ciphertext if `arg2` is fresh.

        :param scheme: Scheme under test.
        """
        unfresh_ct = scheme.unsafe_encrypt(0)
        fresh_ct = scheme.encrypt(0)
        res = scheme.mul(unfresh_ct, fresh_ct)
        assert res.fresh


class TestFullyHomomorphicCiphertext(
    BaseTestHomomorphicCiphertext,
    BaseTestAdditiveHomomorphicCiphertext,
    BaseTestMultiplicativeHomomorphicCiphertext,
):
    """
    Example test class for an implemented fully homomorphic encryption scheme's ciphertext.

    Tests for of an implemented homomorphic encryption scheme's ciphertext are easily adopted by
    implementing from BaseTestHomomorphicCiphertext and more specialized classes as shown for this
    class. Additionally, it should probably inherit from BaseTestRandomizableCiphertext.
    """

    @pytest.fixture(name="ciphertext", scope="class")
    def fixture_ciphertext(self) -> DummyHomomorphicCiphertext:
        return DummyHomomorphicCiphertext(raw_value=0, scheme=DummyHomomorphicScheme(0))


_TEST_VALUES = [-5, 0, 5]


class TestFullyHomomorphicES(
    BaseTestHomomorphicEncryptionScheme,
    BaseTestAdditiveHomomorphicEncryptionScheme,
    BaseTestMultiplicativeHomomorphicEncryptionScheme,
):
    """
    Example test class for an implemented fully homomorphic encryption scheme.

    Tests for of an implemented homomorphic encryption scheme are easily adopted by implementing
    from BaseTestHomomorphicEncryptionScheme and more specialized classes as shown for this class.
    Additionally, it should probably inherit from BaseTestRandomizedHomomorphicEncryptionScheme.
    """

    @pytest.fixture(name="scheme", scope="class")
    def fixture_scheme(self) -> DummyHomomorphicScheme:
        """
        Fixture for the scheme under test.

        :return: Scheme under test.
        """
        return DummyHomomorphicScheme(0)

    @pytest.fixture(name="same_scheme", scope="class")
    def fixture_same_scheme(self) -> DummyHomomorphicScheme:
        """
        Fixture for the scheme under test.

        :return: Scheme under test.
        """
        return DummyHomomorphicScheme(0)

    @pytest.fixture(name="different_scheme", scope="class")
    def fixture_different_scheme(self) -> DummyHomomorphicScheme:
        """
        Fixture for the scheme under test.

        :return: Scheme under test.
        """
        return DummyHomomorphicScheme(99)

    @pytest.fixture(name="value", scope="class", params=_TEST_VALUES)
    def fixture_value(self, request: FixtureRequest) -> int:
        """
        Fixture for returning plaintext values to use in all encryption scheme tests.

        :param request: Pytest request fixture.
        :return: Plaintext value.
        """
        return cast(int, request.param)

    @pytest.fixture(name="ciphertext", scope="class", params=_TEST_VALUES)
    def fixture_ciphertext(
        self, request: FixtureRequest, scheme: DummyHomomorphicScheme
    ) -> DummyHomomorphicCiphertext:
        """
        Fixture for returning ciphertexts to use in all encryption scheme tests.

        :param request: Pytest request fixture.
        :param scheme: Scheme under test.
        :return: Ciphertext.
        """
        return scheme.encrypt(request.param)

    @pytest.fixture(
        name="ciphertext_pair",
        scope="class",
        params=_TEST_VALUES,
        ids=lambda x: str(_duplicate(x)),
    )
    def fixture_ciphertext_pair(
        self, request: FixtureRequest, scheme: DummyHomomorphicScheme
    ) -> tuple[DummyHomomorphicCiphertext, DummyHomomorphicCiphertext]:
        """
        Fixture for returning ciphertext pairs to use in all encryption scheme tests.

        :param request: Pytest request fixture.
        :param scheme: Scheme under test.
        :return: Ciphertext pair.
        """
        v1, v2 = _duplicate(request.param)
        return (scheme.encrypt(v1), scheme.encrypt(v2))


def _duplicate(n: int) -> tuple[int, int]:
    """
    Duplicate a number.

    :param n: Number to duplicate
    :return: Tuple that contains two copies of n.
    """
    return (n, n)
