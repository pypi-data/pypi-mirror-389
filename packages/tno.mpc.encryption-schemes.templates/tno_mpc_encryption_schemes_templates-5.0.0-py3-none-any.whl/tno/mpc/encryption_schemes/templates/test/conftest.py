"""
Imports this package's pytest fixtures so that they work even when the package is not
installed.
"""

# pylint: disable

from __future__ import annotations

import itertools
import sys
import warnings
from typing import Any
from warnings import WarningMessage

from pytest import WarningsRecorder

from tno.mpc.encryption_schemes.templates import (
    AsymmetricEncryptionScheme,
    EncodedPlaintext,
    FullyHomomorphicCiphertext,
    FullyHomomorphicEncryptionScheme,
    PublicKey,
    RandomizableCiphertext,
    RandomizedEncryptionScheme,
    RandomizedEncryptionSchemeWarning,
    SecretKey,
)
from tno.mpc.encryption_schemes.templates.encryption_scheme import PT
from tno.mpc.encryption_schemes.templates.exceptions import (
    WARN_INEFFICIENT_HOM_OPERATION,
)
from tno.mpc.encryption_schemes.templates.test.pytest_plugins import (  # noqa, pylint: disable=useless-import-alias,unused-import
    restore_encryption_scheme_instances as restore_encryption_scheme_instances,
)

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override


_randomness_counter = itertools.count()
next(_randomness_counter)  # skip 0


class DummyPublicKey(PublicKey):
    """
    Dummy public key for tests.
    """


class DummySecretKey(SecretKey):
    """
    Dummy secret key for tests.
    """


class DummyRandomizableCiphertext(
    RandomizableCiphertext[int, int],
):
    """
    Dummy RandomizableCiphertext for tests.
    """

    def __init__(
        self,
        raw_value: int,
        scheme: RandomizedEncryptionScheme[Any, Any, Any, Self, Any],
        *,
        fresh: bool = False,
    ) -> None:
        """
        Dummy RandomizableCiphertext.

        We keep track of all added randomness so that the corresponding scheme can reverse the
        randomization.

        :param raw_value: Raw ciphertext value.
        :param scheme: Corresponding encryption scheme.
        :param fresh: Whether the ciphertext is fresh.
        """
        self._added_randomness = 0
        super().__init__(raw_value, scheme, fresh=fresh)

    def apply_randomness(self, randomization_value: Any) -> None:
        """
        Stub

        :param randomization_value: -
        """
        self._raw_value += randomization_value
        self._added_randomness += randomization_value

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and self._raw_value == other._raw_value
            and self.scheme == other.scheme
        )


class DummyHomomorphicCiphertext(
    DummyRandomizableCiphertext,
    FullyHomomorphicCiphertext[int, int, int],
):
    """
    Dummy RandomizableCiphertext for tests.
    """

    scheme: DummyHomomorphicScheme

    # The use of Self in the signature of FullyHomomorphicCiphertext.__mul__ combined with multiple
    # inheritance confuses mypy, so we override __mul__ here for mypy to understand Self.
    @override
    def __mul__(
        self, other: DummyHomomorphicCiphertext | PT
    ) -> DummyHomomorphicCiphertext:
        """
        Multiply other with the underlying plaintext of this ciphertext.

        :param other: Plaintext or ciphertext to multiply with.
        :return: Multiplication of other with this ciphertext.
        """
        try:
            return self.scheme.mul(self, other)
        except NotImplementedError:
            return NotImplemented

    __rmul__ = __mul__


