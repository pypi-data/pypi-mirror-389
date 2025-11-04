# pylint: disable=protected-access,too-many-ancestors,unsubscriptable-object
# mypy: disable-error-code="misc"
"""
File containing all tests regarding the storing of encryption schemes and the generation of the
id that is used for that purpose.
"""

from __future__ import annotations

import pytest

from tno.mpc.encryption_schemes.templates.test.conftest import (
    DummyRandomizedScheme as DummyScheme,
)


class SubclassA(DummyScheme):
    """Dummy subclass of DummyScheme."""


class SubclassB(DummyScheme):
    """A different dummy subclass of DummyScheme."""


class DummySchemeWithFuncWrongVarName(DummyScheme):
    """
    Dummy encryption scheme with id_from_arguments method that has an argument name different
    from the attribute.
    """

    @classmethod
    def id_from_arguments(cls, unknown_attribute_name: int) -> int:
        """
        Generate a unique id from the dummy_value attribute of this scheme.
        Note: dummy_value is not the attribute of this scheme (that is dummy), this should thus
        fail.

        :param unknown_attribute_name: Dummy value.
        :return: Numeric id
        """
        return unknown_attribute_name


class TestPytestPluginDoesNotRestoreFunctionInstances:
    def test_function_instance_stored(self) -> None:
        """
        Validate pytest plugin restores all instances between invocations.

        Part 1: populate instances.
        """
        scheme = DummyScheme(dummy_value=1)
        scheme.save_globally()
        assert scheme.identifier in scheme._instances

    def test_function_instance_is_not_recoverable(self) -> None:
        """
        Validate pytest plugin restores all instances between invocations.

        Part 2: validate that there are no instances.
        """
        scheme = DummyScheme(dummy_value=1)
        assert scheme.identifier not in scheme._instances


class TestPytestPluginRestoresNonFunctionInstances:
    @pytest.fixture(name="scheme", scope="class")
    def fixture_scheme(self) -> DummyScheme:
        """
        Fixture that creates DummyScheme for multiple tests.
        """
        scheme = DummyScheme(dummy_value=1)
        scheme.save_globally()
        return scheme

    def test_class_instance_can_be_deleted_here(self, scheme: DummyScheme) -> None:
        """
        Validate pytest plugin is able to restore all instances before invocations.
        """
        scheme = DummyScheme(dummy_value=1)
        assert scheme.identifier in scheme._instances
        DummyScheme.clear_instances()
        assert scheme.identifier not in scheme._instances

    def test_class_instance_is_still_alive_here(self, scheme: DummyScheme) -> None:
        """
        Validate pytest plugin is able to restore all instances before invocations.
        """
        scheme = DummyScheme(dummy_value=1)
        assert scheme.identifier in scheme._instances


@pytest.mark.parametrize("identifier", list(range(10)))
def test_id_generation_with_id_from_arguments_wrong_var_name(
    identifier: int,
) -> None:
    """
    Test to check if the right error is thrown when the id_from_arguments method uses wrong
    argument names.

    :param identifier: Identifier to be used for this scheme.
    """
    test_scheme = DummySchemeWithFuncWrongVarName(dummy_value=identifier)
    with pytest.raises(KeyError):
        _ = test_scheme.identifier


@pytest.mark.parametrize("identifier", list(range(10)))
def test_id_generation_with_id_from_arguments_right_var_name(
    identifier: int,
) -> None:
    """
    Test to check if the right id is given to the EncryptionScheme when id_from_arguments is
    implemented correctly.

    :param identifier: Identifier to be used for this scheme.
    """
    test_scheme = DummyScheme(dummy_value=identifier)
    assert test_scheme.identifier == identifier


