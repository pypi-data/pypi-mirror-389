"""
Custom exceptions for the tno.mpc.encryption_scheme modules.
"""

from __future__ import annotations

WARN_INEFFICIENT_RANDOMIZATION = (
    "Randomizing a fresh ciphertext. This indicates a potential inefficiency as the ciphertext is "
    "randomized while the current randomness in the ciphertext is still fresh. It is more "
    "efficient to skip this randomization."
)

WARN_INEFFICIENT_HOM_OPERATION = (
    "Identified a fresh ciphertext as input to a homomorphic operation, which is no longer fresh "
    "after the operation. This indicates a potential inefficiency if the non-fresh input may also "
    "be used in other operations (unused randomness). Solution: randomize ciphertexts as late as "
    "possible, e.g. by encrypting them with scheme.unsafe_encrypt and randomizing them just "
    "before sending. Note that the serializer randomizes non-fresh ciphertexts by default."
)


class EncryptionSchemeWarning(UserWarning):
    """
    Issued to suggest cryptographic best practises.
    """


class RandomizedEncryptionSchemeWarning(EncryptionSchemeWarning):
    """
    Issued for warnings related to the randomness generation.
    """


class TooMuchRandomnessWarning(RandomizedEncryptionSchemeWarning):
    """
    Issued when more randomness has been generated than used by the protocol.
    """


class TooLittleRandomnessWarning(RandomizedEncryptionSchemeWarning):
    """
    Issued when less randomness has been generated than required by the
    protocol, resulting in randomness needing to be generated on the fly.
    """


class EncryptionSchemeError(Exception):
    """
    Generic error type for encryption schemes.
    """


class SerializationError(EncryptionSchemeError):
    """
    Serialization error for encryption schemes.
    """

    def __init__(self, m: str | None = None) -> None:
        super().__init__(
            m
            if m is not None
            else "The tno.mpc.communication package has not been installed. Please install this package before you call the serialization code."
        )
