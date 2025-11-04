"""
Abstract base classes for various types of Homomorphic Encryption Schemes.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from tno.mpc.encryption_schemes.templates._randomness_manager import RR
from tno.mpc.encryption_schemes.templates.encryption_scheme import CV, KM, PT, RP
from tno.mpc.encryption_schemes.templates.randomized_encryption_scheme import (
    RandomizableCiphertext,
    RandomizedEncryptionScheme,
)

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override

T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class SupportsNeg(Protocol[T_co]):  # pylint: disable=too-few-public-methods
    """
    An ABC with one abstract method __neg__.
    """

    __slots__ = ()

    def __neg__(self) -> T_co: ...


HomomorphicCT = TypeVar("HomomorphicCT", bound="HomomorphicCiphertext[Any, Any, Any]")


class HomomorphicCiphertext(Generic[PT, CV, RR], RandomizableCiphertext[CV, RR]):
    """
    HomomorphicCiphertext objects delegate relevant binary operations to the corresponding
    homomorphic encryption scheme.
    """

    scheme: HomomorphicEncryptionScheme[Any, PT, Any, Self, RR]  # type: ignore[assignment]


AdditiveHomomorphicCT = TypeVar(
    "AdditiveHomomorphicCT", bound="AdditiveHomomorphicCiphertext[Any, Any, Any]"
)


class AdditiveHomomorphicCiphertext(HomomorphicCiphertext[PT, CV, RR]):
    """
    AdditiveHomomorphicCiphertext objects delegate binary operations such as addition and
    multiplication to the corresponding additive homomorphic encryption scheme.
    """

    scheme: AdditiveHomomorphicEncryptionScheme[Any, PT, Any, Self, RR]  # type: ignore[assignment]

    def __neg__(self) -> Self:
        """
        Negate the underlying plaintext of this ciphertext.

        :return: Negated ciphertext.
        """
        return self.scheme.neg(self)

    def __add__(self, other: Self | PT) -> Self:
        """
        Add other to the underlying plaintext of this ciphertext.

        :param other: Plaintext or ciphertext to add to self.
        :return: Addition of other to this ciphertext.
        """
        try:
            return self.scheme.add(self, other)
        except NotImplementedError:
            return NotImplemented

    __radd__ = __add__

    def __sub__(self, other: Self | PT) -> Self:
        """
        Subtract other from the underlying plaintext of this ciphertext.

        :param other: Plaintext or ciphertext to subtract from self.
        :raise TypeError: The other object has an unsupported type for subtraction from this
            ciphertext.
        :return: Subtraction of other from this ciphertext.
        """
        if not isinstance(other, SupportsNeg):
            # other.__neg__ does not exist; workaround via self.__rsub__ and self.__neg__
            return -(other - self)
        try:
            return self.scheme.add(self, -other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: Self | PT) -> Self:
        """
        Subtract other from the underlying plaintext of this ciphertext.

        :param other: Plaintext or ciphertext to subtract from.
        :return: Subtraction of other from this ciphertext.
        """
        try:
            return self.scheme.add(-self, other)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: Self | PT) -> Self:
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


MultiplicativeHomomorphicCT = TypeVar(
    "MultiplicativeHomomorphicCT",
    bound="MultiplicativeHomomorphicCiphertext[Any, Any, Any]",
)


class MultiplicativeHomomorphicCiphertext(HomomorphicCiphertext[PT, CV, RR]):
    """
    MultiplicativeHomomorphicCiphertext objects delegate binary operations such as multiplication
    to the corresponding additive homomorphic encryption scheme.
    """

    scheme: MultiplicativeHomomorphicEncryptionScheme[Any, PT, Any, Self, RR]  # type: ignore[assignment]

    def __mul__(self, other: Self | PT) -> Self:
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


FullyHomomorphicCT = TypeVar(
    "FullyHomomorphicCT",
    bound="FullyHomomorphicCiphertext[Any, Any, Any]",
)


class FullyHomomorphicCiphertext(
    AdditiveHomomorphicCiphertext[PT, CV, RR],
    MultiplicativeHomomorphicCiphertext[PT, CV, RR],
):
    """
    MultiplicativeHomomorphicCiphertext objects delegate binary operations such as multiplication
    to the corresponding additive homomorphic encryption scheme.
    """

    scheme: FullyHomomorphicEncryptionScheme[Any, PT, Any, Self, RR]  # type: ignore[assignment]

    # The use of Self in the signature of Additive/MultiplicativeHomomorphicCiphertext.__mul__
    # combined with multiple inheritance confuses mypy, so we override __mul__ here for mypy to
    # understand Self.
    @override
    def __mul__(self, other: Self | PT) -> Self:
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


HomomorphicES = TypeVar(
    "HomomorphicES",
    bound="HomomorphicEncryptionScheme[Any, Any, Any, Any, Any]",
)


class HomomorphicEncryptionScheme(
    RandomizedEncryptionScheme[KM, PT, RP, HomomorphicCT, RR]
):
    """
    Abstract base class to define generic Homomorphic Encryption Scheme functionality.

    Most easily constructed using the from_security_parameter method.
    """

    # Redefining __init__ here somehow avoids mypy issues such as the following:
    # > Argument 1 to "__init__" of "RandomizedEncryptionScheme" has incompatible type "Paillier";
    # > expected "RandomizedEncryptionScheme[KM, PT, RP, RandomizableCT, RR]"  [arg-type]
    __init__ = RandomizedEncryptionScheme.__init__


AdditiveHomomorphicES = TypeVar(
    "AdditiveHomomorphicES",
    bound="AdditiveHomomorphicEncryptionScheme[Any, Any, Any, Any, Any]",
)


class AdditiveHomomorphicEncryptionScheme(
    HomomorphicEncryptionScheme[KM, PT, RP, AdditiveHomomorphicCT, RR], ABC
):
    """
    Abstract base class to define Additive Homomorphic Encryption Scheme functionality.

    Most easily constructed using the `from_security_parameter` method.
    """

    @abstractmethod
    def neg(self, ciphertext: AdditiveHomomorphicCT) -> AdditiveHomomorphicCT:
        """
        Negate the underlying plaintext of this ciphertext. I.e. if the original plaintext of this
        ciphertext was 5 this method returns the ciphertext that has -5 as underlying plaintext.

        :param ciphertext: Ciphertext of which the underlying plaintext should be negated.
        :raise NotImplementedError: Raised when negation is not supported by this scheme.
        :return: Ciphertext object corresponding to the negated plaintext.
        """

    @abstractmethod
    def add(
        self,
        ciphertext: AdditiveHomomorphicCT,
        other: AdditiveHomomorphicCT | PT,
    ) -> AdditiveHomomorphicCT:
        """
        Add the underlying plaintext value of ciphertext with the (underlying) plaintext value of
        other. Where other can either be another ciphertext or a plaintext, depending on the
        scheme.

        :param ciphertext: First Ciphertext of which the underlying plaintext is added.
        :param other: Plaintext or ciphertext to add to self.
        :raise NotImplementedError: Raised when addition is not supported by this scheme.
        :return: A Ciphertext containing the encryption of the addition of both values.
        """

    @abstractmethod
    def mul(
        self,
        ciphertext: AdditiveHomomorphicCT,
        other: AdditiveHomomorphicCT | PT,
    ) -> AdditiveHomomorphicCT:
        """
        Multiply the underlying plaintext value of ciphertext with a plaintext value.

        :param ciphertext: Ciphertext of which the underlying plaintext is multiplied.
        :param other: Plaintext or ciphertext to multiply with.
        :raise NotImplementedError: Raised when multiplication is not supported by this scheme.
        :return: A Ciphertext containing the encryption of the product of both values.
        """


MultiplicativeHomomorphicES = TypeVar(
    "MultiplicativeHomomorphicES",
    bound="MultiplicativeHomomorphicEncryptionScheme[Any, Any, Any, Any, Any]",
)


class MultiplicativeHomomorphicEncryptionScheme(
    HomomorphicEncryptionScheme[KM, PT, RP, MultiplicativeHomomorphicCT, RR], ABC
):
    """
    Abstract base class to define Multiplicative Homomorphic Encryption Scheme functionality.

    Most easily constructed using the `from_security_parameter` method.
    """

    @abstractmethod
    def mul(
        self,
        ciphertext: MultiplicativeHomomorphicCT,
        other: MultiplicativeHomomorphicCT | PT,
    ) -> MultiplicativeHomomorphicCT:
        """
        Multiply the underlying plaintext value of ciphertext with the (underlying) plaintext value
        of other. Where other can either be another ciphertext or a plaintext, depending on the
        scheme.

        :param ciphertext: First Ciphertext of which the underlying plaintext is multiplied.
        :param other: Plaintext or ciphertext to multiply with.
        :raise NotImplementedError: Raised when multiplication is not supported by this scheme.
        :return: A Ciphertext containing the encryption of the product of both values.
        """


class FullyHomomorphicEncryptionScheme(
    AdditiveHomomorphicEncryptionScheme[KM, PT, RP, FullyHomomorphicCT, RR],
    MultiplicativeHomomorphicEncryptionScheme[KM, PT, RP, FullyHomomorphicCT, RR],
):
    """
    Abstract base class for Fully Homomorphic Encryption Schemes.
    """
