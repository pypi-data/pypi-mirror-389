#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Unit tests for the db_model module.
"""

from unittest.mock import Mock, patch

import pytest
from peewee import AutoField, DatabaseProxy, ModelInsert, TextField

from mafw.db.db_model import MAFwBaseModel, MAFwBaseModelDoesNotExist, database_proxy
from mafw.db.trigger import Trigger
from mafw.mafw_errors import UnsupportedDatabaseError


class TestMAFwBaseModelDoesNotExist:
    """Test cases for MAFwBaseModelDoesNotExist exception."""

    def test_exception_inheritance(self):
        """Test that the exception inherits from MAFwException."""
        from mafw.mafw_errors import MAFwException

        assert issubclass(MAFwBaseModelDoesNotExist, MAFwException)

    def test_exception_can_be_raised(self):
        """Test that the exception can be raised and caught."""
        with pytest.raises(MAFwBaseModelDoesNotExist):
            raise MAFwBaseModelDoesNotExist('Test message')


class TestDatabaseProxy:
    """Test cases for database_proxy."""

    def test_database_proxy_is_instance(self):
        """Test that database_proxy is an instance of DatabaseProxy."""
        assert isinstance(database_proxy, DatabaseProxy)


class TestMAFwBaseModel:
    """Test cases for MAFwBaseModel class."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database for testing."""
        db = Mock()
        db.execute_sql = Mock()
        db.drop_tables = Mock()
        return db

    @pytest.fixture
    def mock_trigger(self):
        """Create a mock trigger for testing."""
        trigger = Mock(spec=Trigger)
        trigger.trigger_name = 'test_trigger'
        trigger.set_database = Mock()
        trigger.create = Mock(return_value='CREATE TRIGGER test_trigger...')
        trigger.drop = Mock(return_value='DROP TRIGGER test_trigger')
        return trigger

    @pytest.fixture
    def sample_model_class(self, mock_database):
        """Create a sample model class for testing."""

        class SampleModel(MAFwBaseModel):
            id = AutoField(primary_key=True)
            name = TextField()

            class Meta:
                database = mock_database
                legacy_table_names = False

        # Mock the _meta attribute
        SampleModel._meta = Mock()
        SampleModel._meta.database = mock_database
        SampleModel._meta.composite_key = False
        SampleModel._meta.primary_key = Mock()
        SampleModel._meta.primary_key.name = 'id'
        SampleModel._meta.fields = {'id': Mock(name='id'), 'name': Mock(name='name')}

        return SampleModel

    def test_triggers_default_implementation(self):
        """Test that the default triggers method returns an empty list."""
        triggers = MAFwBaseModel.triggers()
        assert triggers == []
        assert isinstance(triggers, list)

    def test_triggers_can_be_overridden(self, mock_trigger):
        """Test that triggers method can be overridden in subclasses."""

        class CustomModel(MAFwBaseModel):
            @classmethod
            def triggers(cls):
                return [mock_trigger]

        triggers = CustomModel.triggers()
        assert len(triggers) == 1
        assert triggers[0] == mock_trigger

    @patch('mafw.db.db_model.Model.create_table')
    def test_create_table_without_triggers(self, mock_super_create, sample_model_class):
        """Test create_table when no triggers are defined."""
        sample_model_class.triggers = Mock(return_value=[])

        sample_model_class.create_table(safe=True, test_option='value')

        mock_super_create.assert_called_once_with(True, test_option='value')
        sample_model_class._meta.database.execute_sql.assert_not_called()

    @patch('mafw.db.db_model.Model.create_table')
    def test_create_table_with_triggers_success(self, mock_super_create, sample_model_class, mock_trigger):
        """Test successful create_table with triggers."""
        sample_model_class.triggers = Mock(return_value=[mock_trigger])

        sample_model_class.create_table()

        mock_super_create.assert_called_once_with(True)
        mock_trigger.set_database.assert_called_once_with(sample_model_class._meta.database)
        mock_trigger.create.assert_called_once()
        sample_model_class._meta.database.execute_sql.assert_called_once_with(mock_trigger.create.return_value)

    @patch('mafw.db.db_model.Model.create_table')
    def test_create_table_with_unsupported_trigger(self, mock_super_create, sample_model_class, mock_trigger):
        """Test create_table with unsupported trigger (should warn and continue)."""
        sample_model_class.triggers = Mock(return_value=[mock_trigger])
        sample_model_class._meta.database.execute_sql.side_effect = UnsupportedDatabaseError('Unsupported trigger')

        with pytest.warns(UserWarning, match='Skipping unsupported trigger'):
            sample_model_class.create_table()

        mock_super_create.assert_called_once()
        sample_model_class._meta.database.drop_tables.assert_not_called()

    @patch('mafw.db.db_model.Model.create_table')
    def test_create_table_with_trigger_failure_cleanup(self, mock_super_create, sample_model_class, mock_trigger):
        """Test create_table cleanup when trigger creation fails."""
        sample_model_class.triggers = Mock(return_value=[mock_trigger])
        sample_model_class._meta.database.execute_sql.side_effect = Exception('Trigger creation failed')

        with pytest.raises(Exception, match='Trigger creation failed'):
            sample_model_class.create_table()

        # Verify cleanup was attempted
        sample_model_class._meta.database.drop_tables.assert_called_once_with([sample_model_class], safe=True)
        mock_trigger.drop.assert_called_once_with(True)
        sample_model_class._meta.database.execute_sql.assert_called()

    @patch('mafw.db.db_model.Model.create_table')
    def test_create_table_cleanup_ignores_drop_errors(self, mock_super_create, sample_model_class, mock_trigger):
        """Test that cleanup ignores errors when dropping triggers."""
        sample_model_class.triggers = Mock(return_value=[mock_trigger])
        sample_model_class._meta.database.execute_sql.side_effect = Exception('Trigger creation failed')

        # Make trigger.drop raise an exception - should be ignored
        mock_trigger.drop.side_effect = Exception('Drop failed')

        with pytest.raises(Exception, match='Trigger creation failed'):
            sample_model_class.create_table()

        # Should still attempt cleanup despite drop failure
        sample_model_class._meta.database.drop_tables.assert_called_once()
        mock_trigger.drop.assert_called_once()

    @patch('mafw.db.db_model.Model.create_table')
    def test_create_table_multiple_triggers(self, mock_super_create, sample_model_class):
        """Test create_table with multiple triggers."""
        trigger1 = Mock(spec=Trigger)
        trigger1.trigger_name = 'trigger1'
        trigger1.set_database = Mock()
        trigger1.create = Mock(return_value='CREATE TRIGGER trigger1...')
        trigger1.drop = Mock(return_value='DROP TRIGGER trigger1')

        trigger2 = Mock(spec=Trigger)
        trigger2.trigger_name = 'trigger2'
        trigger2.set_database = Mock()
        trigger2.create = Mock(return_value='CREATE TRIGGER trigger2...')
        trigger2.drop = Mock(return_value='DROP TRIGGER trigger2')

        sample_model_class.triggers = Mock(return_value=[trigger1, trigger2])

        sample_model_class.create_table()

        # Verify both triggers were processed
        trigger1.set_database.assert_called_once_with(sample_model_class._meta.database)
        trigger2.set_database.assert_called_once_with(sample_model_class._meta.database)
        assert sample_model_class._meta.database.execute_sql.call_count == 2

    @pytest.fixture
    def mock_model_insert(self):
        """Create a mock ModelInsert for testing."""
        mock_insert = Mock(spec=ModelInsert)
        mock_on_conflict = Mock(spec=ModelInsert)
        mock_insert.on_conflict = Mock(return_value=mock_on_conflict)
        return mock_insert, mock_on_conflict

    @patch('mafw.db.db_model.cast')
    def test_std_upsert_simple_primary_key(self, mock_cast, sample_model_class, mock_model_insert):
        """Test std_upsert with simple primary key."""
        mock_insert, mock_on_conflict = mock_model_insert
        mock_cast.side_effect = [sample_model_class, mock_on_conflict]

        with patch.object(sample_model_class, 'insert', return_value=mock_insert):
            result = sample_model_class.std_upsert({'name': 'test'}, id=1)

            sample_model_class.insert.assert_called_once_with({'name': 'test'}, id=1)
            mock_insert.on_conflict.assert_called_once()

            # Verify the on_conflict call arguments
            call_args = mock_insert.on_conflict.call_args
            assert 'conflict_target' in call_args.kwargs
            assert 'preserve' in call_args.kwargs

            assert result == mock_on_conflict

    @patch('mafw.db.db_model.cast')
    def test_std_upsert_composite_key(self, mock_cast, sample_model_class, mock_model_insert):
        """Test std_upsert with composite primary key."""
        mock_insert, mock_on_conflict = mock_model_insert
        mock_cast.side_effect = [sample_model_class, mock_on_conflict]

        # Setup composite key scenario
        sample_model_class._meta.composite_key = True
        sample_model_class._meta.primary_key = Mock()
        sample_model_class._meta.primary_key.field_names = ['id', 'type']
        sample_model_class._meta.fields = {'id': Mock(name='id'), 'type': Mock(name='type'), 'name': Mock(name='name')}

        with patch.object(sample_model_class, 'insert', return_value=mock_insert):
            result = sample_model_class.std_upsert(name='test')

            sample_model_class.insert.assert_called_once_with(None, name='test')
            mock_insert.on_conflict.assert_called_once()
            assert result == mock_on_conflict

    @patch('mafw.db.db_model.cast')
    def test_std_upsert_many_simple_key(self, mock_cast, sample_model_class, mock_model_insert):
        """Test std_upsert_many with simple primary key."""
        mock_insert, mock_on_conflict = mock_model_insert
        mock_cast.side_effect = [sample_model_class, mock_on_conflict]

        rows = [{'id': 1, 'name': 'test1'}, {'id': 2, 'name': 'test2'}]

        with patch.object(sample_model_class, 'insert_many', return_value=mock_insert):
            result = sample_model_class.std_upsert_many(rows, ['id', 'name'])

            sample_model_class.insert_many.assert_called_once_with(rows, ['id', 'name'])
            mock_insert.on_conflict.assert_called_once()
            assert result == mock_on_conflict

    @patch('mafw.db.db_model.cast')
    def test_std_upsert_many_composite_key(self, mock_cast, sample_model_class, mock_model_insert):
        """Test std_upsert_many with composite primary key."""
        mock_insert, mock_on_conflict = mock_model_insert
        mock_cast.side_effect = [sample_model_class, mock_on_conflict]

        # Setup composite key scenario
        sample_model_class._meta.composite_key = True
        sample_model_class._meta.primary_key = Mock()
        sample_model_class._meta.primary_key.field_names = ['id', 'type']
        sample_model_class._meta.fields = {'id': Mock(name='id'), 'type': Mock(name='type'), 'name': Mock(name='name')}

        rows = [(1, 'A', 'test1'), (2, 'B', 'test2')]

        with patch.object(sample_model_class, 'insert_many', return_value=mock_insert):
            result = sample_model_class.std_upsert_many(rows, ['id', 'type', 'name'])

            sample_model_class.insert_many.assert_called_once_with(rows, ['id', 'type', 'name'])
            mock_insert.on_conflict.assert_called_once()
            assert result == mock_on_conflict

    @pytest.mark.parametrize(
        'safe_param,expected_safe',
        [
            (True, True),
            (False, False),
            (None, True),  # Default value
        ],
    )
    @patch('mafw.db.db_model.Model.create_table')
    def test_create_table_safe_parameter(self, mock_super_create, sample_model_class, safe_param, expected_safe):
        """Test create_table with different safe parameter values."""
        sample_model_class.triggers = Mock(return_value=[])

        if safe_param is None:
            sample_model_class.create_table()
        else:
            sample_model_class.create_table(safe=safe_param)

        mock_super_create.assert_called_once_with(expected_safe)

    def test_meta_class_attributes(self):
        """Test that Meta class has correct default attributes."""
        assert MAFwBaseModel._meta.database == database_proxy
        assert MAFwBaseModel._meta.legacy_table_names is False

    def test_model_inheritance(self):
        """Test that MAFwBaseModel properly inherits from peewee Model."""
        # Import here to avoid circular imports in the actual test
        from playhouse.signals import Model

        assert issubclass(MAFwBaseModel, Model)

    @patch('mafw.db.db_model.warnings.warn')
    @patch('mafw.db.db_model.Model.create_table')
    def test_unsupported_database_warning_message(self, mock_super_create, mock_warn, sample_model_class, mock_trigger):
        """Test that the correct warning message is generated for unsupported database errors."""
        sample_model_class.triggers = Mock(return_value=[mock_trigger])
        error_msg = "This database doesn't support triggers"
        sample_model_class._meta.database.execute_sql.side_effect = UnsupportedDatabaseError(error_msg)

        sample_model_class.create_table()

        mock_warn.assert_called_once_with(f'Skipping unsupported trigger {mock_trigger.trigger_name}: {error_msg}')

    @patch('mafw.db.db_model.cast')
    def test_std_upsert_without_data_parameter(self, mock_cast, sample_model_class, mock_model_insert):
        """Test std_upsert when __data parameter is None."""
        mock_insert, mock_on_conflict = mock_model_insert
        mock_cast.side_effect = [sample_model_class, mock_on_conflict]

        with patch.object(sample_model_class, 'insert', return_value=mock_insert):
            result = sample_model_class.std_upsert(None, name='test')

            sample_model_class.insert.assert_called_once_with(None, name='test')
            assert result == mock_on_conflict

    @patch('mafw.db.db_model.cast')
    def test_std_upsert_many_without_fields_parameter(self, mock_cast, sample_model_class, mock_model_insert):
        """Test std_upsert_many when fields parameter is None."""
        mock_insert, mock_on_conflict = mock_model_insert
        mock_cast.side_effect = [sample_model_class, mock_on_conflict]
        rows = [{'id': 1, 'name': 'test'}]

        with patch.object(sample_model_class, 'insert_many', return_value=mock_insert):
            result = sample_model_class.std_upsert_many(rows, None)

            sample_model_class.insert_many.assert_called_once_with(rows, None)
            assert result == mock_on_conflict

    @pytest.fixture
    def sample_model_instance(self, mock_database):
        """Create a sample model instance for testing."""

        # Create the actual model class first
        class TestModel(MAFwBaseModel):
            id = AutoField(primary_key=True)
            name = TextField()

            class Meta:
                database = mock_database
                legacy_table_names = False

        # Create a mock instance but with the actual methods from MAFwBaseModel
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.name = 'test_name'
        mock_instance._meta = Mock()
        mock_instance._meta.database = mock_database

        # Bind the actual methods to the mock instance
        mock_instance.to_dict = TestModel.to_dict.__get__(mock_instance, TestModel)
        mock_instance.update_from_dict = TestModel.update_from_dict.__get__(mock_instance, TestModel)

        return mock_instance, TestModel

    @patch('mafw.db.db_model.model_to_dict')
    def test_to_dict_default_parameters(self, mock_model_to_dict, sample_model_instance):
        """Test to_dict with default parameters."""
        instance, model_class = sample_model_instance
        expected_result = {'id': 1, 'name': 'test_name'}
        mock_model_to_dict.return_value = expected_result

        result = instance.to_dict()

        mock_model_to_dict.assert_called_once_with(instance, recurse=True, backrefs=False, only=None, exclude=None)
        assert result == expected_result

    @patch('mafw.db.db_model.model_to_dict')
    def test_to_dict_custom_parameters(self, mock_model_to_dict, sample_model_instance):
        """Test to_dict with custom parameters."""
        instance, model_class = sample_model_instance
        expected_result = {'name': 'test_name'}
        mock_model_to_dict.return_value = expected_result

        result = instance.to_dict(recurse=False, backrefs=True, only=['name'], exclude=['id'])

        mock_model_to_dict.assert_called_once_with(
            instance, recurse=False, backrefs=True, only=['name'], exclude=['id']
        )
        assert result == expected_result

    @patch('mafw.db.db_model.model_to_dict')
    def test_to_dict_with_kwargs(self, mock_model_to_dict, sample_model_instance):
        """Test to_dict with additional kwargs."""
        instance, model_class = sample_model_instance
        expected_result = {'id': 1}
        mock_model_to_dict.return_value = expected_result

        result = instance.to_dict(recurse=False, max_depth=2, extra_attr='value')

        mock_model_to_dict.assert_called_once_with(
            instance, recurse=False, backrefs=False, only=None, exclude=None, max_depth=2, extra_attr='value'
        )
        assert result == expected_result

    @patch('mafw.db.db_model.dict_to_model')
    def test_from_dict_default_parameters(self, mock_dict_to_model, sample_model_instance):
        """Test from_dict with default parameters."""
        instance, model_class = sample_model_instance
        data = {'id': 1, 'name': 'test_name'}
        mock_instance = Mock()
        mock_dict_to_model.return_value = mock_instance

        result = model_class.from_dict(data)

        mock_dict_to_model.assert_called_once_with(model_class, data, ignore_unknown=False)
        assert result == mock_instance

    @patch('mafw.db.db_model.dict_to_model')
    def test_from_dict_ignore_unknown_true(self, mock_dict_to_model, sample_model_instance):
        """Test from_dict with ignore_unknown=True."""
        instance, model_class = sample_model_instance
        data = {'id': 1, 'name': 'test_name', 'unknown_field': 'value'}
        mock_instance = Mock()
        mock_dict_to_model.return_value = mock_instance

        result = model_class.from_dict(data, ignore_unknown=True)

        mock_dict_to_model.assert_called_once_with(model_class, data, ignore_unknown=True)
        assert result == mock_instance

    @patch('mafw.db.db_model.dict_to_model')
    def test_from_dict_ignore_unknown_false(self, mock_dict_to_model, sample_model_instance):
        """Test from_dict with ignore_unknown=False explicitly."""
        instance, model_class = sample_model_instance
        data = {'id': 1, 'name': 'test_name'}
        mock_instance = Mock()
        mock_dict_to_model.return_value = mock_instance

        result = model_class.from_dict(data, ignore_unknown=False)

        mock_dict_to_model.assert_called_once_with(model_class, data, ignore_unknown=False)
        assert result == mock_instance

    @patch('mafw.db.db_model.update_model_from_dict')
    def test_update_from_dict_default_parameters(self, mock_update_model_from_dict, sample_model_instance):
        """Test update_from_dict with default parameters."""
        instance, model_class = sample_model_instance
        data = {'name': 'updated_name'}

        result = instance.update_from_dict(data)

        mock_update_model_from_dict.assert_called_once_with(instance, data, ignore_unknown=False)
        # Verify method chaining (returns self)
        assert result == instance

    @patch('mafw.db.db_model.update_model_from_dict')
    def test_update_from_dict_ignore_unknown_true(self, mock_update_model_from_dict, sample_model_instance):
        """Test update_from_dict with ignore_unknown=True."""
        instance, model_class = sample_model_instance
        data = {'name': 'updated_name', 'unknown_field': 'value'}

        result = instance.update_from_dict(data, ignore_unknown=True)

        mock_update_model_from_dict.assert_called_once_with(instance, data, ignore_unknown=True)
        assert result == instance

    @patch('mafw.db.db_model.update_model_from_dict')
    def test_update_from_dict_ignore_unknown_false(self, mock_update_model_from_dict, sample_model_instance):
        """Test update_from_dict with ignore_unknown=False explicitly."""
        instance, model_class = sample_model_instance
        data = {'name': 'updated_name'}

        result = instance.update_from_dict(data, ignore_unknown=False)

        mock_update_model_from_dict.assert_called_once_with(instance, data, ignore_unknown=False)
        assert result == instance

    @patch('mafw.db.db_model.update_model_from_dict')
    def test_update_from_dict_method_chaining(self, mock_update_model_from_dict, sample_model_instance):
        """Test that update_from_dict returns self for method chaining."""
        instance, model_class = sample_model_instance
        data1 = {'name': 'first_update'}
        data2 = {'name': 'second_update'}

        # Test chaining capability
        result = instance.update_from_dict(data1).update_from_dict(data2)

        assert mock_update_model_from_dict.call_count == 2
        mock_update_model_from_dict.assert_any_call(instance, data1, ignore_unknown=False)
        mock_update_model_from_dict.assert_any_call(instance, data2, ignore_unknown=False)
        assert result == instance

    @patch('mafw.db.db_model.model_to_dict')
    def test_to_dict_return_type(self, mock_model_to_dict, sample_model_instance):
        """Test that to_dict returns the correct type annotation."""
        instance, model_class = sample_model_instance
        expected_result = {'id': 1, 'name': 'test_name'}
        mock_model_to_dict.return_value = expected_result

        result = instance.to_dict()

        assert isinstance(result, dict)
        # Verify it's actually the mocked return value
        assert result == expected_result

    @patch('mafw.db.db_model.dict_to_model')
    def test_from_dict_return_type(self, mock_dict_to_model, sample_model_instance):
        """Test that from_dict returns the correct type (MAFwBaseModel)."""
        instance, model_class = sample_model_instance
        data = {'id': 1, 'name': 'test_name'}
        # Create a mock that looks like an instance of our model
        mock_instance = Mock(spec=model_class)
        mock_dict_to_model.return_value = mock_instance

        result = model_class.from_dict(data)

        assert result == mock_instance


