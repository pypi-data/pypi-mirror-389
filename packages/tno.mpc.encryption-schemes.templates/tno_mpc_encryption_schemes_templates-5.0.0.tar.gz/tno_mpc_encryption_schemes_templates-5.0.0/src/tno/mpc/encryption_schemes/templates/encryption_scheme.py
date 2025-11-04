"""
Generic classes used for creating an encryption scheme.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from tno.mpc.encryption_schemes.templates.util.instance_manager import (
    InstanceManagerMixin,
)

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


PT = TypeVar("PT")  # plaintext        - type of non-encoded plaintext
RP = TypeVar("RP")  # raw plaintext    - type of EncodedPlaintext.value
KM = TypeVar("KM")  # key material
CV = TypeVar("CV")  # ciphertext value - type of Ciphertext.value


@dataclass
class EncodedPlaintext(Generic[RP]):  # pylint: disable=too-few-public-methods
    """
    Class that contains the encoding of a plaintext for a particular scheme.

    Constructs an EncodedPlaintext with the given value and encoding as specified in the scheme.

    :param value: value of the plaintext after encoding
    :param scheme: encryption scheme that specifies the used encoding
    :raise TypeError: provided scheme has the incorrect type.
    """

    value: RP
    scheme: EncryptionScheme[Any, Any, RP, Any]

    def __post_init__(self) -> None:
        """
        Validate encryption scheme.

        :raise TypeError: Scheme is of the wrong type.
        """
        if not isinstance(self.scheme, EncryptionScheme):
            raise TypeError(
                f"Expected scheme to be an EncryptionScheme, not {type(self.scheme)}"
            )


CT = TypeVar("CT", bound="Ciphertext[Any]")


class Ciphertext(Generic[CV]):  # pylint: disable=eq-without-hash
    """
    Ciphertext objects support addition and multiplication by plaintext scalars.
    """

    scheme: EncryptionScheme[Any, Any, Any, Self]

    def __init__(
        self,
        raw_value: CV,
        scheme: EncryptionScheme[Any, Any, Any, Self],
        **_kwargs: Any,
    ) -> None:
        r"""
        Constructs a Ciphertext with the given ciphertext value encrypted using the specified
        scheme.

        :param raw_value: value of the ciphertext
        :param scheme: encryption scheme used for creating this ciphertext
        :param \**_kwargs: Optional extra keyword arguments for the constructor.
        """
        self._raw_value = raw_value
        self.scheme = scheme

    @property
    def value(self) -> CV:
        """
        Raw value of the ciphertext.

        :return: Value of the ciphertext.
        """
        return self._raw_value

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """
        Method that determines whether two Ciphertexts are the same.

        :param other: Ciphertext to be compared to Self.
        :return: Boolean indicating whether they are the same.
        """

    def __str__(self) -> str:
        """
        :return: String representation of Ciphertext.
        """
        return f"{self.__class__.__name__}<value={str(self.value)}>"


EncryptionSchemeT = TypeVar(
    "EncryptionSchemeT", bound="EncryptionScheme[Any, Any, Any, Any]"
)


class EncryptionScheme(
    InstanceManagerMixin, ABC, Generic[KM, PT, RP, CT]
):  # pylint: disable=eq-without-hash
    """
    Abstract base class to define generic Homomorphic Encryption Scheme functionality. Can
    be used for all kinds of encryption schemes.

    Most easily constructed using the `from_security_parameter` method.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        r"""
        Construct a new EncryptionScheme.

        :param \*_args: Optional extra arguments for the constructor of a concrete implementation.
        :param \**_kwargs: Optional extra keyword arguments for the constructor of a concrete
            implementation.
        """
        super().__init__()

    @classmethod
    @abstractmethod
    def from_security_parameter(cls, *args: Any, **kwargs: Any) -> Self:
        r"""
        Generate a new EncryptionScheme from a security parameter.

        :param \*args: Security parameter(s) and optional extra arguments for the EncryptionScheme
            constructor.
        :param \**kwargs: Security parameter(s) and optional extra arguments for the
            EncryptionScheme constructor.
        :return: A new EncryptionScheme.
        """

    @staticmethod
    @abstractmethod
    def generate_key_material(*args: Any, **kwargs: Any) -> KM:
        r"""
        Method to generate key material (format depending on the type of scheme) for this scheme.

        :param \*args: Required arguments to generate said key material.
        :param \**kwargs: Required keyword arguments to generate said key material.
        """

    @abstractmethod
    def encode(self, plaintext: PT) -> EncodedPlaintext[RP]:
        """
        Encode a supported Plaintext using the specified encoding scheme.

        :param plaintext: Plaintext to be encoded.
        :return: EncodedPlaintext object containing the encoded value.
        """

    @abstractmethod
    def decode(self, encoded_plaintext: EncodedPlaintext[RP]) -> PT:
        """
        Decode an EncodedPlaintext using the specified encoding scheme.

        :param encoded_plaintext: Plaintext to be decoded.
        :return: Decoded Plaintext value
        """

    def encrypt(
        self, plaintext: PT | EncodedPlaintext[RP], apply_encoding: bool = True
    ) -> CT:
        """
        Encrypts the entered (encoded) Plaintext. Also encodes the Plaintext when this is required.

        :param plaintext: Plaintext or EncodedPlaintext to be encrypted.
        :param apply_encoding: Boolean indicating whether a non-encoded plaintext should be encoded.
            If False, the plaintext is encrypted in raw form.
        :return: Ciphertext object containing the encrypted value of the plaintext.
        """
        if isinstance(plaintext, EncodedPlaintext):
            return self._encrypt_raw(plaintext)
        if apply_encoding:
            return self._encrypt_raw(self.encode(plaintext))
        return self._encrypt_raw(EncodedPlaintext(cast(RP, plaintext), self))

    def encrypt_sequence(
        self,
        plaintext_sequence: Iterable[PT] | Iterable[EncodedPlaintext[RP]],
        apply_encoding: bool = True,
    ) -> Iterator[CT]:
        """
        Encrypts the entered sequence of (encoded) Plaintext. Also encodes a Plaintext when this
        is required.

        :param plaintext_sequence: Sequence of Plaintext or EncodedPlaintext to be encrypted.
        :param apply_encoding: Boolean indicating whether a non-encoded plaintext should be encoded.
            If False, the plaintext is encrypted in raw form.
        :return: Ciphertext object containing the encrypted value of the plaintext.
        """
        for plaintext in plaintext_sequence:
            yield self.encrypt(plaintext, apply_encoding)

    def decrypt(self, ciphertext: CT, apply_encoding: bool = True) -> PT:
        """
        Decrypts the input ciphertext.

        :param ciphertext: Ciphertext to be decrypted.
        :param apply_encoding: Boolean indicating whether the decrypted ciphertext is decoded
            before it is returned.
        :return: Plaintext decrypted value.
        """
        decrypted_ciphertext = self._decrypt_raw(ciphertext)
        return (
            self.decode(decrypted_ciphertext)
            if apply_encoding
            else cast(PT, decrypted_ciphertext.value)
        )

    def decrypt_sequence(
        self, ciphertext_sequence: Iterable[CT], apply_encoding: bool = True
    ) -> Iterator[PT]:
        """
        Decrypts the list of input ciphertext.

        :param ciphertext_sequence: Sequence of Ciphertext to be decrypted.
        :param apply_encoding: Boolean indicating whether the decrypted ciphertext is decoded
            before it is returned.
        :return: A list of Plaintext decrypted values.
        """
        for ciphertext in ciphertext_sequence:
            yield self.decrypt(ciphertext, apply_encoding)

    @abstractmethod
    def _encrypt_raw(self, plaintext: EncodedPlaintext[RP]) -> CT:
        """
        Encrypts an encoded (raw) plaintext value.

        :param plaintext: EncodedPlaintext object containing the raw value to be encrypted.
        :return: Ciphertext object containing the encrypted plaintext.
        """

    @abstractmethod
    def _decrypt_raw(self, ciphertext: CT) -> EncodedPlaintext[RP]:
        """
        Decrypts a ciphertext to its encoded plaintext value.

        :param ciphertext: Ciphertext object containing the ciphertext to be decrypted.
        :return: EncodedPlaintext object containing the encoded decryption of the ciphertext.
        """

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """
        Method that determines whether two EncryptionSchemes are the same.

        :param other: EncryptionScheme to be compared to Self.
        :return: Boolean indicating whether they are the same.
        """
