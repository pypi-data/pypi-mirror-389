"""
Pytest plugins that facilitate testing the contents of our package.
"""

from collections.abc import Iterator
from typing import Any

import pytest

from tno.mpc.encryption_schemes.templates.encryption_scheme import EncryptionScheme


@pytest.fixture(autouse=True)
def restore_encryption_scheme_instances() -> Iterator[None]:
    """
    Restore EncryptionScheme instances after test invocation.

    :return: Environment with no registered EncryptionSchemes.
    """
    instance_dict = _get_all_instances(EncryptionScheme)  # type: ignore[type-abstract]
    yield
    _restore_all_instances(EncryptionScheme, instance_dict)  # type: ignore[type-abstract]


def _get_all_instances(
    scheme: type[EncryptionScheme[Any, Any, Any, Any]],
) -> dict[str, Any]:
    """
    Recursively store the instances and derived classes of the provided class, and then for every
    derived class do the same.

    :param scheme: Scheme of which the instances need to be stored.
    :return: Ugly recursive dictionary.
    """
    result: dict[str, Any] = {
        "type": scheme.__name__,
        "instances": scheme._instances.copy(),
    }
    derived_subclasses = scheme._derived_classes.copy()
    derived_subclass_instances = [_get_all_instances(d) for d in derived_subclasses]
    result["derived_classes"] = derived_subclasses
    result["derived_classes_dict"] = derived_subclass_instances
    return result


def _restore_all_instances(
    scheme: type[EncryptionScheme[Any, Any, Any, Any]], instance_dict: dict[str, Any]
) -> None:
    """
    Recursively restore instances of the provided class and those of its derived classes.

    :param scheme: Scheme of which the instances need to be restored.
    :param instance_dict: Ugly recursive dictionary.
    """
    scheme.clear_instances(all_types=True)
    scheme._instances.update(instance_dict["instances"])
    for d, i in zip(
        instance_dict["derived_classes"],
        instance_dict["derived_classes_dict"],
    ):
        _restore_all_instances(d, i)