class _DummyScheme(
    AsymmetricEncryptionScheme[
        DummyPublicKey, DummySecretKey, int, Any, DummyHomomorphicCiphertext
    ],
):
    def __init__(self, dummy_value: int) -> None:
        r"""
        Create a dummy scheme with some dummy identifier for tests.

        :param dummy_value: Dummy identifier, used for scheme equality tests.
        :param \**kwargs: Optional extra arguments for this EncryptionScheme.
        """
        AsymmetricEncryptionScheme.__init__(self, DummyPublicKey(), None)
        self.dummy_value = dummy_value

    @classmethod
    def from_security_parameter(cls, security_parameter: int) -> Self:
        """
        Dummy

        :param security_parameter: -
        :raise NotImplementedError: always
        :return: -
        """
        raise NotImplementedError()

    @classmethod
    def id_from_arguments(cls, dummy_value: int) -> int:
        """
        Generate a unique id from the dummy_value attribute of this scheme.

        :param dummy_value: Dummy value.
        :return: Numeric id
        """
        return dummy_value

    @staticmethod
    def generate_key_material(
        *args: Any, **kwargs: Any
    ) -> tuple[DummyPublicKey, DummySecretKey]:
        r"""
        Stub

        :param \*args: -
        :param \**kwargs: -
        :return: -
        """
        raise NotImplementedError()

    def encode(self, plaintext: Any) -> EncodedPlaintext[Any]:
        """
        Dummy encoding of plaintext.

        :param plaintext: Plaintext to encode.
        :return: Dummy encoding of plaintext.
        """
        return EncodedPlaintext(value=plaintext, scheme=self)

    def decode(self, encoded_plaintext: EncodedPlaintext[Any]) -> Any:
        """
        Decoding of dummy encoded plaintext.

        :param encoded_plaintext: Encoded plaintext to be decoded.
        :return: Decoded plaintext
        """
        return encoded_plaintext.value

    @staticmethod
    def _generate_randomness() -> int:
        """
        Method to generate randomness for this particular scheme.

        :return: A list containing number_of_randomizations random numbers.
        """
        return next(_randomness_counter)

    def __eq__(self, other: object) -> bool:
        """
        Stub

        :param other: -
        :return: -
        """
        return isinstance(other, type(self)) and self.dummy_value == other.dummy_value


class DummyRandomizedScheme(
    _DummyScheme,
    RandomizedEncryptionScheme[
        tuple[DummyPublicKey, DummySecretKey],
        int,
        Any,
        DummyRandomizableCiphertext,
        int,
    ],
):
    """
    Dummy RandomizedEncryptionScheme.
    """

    def __init__(self, dummy_value: int = 42) -> None:
        _DummyScheme.__init__(self, dummy_value=dummy_value)
        RandomizedEncryptionScheme.__init__(self)

    def _unsafe_encrypt_raw(
        self, plaintext: EncodedPlaintext[Any]
    ) -> DummyRandomizableCiphertext:
        """
        Method to encrypt an encoded plaintext value to a ciphertext without randomization.

        :param plaintext: an encoded plaintext to encrypt
        :return: a ciphertext
        """
        return DummyRandomizableCiphertext(plaintext.value, self)

    def _decrypt_raw(
        self, ciphertext: DummyRandomizableCiphertext
    ) -> EncodedPlaintext[Any]:
        """
        Decryption of dummy encrypted ciphertext.

        :param ciphertext: Ciphertext to be decrypted
        :return: Dummy encoded decryption of the given ciphertext.
        """
        return EncodedPlaintext(value=ciphertext.value, scheme=self)


