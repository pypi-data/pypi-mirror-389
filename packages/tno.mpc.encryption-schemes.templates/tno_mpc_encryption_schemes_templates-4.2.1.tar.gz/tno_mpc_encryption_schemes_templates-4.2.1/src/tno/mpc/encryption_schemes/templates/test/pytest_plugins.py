"""
Pytest plugins that facilitate testing the contents of our package.
"""

from collections.abc import Iterator

import pytest

from tno.mpc.encryption_schemes.templates.encryption_scheme import EncryptionScheme


@pytest.fixture(autouse=True)
def reset_encryption_scheme_instances() -> Iterator[None]:
    """
    Reset EncryptionScheme instances before and after test invocation.

    :return: Environment with no registered EncryptionSchemes.
    """
    EncryptionScheme.clear_instances(all_types=True)
    yield
    EncryptionScheme.clear_instances(all_types=True)