@pytest.mark.parametrize("identifier", list(range(10)))
def test_saving_globally(
    identifier: int,
) -> None:
    """
    Test to check if the EncryptionScheme is saved correctly globally when id_from_arguments is
    implemented correctly. Also check overwrite warnings in case that the should or should not be
    given. Next to this, removal of the global list is checked.

    :param identifier: Identifier to be used for this scheme.
    """
    # Ensure we start with a clean slate
    DummyScheme.clear_instances()

    test_scheme_1 = DummyScheme(dummy_value=identifier)
    test_scheme_2 = DummyScheme(dummy_value=identifier)
    with pytest.raises(KeyError):
        _ = DummyScheme.from_id(identifier)

    assert len(DummyScheme._instances) == 0

    test_scheme_1.save_globally(overwrite=False)
    assert len(DummyScheme._instances) == 1
    assert DummyScheme._instances[identifier] is test_scheme_1
    assert DummyScheme.from_id(identifier) is test_scheme_1
    assert DummyScheme.from_id_arguments(dummy_value=identifier) is test_scheme_1

    # This should do nothing
    test_scheme_1.save_globally(overwrite=False)
    assert len(DummyScheme._instances) == 1
    assert DummyScheme._instances[identifier] is test_scheme_1
    assert DummyScheme.from_id(identifier) is test_scheme_1
    assert DummyScheme.from_id_arguments(dummy_value=identifier) is test_scheme_1

    # ensure that test_scheme_1 does not get overwritten and a proper exception is thrown
    with pytest.raises(KeyError):
        test_scheme_2.save_globally(overwrite=False)

    test_scheme_2.save_globally(overwrite=True)
    # The entry of identifier in the global list should be overwritten now
    assert len(DummyScheme._instances) == 1
    assert DummyScheme._instances[identifier] is test_scheme_2
    assert DummyScheme.from_id(identifier) is test_scheme_2
    assert DummyScheme.from_id_arguments(dummy_value=identifier) is test_scheme_2

    test_scheme_3 = DummyScheme(dummy_value=identifier + 1)
    # the global list should be the same
    assert len(DummyScheme._instances) == 1
    assert DummyScheme._instances[identifier] is test_scheme_2
    assert DummyScheme.from_id(identifier) is test_scheme_2
    assert DummyScheme.from_id_arguments(dummy_value=identifier) is test_scheme_2

    test_scheme_3.save_globally()
    # check if the scheme is saved properly when another scheme is stored
    assert len(DummyScheme._instances) == 2
    assert DummyScheme._instances[identifier] is test_scheme_2
    assert DummyScheme.from_id(identifier) is test_scheme_2
    assert DummyScheme.from_id_arguments(dummy_value=identifier) is test_scheme_2
    assert DummyScheme._instances[identifier + 1] is test_scheme_3
    assert DummyScheme.from_id(identifier + 1) is test_scheme_3
    assert DummyScheme.from_id_arguments(dummy_value=identifier + 1) is test_scheme_3

    test_scheme_3.remove_from_global_list()
    # check if removal works properly
    assert len(DummyScheme._instances) == 1
    assert DummyScheme._instances[identifier] is test_scheme_2
    assert DummyScheme.from_id(identifier) is test_scheme_2
    assert DummyScheme.from_id_arguments(dummy_value=identifier) is test_scheme_2


def test_init_subclass() -> None:
    """
    Test that the class properties InstanceManagerMixin._instances and
    InstanceManagerMixin._derived_classes work as expect.

    When instantiating a new subclass of InstanceManagerMixin, its _instances
    and _derived_classes should be empty and independent of the other
    subclasses of InstanceManagerMixin.
    """
    # Ensure we start with a clean slate
    DummyScheme.clear_instances(all_types=True)

    # Check that the global _instances list are independent for each subclass
    base_scheme_instance = DummyScheme(dummy_value=1)
    base_scheme_instance.save_globally()
    subclass_a_instance = SubclassA(dummy_value=2)
    subclass_a_instance.save_globally()
    subclass_b_instance = SubclassB(dummy_value=3)
    subclass_b_instance.save_globally()
    assert len(DummyScheme._instances) == 1
    assert len(base_scheme_instance._instances) == 1
    assert len(subclass_a_instance._instances) == 1
    assert len(SubclassA._instances) == 1
    assert len(subclass_b_instance._instances) == 1
    assert len(SubclassB._instances) == 1

    # Check that the derived classes are saved
    assert SubclassA in base_scheme_instance._derived_classes
    assert SubclassB in base_scheme_instance._derived_classes

    # Check that the derived classes themselves have no derived classes
    assert len(subclass_a_instance._derived_classes) == 0
    assert len(SubclassA._derived_classes) == 0
    assert len(subclass_b_instance._derived_classes) == 0
    assert len(SubclassB._derived_classes) == 0