class DummyHomomorphicScheme(
    _DummyScheme,
    FullyHomomorphicEncryptionScheme[
        tuple[DummyPublicKey, DummySecretKey], int, Any, DummyHomomorphicCiphertext, int
    ],
):
    """
    Dummy HomomorphicEncrypionScheme.
    """

    def __init__(self, dummy_value: int = 42) -> None:
        _DummyScheme.__init__(self, dummy_value=dummy_value)
        RandomizedEncryptionScheme.__init__(self)

    def _unsafe_encrypt_raw(
        self, plaintext: EncodedPlaintext[Any]
    ) -> DummyHomomorphicCiphertext:
        """
        Dummy encryption of encoded plaintext.

        :param plaintext: Plaintext to encrypt
        :return: Raw dummy encryption of plaintext.
        """
        return DummyHomomorphicCiphertext(raw_value=plaintext.value, scheme=self)

    def _decrypt_raw(
        self, ciphertext: DummyRandomizableCiphertext
    ) -> EncodedPlaintext[Any]:
        """
        Decryption of dummy encrypted ciphertext.

        :param ciphertext: Ciphertext to be decrypted.
        :return: Dummy encoded decryption of the given ciphertext.
        """
        return EncodedPlaintext(
            value=ciphertext.get_value() - ciphertext._added_randomness, scheme=self
        )

    def neg(self, ciphertext: DummyHomomorphicCiphertext) -> DummyHomomorphicCiphertext:
        """
        Stub

        :param ciphertext: -
        :return: -
        """
        return type(ciphertext)(
            raw_value=-(ciphertext.get_value() - ciphertext._added_randomness),
            scheme=ciphertext.scheme,
        )

    def add(
        self,
        ciphertext: DummyHomomorphicCiphertext,
        other: DummyHomomorphicCiphertext | PT,
    ) -> DummyHomomorphicCiphertext:
        """
        Stub

        :param ciphertext: -
        :param ciphertext_2: -
        :return: -
        """
        c_type = type(ciphertext)
        c_scheme = ciphertext.scheme
        if c_fresh := ciphertext.fresh:
            warnings.warn(
                WARN_INEFFICIENT_HOM_OPERATION, RandomizedEncryptionSchemeWarning
            )

        # ciphertext.get_value() automatically marks ciphertext as not fresh
        c_val = ciphertext.get_value() - ciphertext._added_randomness
        if isinstance(other, DummyRandomizableCiphertext):
            if fresh := c_fresh or other.fresh:
                warnings.warn(
                    WARN_INEFFICIENT_HOM_OPERATION, RandomizedEncryptionSchemeWarning
                )
            return c_type(
                raw_value=c_val + other.get_value() - other._added_randomness,
                scheme=c_scheme,
                fresh=fresh,
            )
        if isinstance(other, int):
            return c_type(raw_value=c_val + other, scheme=c_scheme, fresh=c_fresh)
        raise NotImplementedError()

    def mul(
        self,
        ciphertext: DummyHomomorphicCiphertext,
        other: DummyHomomorphicCiphertext | PT,
    ) -> DummyHomomorphicCiphertext:
        """
        Stub

        :param ciphertext: -
        :param other: -
        :return: -
        """
        c_type = type(ciphertext)
        c_scheme = ciphertext.scheme
        if c_fresh := ciphertext.fresh:
            warnings.warn(
                WARN_INEFFICIENT_HOM_OPERATION, RandomizedEncryptionSchemeWarning
            )

        # ciphertext.get_value() automatically marks ciphertext as not fresh
        c_val = ciphertext.get_value() - ciphertext._added_randomness
        if isinstance(other, DummyRandomizableCiphertext):
            if fresh := c_fresh or other.fresh:
                warnings.warn(
                    WARN_INEFFICIENT_HOM_OPERATION, RandomizedEncryptionSchemeWarning
                )
            return c_type(
                raw_value=c_val * (other.get_value() - other._added_randomness),
                scheme=c_scheme,
                fresh=fresh,
            )
        if isinstance(other, int):
            return c_type(raw_value=c_val * other, scheme=c_scheme, fresh=c_fresh)
        raise NotImplementedError()


def _assert_no_es_warnings(record: WarningsRecorder) -> tuple[bool, str]:
    """
    Assert that the warningsrecord does not contain EncryptionSchemeWarnings.

    :param record: Record with warnings.
    :return: Tuple where the first element is a boolean indicating if there were no warnings, and
        the second element is a string with an error message in case there were warnings.
    """
    es_warnings = list(map(_is_encryption_scheme_warning, record))
    no_warnings = len(es_warnings) == 0
    warning_msg = (
        ""
        if no_warnings
        else f"Expected no EncryptionScheme warnings, but received {len(es_warnings)} warnings. First warning:\n{es_warnings[0]}"
    )
    return no_warnings, warning_msg


def _is_encryption_scheme_warning(wm: WarningMessage) -> bool:
    return not issubclass(wm.category, RandomizedEncryptionSchemeWarning)