class TestModuleConstants:
    """Test module-level constants and imports."""

    def test_database_proxy_exists(self):
        """Test that database_proxy is properly defined."""
        from mafw.db.db_model import database_proxy

        assert database_proxy is not None
        assert isinstance(database_proxy, DatabaseProxy)


@pytest.mark.integration_test
class TestIntegration:
    """Integration tests that test multiple components together."""

    @pytest.fixture
    def complete_model_setup(self):
        """Setup a complete model with all components for integration testing."""
        db = Mock()
        db.execute_sql = Mock()
        db.drop_tables = Mock()

        trigger = Mock(spec=Trigger)
        trigger.trigger_name = 'integration_trigger'
        trigger.set_database = Mock()
        trigger.create = Mock(return_value='CREATE TRIGGER integration_trigger...')
        trigger.drop = Mock(return_value='DROP TRIGGER integration_trigger')

        class IntegrationModel(MAFwBaseModel):
            id = AutoField(primary_key=True)
            name = TextField()

            @classmethod
            def triggers(cls):
                return [trigger]

            class Meta:
                database = db

        # Setup _meta properly
        IntegrationModel._meta = Mock()
        IntegrationModel._meta.database = db
        IntegrationModel._meta.composite_key = False
        IntegrationModel._meta.primary_key = Mock(name='id')
        IntegrationModel._meta.fields = {'id': Mock(name='id'), 'name': Mock(name='name')}

        return IntegrationModel, db, trigger

    @pytest.fixture
    def mock_model_insert(self):
        """Create a mock ModelInsert for testing."""
        mock_insert = Mock(spec=ModelInsert)
        mock_on_conflict = Mock(spec=ModelInsert)
        mock_insert.on_conflict = Mock(return_value=mock_on_conflict)
        return mock_insert, mock_on_conflict

    @patch('mafw.db.db_model.Model.create_table')
    @patch('mafw.db.db_model.cast')
    def test_complete_workflow_success(self, mock_cast, mock_super_create, complete_model_setup, mock_model_insert):
        """Test the complete workflow from table creation to upsert operations."""
        model_class, db, trigger = complete_model_setup
        mock_insert, mock_on_conflict = mock_model_insert
        mock_cast.side_effect = [model_class, model_class, mock_on_conflict]
        # Test table creation
        model_class.create_table()

        # Verify table and trigger creation
        mock_super_create.assert_called_once()
        trigger.set_database.assert_called_once_with(db)
        db.execute_sql.assert_called_once()

        with patch.object(model_class, 'insert', return_value=mock_insert):
            result = model_class.std_upsert(name='integration_test')

            assert result == mock_on_conflict
            model_class.insert.assert_called_once()
            mock_insert.on_conflict.assert_called_once()


class TestMAFwBaseModelDictionaryHandling:
    """Test cases for dictionary conversion methods in MAFwBaseModel."""

    @pytest.fixture
    def mock_database(self):
        """Create a mock database for testing."""
        db = Mock()
        db.execute_sql = Mock()
        db.drop_tables = Mock()
        return db

    @pytest.fixture
    def sample_model_class(self, mock_database):
        """Create a sample model class for testing."""

        class SampleModel(MAFwBaseModel):
            id = AutoField(primary_key=True)
            name = TextField()

            class Meta:
                database = mock_database
                legacy_table_names = False

        # Mock the _meta attribute
        SampleModel._meta = Mock()
        SampleModel._meta.database = mock_database
        SampleModel._meta.composite_key = False
        SampleModel._meta.primary_key = Mock()
        SampleModel._meta.primary_key.name = 'id'
        SampleModel._meta.fields = {'id': Mock(name='id'), 'name': Mock(name='name')}

        return SampleModel
