#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Unit tests for db_filter module.
"""

import operator
import warnings
from unittest.mock import Mock, patch

import pytest
from peewee import AutoField, BooleanField, IntegerField, Model, TextField

from mafw.db.db_filter import Filter, FilterCondition, FilterRegister
from mafw.enumerators import LogicalOp


# Mock Model classes for testing
class MockModel(Model):
    """Mock model for testing."""

    id = AutoField(primary_key=True)
    name = TextField()
    active = BooleanField()
    count = IntegerField()
    flags = IntegerField()

    class Meta:
        database = Mock()


class AnotherMockModel(Model):
    """Another mock model for testing."""

    id = AutoField(primary_key=True)
    description = TextField()

    class Meta:
        database = Mock()


class LastMockModel(Model):
    """Another mock model for testing."""

    id = AutoField(primary_key=True)
    description = TextField()

    class Meta:
        database = Mock()


class TestFilterCondition:
    """Test cases for the FilterCondition class."""

    def test_init_with_logical_op_enum(self):
        """Test FilterCondition initialization with LogicalOp enum."""
        condition = FilterCondition(LogicalOp.EQ, 42, 'test_field')
        assert condition.operation == LogicalOp.EQ
        assert condition.value == 42
        assert condition.field_name == 'test_field'

    def test_init_with_string_operation(self):
        """Test FilterCondition initialization with string operation."""
        condition = FilterCondition('>=', 10)
        assert condition.operation == LogicalOp.GE
        assert condition.value == 10
        assert condition.field_name is None

    def test_init_with_invalid_string_operation(self):
        """Test FilterCondition initialization with invalid string operation."""
        with pytest.raises(ValueError, match='Unsupported operation: INVALID'):
            FilterCondition('INVALID', 42)

    @pytest.mark.parametrize(
        'operation,value,expected_calls',
        [
            (LogicalOp.EQ, 42, [('__eq__', 42)]),
            (LogicalOp.NE, 42, [('__ne__', 42)]),
            (LogicalOp.LT, 42, [('__lt__', 42)]),
            (LogicalOp.LE, 42, [('__le__', 42)]),
            (LogicalOp.GT, 42, [('__gt__', 42)]),
            (LogicalOp.GE, 42, [('__ge__', 42)]),
            (LogicalOp.GLOB, 'test*', [('__mod__', 'test*')]),
            (LogicalOp.LIKE, 'test%', [('__pow__', 'test%')]),
        ],
    )
    def test_to_expression_basic_operations(self, operation, value, expected_calls):
        """Test to_expression with basic operations."""
        condition = FilterCondition(operation, value)
        mock_field = Mock()

        # Set up mock return values
        for method_name, _ in expected_calls:
            setattr(mock_field, method_name, Mock(return_value=Mock()))

        condition.to_expression(mock_field)

        # Verify the correct method was called with correct arguments
        for method_name, expected_value in expected_calls:
            getattr(mock_field, method_name).assert_called_once_with(expected_value)

    def test_to_expression_regexp(self):
        """Test to_expression with REGEXP operation."""
        condition = FilterCondition(LogicalOp.REGEXP, r'test\d+')
        mock_field = Mock()
        mock_field.regexp = Mock(return_value=Mock())

        with (
            patch('mafw.db.db_filter.hasattr', return_value=True),
            patch('mafw.db.db_filter.callable', return_value=True),
            patch('mafw.db.db_filter.getattr', return_value=mock_field.regexp),
        ):
            condition.to_expression(mock_field)
            mock_field.regexp.assert_called_once_with(r'test\d+')

    def test_to_expression_regexp_not_available(self):
        """Test to_expression with REGEXP when not available."""
        condition = FilterCondition(LogicalOp.REGEXP, r'test\d+')
        mock_field = Mock()

        with patch('mafw.db.db_filter.hasattr', return_value=False):
            with pytest.raises(ValueError, match='REGEXP operation not supported'):
                condition.to_expression(mock_field)

    def test_to_expression_in_operation(self):
        """Test to_expression with IN operation."""
        condition = FilterCondition(LogicalOp.IN, [1, 2, 3])
        mock_field = Mock()
        mock_field.in_ = Mock(return_value=Mock())

        condition.to_expression(mock_field)
        mock_field.in_.assert_called_once_with([1, 2, 3])

    def test_to_expression_in_operation_invalid_value(self):
        """Test to_expression with IN operation and invalid value type."""
        condition = FilterCondition(LogicalOp.IN, 'not_a_list')
        mock_field = Mock()

        with pytest.raises(TypeError, match='IN operation requires list/tuple'):
            condition.to_expression(mock_field)

    def test_to_expression_not_in_operation(self):
        """Test to_expression with NOT_IN operation."""
        condition = FilterCondition(LogicalOp.NOT_IN, [1, 2, 3])
        mock_field = Mock()
        mock_field.not_in = Mock(return_value=Mock())

        condition.to_expression(mock_field)
        mock_field.not_in.assert_called_once_with([1, 2, 3])

    def test_to_expression_not_in_operation_invalid_value(self):
        """Test to_expression with NOT_IN operation and invalid value type."""
        condition = FilterCondition(LogicalOp.NOT_IN, 42)
        mock_field = Mock()

        with pytest.raises(TypeError, match='NOT_IN operation requires list/tuple'):
            condition.to_expression(mock_field)

    def test_to_expression_between_operation(self):
        """Test to_expression with BETWEEN operation."""
        condition = FilterCondition(LogicalOp.BETWEEN, [1, 10])
        mock_field = Mock()
        mock_field.between = Mock(return_value=Mock())

        condition.to_expression(mock_field)
        mock_field.between.assert_called_once_with(1, 10)

    @pytest.mark.parametrize(
        'invalid_value',
        [
            42,  # not a list
            [1],  # too few elements
            [1, 2, 3],  # too many elements
        ],
    )
    def test_to_expression_between_operation_invalid_value(self, invalid_value):
        """Test to_expression with BETWEEN operation and invalid values."""
        condition = FilterCondition(LogicalOp.BETWEEN, invalid_value)
        mock_field = Mock()

        with pytest.raises(TypeError, match='BETWEEN operation requires list/tuple of 2 elements'):
            condition.to_expression(mock_field)

    def test_to_expression_bit_and_operation(self):
        """Test to_expression with BIT_AND operation."""
        condition = FilterCondition(LogicalOp.BIT_AND, 5)
        mock_field = Mock()
        mock_bin_and_result = Mock()
        mock_field.bin_and = Mock(return_value=mock_bin_and_result)
        mock_bin_and_result.__ne__ = Mock(return_value=Mock())

        condition.to_expression(mock_field)
        mock_field.bin_and.assert_called_once_with(5)
        mock_bin_and_result.__ne__.assert_called_once_with(0)

    def test_to_expression_bit_or_operation(self):
        """Test to_expression with BIT_OR operation."""
        condition = FilterCondition(LogicalOp.BIT_OR, 7)
        mock_field = Mock()
        mock_bin_or_result = Mock()
        mock_field.bin_or = Mock(return_value=mock_bin_or_result)
        mock_bin_or_result.__ne__ = Mock(return_value=Mock())

        condition.to_expression(mock_field)
        mock_field.bin_or.assert_called_once_with(7)
        mock_bin_or_result.__ne__.assert_called_once_with(0)

    def test_to_expression_is_null_operation(self):
        """Test to_expression with IS_NULL operation."""
        condition = FilterCondition(LogicalOp.IS_NULL, None)
        mock_field = Mock()
        mock_field.is_null = Mock(return_value=Mock())

        condition.to_expression(mock_field)
        mock_field.is_null.assert_called_once_with()

    def test_to_expression_is_not_null_operation(self):
        """Test to_expression with IS_NOT_NULL operation."""
        condition = FilterCondition(LogicalOp.IS_NOT_NULL, None)
        mock_field = Mock()
        mock_field.is_null = Mock(return_value=Mock())

        condition.to_expression(mock_field)
        mock_field.is_null.assert_called_once_with(False)

    def test_to_expression_unsupported_operation(self):
        """Test to_expression with unsupported operation."""
        # Create a condition with a valid operation first, then modify it
        condition = FilterCondition(LogicalOp.EQ, 42)
        # Manually set an invalid operation to test the else clause
        condition.operation = 'INVALID_OP'  # type: ignore
        mock_field = Mock()

        with pytest.raises(ValueError, match='Unsupported operation: INVALID_OP'):
            condition.to_expression(mock_field)


class TestFilter:
    """Test cases for the Filter class."""

    @pytest.fixture
    def basic_filter(self):
        """Basic filter fixture."""
        return Filter('TestProcessor.Filter.TestModel', name='test*', active=True, count=[1, 2, 3])

    @pytest.fixture
    def bound_filter(self):
        """Filter bound to a model."""
        flt = Filter('TestProcessor.Filter.MockModel', name='test*', active=True, count=[1, 2, 3])
        flt.bind(MockModel)
        return flt

    def test_init_basic(self):
        """Test basic Filter initialization."""
        flt = Filter('TestProcessor.Filter.TestModel')
        assert flt.name == 'TestProcessor.Filter.TestModel'
        assert flt.model_name == 'TestModel'
        assert flt.model is None
        assert not flt._model_bound
        assert flt._fields == {}

    def test_init_with_kwargs(self):
        """Test Filter initialization with keyword arguments."""
        flt = Filter('TestProcessor.Filter.TestModel', active=True, count=42)
        assert flt.name == 'TestProcessor.Filter.TestModel'
        assert flt.model_name == 'TestModel'
        assert flt._fields == {'active': True, 'count': 42}
        assert flt.get_field('active') is True
        assert flt.get_field('count') == 42

    @pytest.mark.parametrize(
        'name,expected_model_name',
        [
            ('Processor.Filter.Model', 'Model'),
            ('Simple', 'Simple'),
            ('A.B.C.D', 'D'),
            ('Processor.Filter.ComplexModelName', 'ComplexModelName'),
        ],
    )
    def test_model_name_extraction(self, name, expected_model_name):
        """Test model name extraction from filter name."""
        flt = Filter(name)
        assert flt.model_name == expected_model_name

    def test_bind_with_model(self):
        """Test binding filter to a specific model."""
        flt = Filter('TestProcessor.Filter.TestModel')
        flt.bind(MockModel)
        assert flt.model == MockModel
        assert flt.is_bound

    def test_bind_without_model_success(self):
        """Test binding filter without model parameter when model exists in globals."""
        flt = Filter('TestProcessor.Filter.MockModel')
        with patch('mafw.db.db_filter.globals', return_value={'MockModel': MockModel}):
            flt.bind()
            assert flt.model == MockModel
            assert flt.is_bound

    def test_bind_without_model_failure(self):
        """Test binding filter without model parameter when model doesn't exist in globals."""
        flt = Filter('TestProcessor.Filter.NonExistentModel')
        with patch('mafw.db.db_filter.globals', return_value={}):
            flt.bind()
            assert flt.model is None
            assert not flt.is_bound

    def test_is_bound_property(self):
        """Test is_bound property."""
        flt = Filter('TestProcessor.Filter.TestModel')
        assert not flt.is_bound
        flt.bind(MockModel)
        assert flt.is_bound

    def test_get_field_success(self, basic_filter):
        """Test getting existing field."""
        assert basic_filter.get_field('name') == 'test*'
        assert basic_filter.get_field('active') is True
        assert basic_filter.get_field('count') == [1, 2, 3]

    def test_get_field_failure(self, basic_filter):
        """Test getting non-existent field raises KeyError."""
        with pytest.raises(KeyError):
            basic_filter.get_field('nonexistent')

    def test_set_field(self, basic_filter):
        """Test setting field value."""
        basic_filter.set_field('new_field', 'new_value')
        assert basic_filter.get_field('new_field') == 'new_value'
        assert 'new_field' in basic_filter._fields

        # Test updating existing field
        basic_filter.set_field('name', 'updated*')
        assert basic_filter.get_field('name') == 'updated*'

    def test_field_names_property(self, basic_filter):
        """Test field_names property."""
        expected_names = ['name', 'active', 'count']
        assert set(basic_filter.field_names) == set(expected_names)
        assert len(basic_filter.field_names) == 3

    @pytest.mark.parametrize(
        'conf,name,expected_params',
        [
            # Standard dotted notation with matching config
            (
                {'TestProc': {'Filter': {'TestModel': {'field1': 'value1', 'field2': 42}}}},
                'TestProc.Filter.TestModel',
                {'field1': 'value1', 'field2': 42},
            ),
            # Non-existent processor
            ({'OtherProc': {'Filter': {'TestModel': {'field1': 'value1'}}}}, 'TestProc.Filter.TestModel', {}),
            # Non-standard name format
            ({'TestProc': {'Filter': {'TestModel': {'field1': 'value1'}}}}, 'SimpleFilter', {}),
            # With default configuration
            (
                {'TestProc': {'Filter': {'TestModel': {'field1': 'overridden'}}}},
                'TestProc.Filter.TestModel',
                {'default_field': 'default_value', 'field1': 'overridden'},
            ),
        ],
    )
    def test_from_conf(self, conf, name, expected_params):
        """Test creating Filter from configuration."""
        default = {'default_field': 'default_value'} if 'default_field' in str(expected_params) else None
        flt = Filter.from_conf(name, conf, default)

        assert flt.name == name
        for key, value in expected_params.items():
            assert flt.get_field(key) == value

    def test_from_conf_with_copy(self):
        """Test that from_conf creates a copy of the configuration."""
        original_conf = {'field1': 'value1'}
        conf = {'TestProc': {'Filter': {'TestModel': original_conf}}}

        flt = Filter.from_conf('TestProc.Filter.TestModel', conf)
        flt.set_field('field1', 'modified')

        # Original config should not be modified
        assert original_conf['field1'] == 'value1'

    def test_filter_unbound_warning(self):
        """Test filter method with unbound filter shows warning."""
        flt = Filter('TestProcessor.Filter.TestModel', name='test')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            result = flt.filter()

            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert 'Unable to generate the filter' in str(w[0].message)
            assert result is True

    def test_filter_bound_no_fields(self):
        """Test filter method with bound filter but no fields."""
        flt = Filter('TestProcessor.Filter.MockModel')
        flt.bind(MockModel)

        result = flt.filter()
        assert result is True

    def test_filter_bound_with_fields(self, bound_filter):
        """Test filter method with bound filter and fields."""
        # Mock the model fields and their methods
        mock_name_field = Mock()
        mock_active_field = Mock()
        mock_count_field = Mock()

        mock_name_field.__mod__ = Mock(return_value=True)
        mock_active_field.__eq__ = Mock(return_value=True)
        mock_count_field.in_ = Mock(return_value=True)

        # Set up the model to have these fields
        with (
            patch.object(MockModel, 'name', mock_name_field),
            patch.object(MockModel, 'active', mock_active_field),
            patch.object(MockModel, 'count', mock_count_field),
        ):
            bound_filter.filter()

            # Verify field operations were called correctly
            mock_name_field.__mod__.assert_called_once_with('test*')
            mock_active_field.__eq__.assert_called_once_with(True)
            mock_count_field.in_.assert_called_once_with([1, 2, 3])

    @pytest.mark.parametrize(
        'field_value,expected_operation',
        [
            (42, '__eq__'),  # int
            (3.14, '__eq__'),  # float
            (True, '__eq__'),  # bool
            ('test*', '__mod__'),  # string
            ([1, 2, 3], 'in_'),  # list
        ],
    )
    def test_filter_field_types(self, field_value, expected_operation):
        """Test filter method with different field value types."""
        flt = Filter('TestProcessor.Filter.MockModel', name=field_value)
        flt.bind(MockModel)

        mock_field = Mock()

        if expected_operation == 'in_':
            mock_field.in_ = Mock(return_value=True)
        elif expected_operation == '__mod__':
            mock_field.__mod__ = Mock(return_value=True)
        else:  # __eq__
            mock_field.__eq__ = Mock(return_value=True)

        with patch.object(MockModel, 'name', mock_field):
            flt.filter()

            if expected_operation == 'in_':
                mock_field.in_.assert_called_once_with(field_value)
            elif expected_operation == '__mod__':
                mock_field.__mod__.assert_called_once_with(field_value)
            else:
                mock_field.__eq__.assert_called_once_with(field_value)

    def test_filter_with_not_supported_value_type(self):
        with pytest.raises(TypeError):
            # a dictionary as a value is actually supported, but it must have op and value keys because it is the
            # way we pass explicit operation.
            Filter('TestProcessor.Filter.MockModel', name={})

    def test_filter_nonexistent_model_field(self):
        """Test filter method ignores fields that don't exist on the model."""

        flt = Filter('TestProcessor.Filter.MockModel', nonexistent_field='value')
        flt.bind(MockModel)

        result = flt.filter()
        assert result is True  # Should return True when no valid fields


class TestFilterEnhanced:
    """Test cases for the enhanced Filter class functionality."""

    def test_init_with_explicit_dict_operation(self):
        """Test Filter initialization with explicit dict operations."""
        flt = Filter(
            'TestProcessor.Filter.TestModel', flags={'op': 'BIT_AND', 'value': 5}, score={'op': '>=', 'value': 75}
        )

        assert flt.get_field('flags') == {'op': 'BIT_AND', 'value': 5}
        assert flt.get_field('score') == {'op': '>=', 'value': 75}

        # Check that conditions were created
        assert flt._conditions['flags'].operation == LogicalOp.BIT_AND
        assert flt._conditions['flags'].value == 5
        assert flt._conditions['score'].operation == LogicalOp.GE
        assert flt._conditions['score'].value == 75

    def test_create_condition_from_value_int(self):
        """Test _create_condition_from_value with integer."""
        flt = Filter('test')
        condition = flt._create_condition_from_value(42, 'test_field')

        assert condition.operation == LogicalOp.EQ
        assert condition.value == 42
        assert condition.field_name == 'test_field'

    def test_create_condition_from_value_float(self):
        """Test _create_condition_from_value with float."""
        flt = Filter('test')
        condition = flt._create_condition_from_value(3.14, 'test_field')

        assert condition.operation == LogicalOp.EQ
        assert condition.value == 3.14

    def test_create_condition_from_value_bool(self):
        """Test _create_condition_from_value with boolean."""
        flt = Filter('test')
        condition = flt._create_condition_from_value(True, 'test_field')

        assert condition.operation == LogicalOp.EQ
        assert condition.value is True

    def test_create_condition_from_value_string(self):
        """Test _create_condition_from_value with string."""
        flt = Filter('test')
        condition = flt._create_condition_from_value('test*', 'test_field')

        assert condition.operation == LogicalOp.GLOB
        assert condition.value == 'test*'

    def test_create_condition_from_value_list(self):
        """Test _create_condition_from_value with list."""
        flt = Filter('test')
        condition = flt._create_condition_from_value([1, 2, 3], 'test_field')

        assert condition.operation == LogicalOp.IN
        assert condition.value == [1, 2, 3]

    def test_create_condition_from_value_unsupported_type(self):
        """Test _create_condition_from_value with unsupported type."""
        flt = Filter('test')

        with pytest.raises(TypeError, match='Filter value of unsupported type .* for field test_field'):
            flt._create_condition_from_value(object(), 'test_field')

    def test_set_field_with_explicit_operation(self):
        """Test set_field with explicit operation dictionary."""
        flt = Filter('TestProcessor.Filter.TestModel')

        flt.set_field('new_field', {'op': 'BIT_AND', 'value': 5})

        assert flt.get_field('new_field') == {'op': 'BIT_AND', 'value': 5}
        assert flt._conditions['new_field'].operation == LogicalOp.BIT_AND
        assert flt._conditions['new_field'].value == 5

    def test_set_field_with_simple_value(self):
        """Test set_field with simple value."""
        flt = Filter('TestProcessor.Filter.TestModel')

        flt.set_field('new_field', 'test_value')

        assert flt.get_field('new_field') == 'test_value'
        assert flt._conditions['new_field'].operation == LogicalOp.GLOB
        assert flt._conditions['new_field'].value == 'test_value'

    def test_get_condition(self):
        """Test get_condition method."""
        flt = Filter('TestProcessor.Filter.TestModel', name='test*')

        condition = flt.get_condition('name')
        assert condition.operation == LogicalOp.GLOB
        assert condition.value == 'test*'

    def test_get_condition_nonexistent(self):
        """Test get_condition with nonexistent field."""
        flt = Filter('TestProcessor.Filter.TestModel')

        with pytest.raises(KeyError):
            flt.get_condition('nonexistent')

    def test_set_condition_with_enum(self):
        """Test set_condition method with LogicalOp enum."""
        flt = Filter('TestProcessor.Filter.TestModel')

        flt.set_condition('test_field', LogicalOp.GE, 10)

        condition = flt.get_condition('test_field')
        assert condition.operation == LogicalOp.GE
        assert condition.value == 10

        # Check backward compatibility fields
        assert flt.get_field('test_field') == {'op': '>=', 'value': 10}

    def test_set_condition_with_string(self):
        """Test set_condition method with string operation."""
        flt = Filter('TestProcessor.Filter.TestModel')

        flt.set_condition('test_field', 'BIT_AND', 5)

        condition = flt.get_condition('test_field')
        assert condition.operation == LogicalOp.BIT_AND
        assert condition.value == 5

    def test_filter_with_or_join(self):
        """Test filter method with OR join."""
        flt = Filter('TestProcessor.Filter.MockModel', name='test*', active=True)
        flt.bind(MockModel)

        # Mock the model fields
        mock_name_field = Mock()
        mock_active_field = Mock()
        mock_name_expr = Mock()
        mock_active_expr = Mock()

        mock_name_field.__mod__ = Mock(return_value=mock_name_expr)
        mock_active_field.__eq__ = Mock(return_value=mock_active_expr)

        with (
            patch.object(MockModel, 'name', mock_name_field),
            patch.object(MockModel, 'active', mock_active_field),
            patch('mafw.db.db_filter.reduce') as mock_reduce,
        ):
            mock_reduce.return_value = 'or_expression'
            result = flt.filter(join_with='OR')

            mock_reduce.assert_called_once()
            args = mock_reduce.call_args[0]
            assert args[0] == operator.or_  # operator should be OR
            assert result == 'or_expression'

    def test_filter_invalid_join_with(self):
        """Test filter method with invalid join_with parameter."""
        flt = Filter('TestProcessor.Filter.MockModel', name='test*')
        flt.bind(MockModel)

        with pytest.raises(ValueError, match="join_with must be 'AND' or 'OR'"):
            flt.filter(join_with='INVALID')

    def test_filter_with_explicit_operations(self):
        """Test filter method with explicit operations."""
        flt = Filter(
            'TestProcessor.Filter.MockModel', flags={'op': 'BIT_AND', 'value': 5}, count={'op': '>=', 'value': 10}
        )
        flt.bind(MockModel)

        # Mock the model fields and their operations
        mock_flags_field = Mock()
        mock_count_field = Mock()
        mock_bin_and_result = Mock()
        mock_ge_result = Mock()

        mock_flags_field.bin_and = Mock(return_value=mock_bin_and_result)
        mock_bin_and_result.__ne__ = Mock(return_value=Mock())
        mock_count_field.__ge__ = Mock(return_value=mock_ge_result)

        with (
            patch.object(MockModel, 'flags', mock_flags_field),
            patch.object(MockModel, 'count', mock_count_field),
            patch('mafw.db.db_filter.reduce') as mock_reduce,
        ):
            mock_reduce.return_value = True
            flt.filter()

            mock_reduce.assert_called_once()
            mock_flags_field.bin_and.assert_called_once_with(5)
            mock_bin_and_result.__ne__.assert_called_once_with(0)
            mock_count_field.__ge__.assert_called_once_with(10)

    def test_filter_condition_creation_error(self):
        """Test filter method when condition creation fails."""
        flt = Filter('TestProcessor.Filter.MockModel', name='test*')
        flt.bind(MockModel)

        # Mock a condition that raises an error
        with patch.object(flt._conditions['name'], 'to_expression') as mock_to_expr:
            mock_to_expr.side_effect = TypeError('Test error')

            with patch.object(MockModel, 'name', Mock()):
                with pytest.raises(TypeError, match='Error creating filter for field name: Test error'):
                    flt.filter()

    def test_filter_empty_expression_list(self):
        """Test filter method when no valid expressions are created."""
        flt = Filter('TestProcessor.Filter.MockModel', nonexistent='value')
        flt.bind(MockModel)

        import warnings

        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            result = flt.filter()
            assert result is True

    def test_filter_mixed_traditional_and_explicit(self):
        """Test filter with mix of traditional and explicit operations."""
        flt = Filter(
            'TestProcessor.Filter.MockModel',
            name='test*',  # traditional
            flags={'op': 'BIT_AND', 'value': 5},  # explicit
            active=True,  # traditional
        )
        flt.bind(MockModel)

        # Verify conditions were created correctly
        assert flt._conditions['name'].operation == LogicalOp.GLOB
        assert flt._conditions['flags'].operation == LogicalOp.BIT_AND
        assert flt._conditions['active'].operation == LogicalOp.EQ

    def test_init_with_invalid_dict_operation(self):
        """Test Filter initialization with invalid dict operation (missing keys)."""
        with pytest.raises(TypeError):
            Filter('TestProcessor.Filter.TestModel', field={'missing_op': 'value'})


class TestFilterRegister:
    """Test cases for the FilterRegister class."""

    @pytest.fixture
    def empty_register(self):
        """Empty FilterRegister fixture."""
        return FilterRegister()

    @pytest.fixture
    def populated_register(self):
        """FilterRegister with some filters."""
        flt1 = Filter('Proc.Filter.MockModel', field1='value1')
        flt2 = Filter('Proc.Filter.AnotherMockModel', field2='value2')
        return FilterRegister({'MockModel': flt1, 'AnotherMockModel': flt2})

    def test_init_empty(self):
        """Test FilterRegister initialization without data."""
        register = FilterRegister()
        assert len(register) == 0
        assert register._global_filter == {}
        assert register.new_only is True  # Default value

    def test_init_with_data(self):
        """Test FilterRegister initialization with data."""
        flt = Filter('Test.Filter.Model', field='value')
        register = FilterRegister({'Model': flt})
        assert len(register) == 1
        assert register['Model'] == flt

    def test_new_only_property_default(self, empty_register):
        """Test new_only property default value."""
        assert empty_register.new_only is True

    def test_new_only_property_get_set(self, empty_register):
        """Test new_only property getter and setter."""
        empty_register.new_only = False
        assert empty_register.new_only is False
        assert empty_register._global_filter['new_only'] is False

        empty_register.new_only = True
        assert empty_register.new_only is True

    def test_new_only_property_from_global_filter(self):
        """Test new_only property when set in global filter."""
        register = FilterRegister()
        register._global_filter['new_only'] = False
        assert register.new_only is False

    def test_setitem_valid_filter(self, empty_register):
        """Test setting valid Filter object."""
        flt = Filter('Test.Filter.Model', field='value')
        empty_register['Model'] = flt
        assert empty_register['Model'] == flt
        assert len(empty_register) == 1

    def test_setitem_invalid_type(self, empty_register):
        """Test setting invalid type is silently ignored."""
        initial_len = len(empty_register)
        empty_register['Model'] = 'not a filter'
        empty_register['Model2'] = 42
        empty_register['Model3'] = None

        assert len(empty_register) == initial_len
        assert 'Model' not in empty_register
        assert 'Model2' not in empty_register
        assert 'Model3' not in empty_register

    def test_bind_all_with_list(self, populated_register):
        """Test bind_all method with list of models."""
        models = [MockModel, AnotherMockModel]

        # Mock the bind method on filters
        with (
            patch.object(populated_register['MockModel'], 'bind') as mock_bind1,
            patch.object(populated_register['AnotherMockModel'], 'bind') as mock_bind2,
        ):
            populated_register.bind_all(models)

            mock_bind1.assert_called_once_with(MockModel)
            mock_bind2.assert_called_once_with(AnotherMockModel)

    def test_bind_all_with_dict(self, populated_register):
        """Test bind_all method with dictionary of models."""
        models = {'MockModel': MockModel, 'AnotherMockModel': AnotherMockModel}

        with (
            patch.object(populated_register['MockModel'], 'bind') as mock_bind1,
            patch.object(populated_register['AnotherMockModel'], 'bind') as mock_bind2,
        ):
            populated_register.bind_all(models)

            mock_bind1.assert_called_once_with(MockModel)
            mock_bind2.assert_called_once_with(AnotherMockModel)

    def test_bind_all_creates_missing_filters(self, empty_register):
        """Test bind_all creates filters for models not in register."""
        models = {'NewModel': MockModel}
        empty_register._global_filter = {'default_field': 'default_value'}

        with patch.object(Filter, 'from_conf') as mock_from_conf:
            mock_filter = Mock(spec=Filter)
            mock_from_conf.return_value = mock_filter

            empty_register.bind_all(models)

            mock_from_conf.assert_called_once_with('NewModel', conf={}, default={'default_field': 'default_value'})
            assert 'NewModel' in empty_register
            mock_filter.bind.assert_called_once_with(MockModel)

    def test_bind_all_fallback_bind(self, populated_register):
        """Test bind_all falls back to parameterless bind when filter not in models dict."""
        # populated_register has 'Model1' and 'Model2' filters
        # but we only provide models for 'Model1'
        models = {'MockModel': MockModel}  # Only one model, but register has two filters

        with (
            patch.object(populated_register['MockModel'], 'bind') as mock_bind1,
            patch.object(populated_register['AnotherMockModel'], 'bind') as mock_bind2,
        ):
            populated_register.bind_all(models)

            # MockModel should bind with the provided model
            mock_bind1.assert_called_once_with(MockModel)
            # AnotherMockModel should fall back to parameterless bind (tries to find in globals)
            mock_bind2.assert_called_once_with()

    def test_bind_all_fallback_bind_more_models(self, populated_register):
        # the registry has two models, but the model dict has three.
        models = {'MockModel': MockModel, 'AnotherMockModel': AnotherMockModel, 'LastMockModel': LastMockModel}

        # Mock the existing filters
        with (
            patch.object(populated_register['MockModel'], 'bind') as mock_bind1,
            patch.object(populated_register['AnotherMockModel'], 'bind') as mock_bind2,
            patch.object(Filter, 'from_conf') as mock_from_conf,
        ):
            # Mock the new filter creation
            mock_new_filter = Mock(spec=Filter)
            mock_from_conf.return_value = mock_new_filter

            populated_register.bind_all(models)

            # Assert register now has three items
            assert len(populated_register) == 3
            assert 'MockModel' in populated_register
            assert 'AnotherMockModel' in populated_register
            assert 'LastMockModel' in populated_register

            # Assert existing filters were bound with their models
            mock_bind1.assert_called_once_with(MockModel)
            mock_bind2.assert_called_once_with(AnotherMockModel)

            # Assert new filter was created and bound
            mock_from_conf.assert_called_once_with('LastMockModel', conf={}, default=populated_register._global_filter)
            mock_new_filter.bind.assert_called_once_with(LastMockModel)

    def test_filter_all_empty(self, empty_register):
        """Test filter_all with empty register."""
        result = empty_register.filter_all()
        assert result is True

    def test_filter_all_with_bound_filters(self, populated_register):
        """Test filter_all with bound filters."""
        # Mock the filters and their filter methods
        mock_expr1 = Mock()
        mock_expr2 = Mock()

        populated_register['MockModel'].filter = Mock(return_value=mock_expr1)
        populated_register['MockModel']._model_bound = True  # fake binding
        populated_register['AnotherMockModel'].filter = Mock(return_value=mock_expr2)
        populated_register['AnotherMockModel']._model_bound = True  # fake binding

        with patch('mafw.db.db_filter.reduce') as mock_reduce:
            mock_reduce.return_value = 'combined_expression'

            result = populated_register.filter_all()

            mock_reduce.assert_called_once_with(operator.and_, [mock_expr1, mock_expr2], True)
            assert result == 'combined_expression'

    def test_filter_all_with_unbound_filters(self, populated_register):
        """Test filter_all ignores unbound filters."""
        mock_expr1 = Mock()

        populated_register['MockModel'].filter = Mock(return_value=mock_expr1)
        populated_register['MockModel']._model_bound = True  # fake binding
        populated_register['AnotherMockModel'].filter = Mock(return_value=Mock())
        assert not populated_register['AnotherMockModel'].is_bound  # not bound

        with patch('mafw.db.db_filter.reduce') as mock_reduce:
            mock_reduce.return_value = 'single_expression'

            result = populated_register.filter_all()

            # Should only include the bound filter
            mock_reduce.assert_called_once_with(operator.and_, [mock_expr1], True)
            assert result == 'single_expression'

    def test_filter_all_no_bound_filters(self, populated_register):
        """Test filter_all when no filters are bound."""
        assert not populated_register['MockModel'].is_bound
        assert not populated_register['AnotherMockModel'].is_bound

        result = populated_register.filter_all()
        assert result is True


class TestFilterRegisterEnhanced:
    """Test cases for enhanced FilterRegister functionality."""

    def test_filter_all_with_or_join(self):
        """Test filter_all with OR join."""
        flt1 = Filter('Proc.Filter.MockModel', field1='value1')
        flt2 = Filter('Proc.Filter.MockModel2', field2='value2')

        register = FilterRegister({'MockModel': flt1, 'MockModel2': flt2})

        # Mock the filters as bound and their filter methods
        mock_expr1 = Mock()
        mock_expr2 = Mock()

        flt1._model_bound = True
        flt2._model_bound = True
        flt1.filter = Mock(return_value=mock_expr1)
        flt2.filter = Mock(return_value=mock_expr2)

        with patch('mafw.db.db_filter.reduce') as mock_reduce:
            mock_reduce.return_value = 'or_combined_expression'

            result = register.filter_all(join_with='OR')

            mock_reduce.assert_called_once()
            args = mock_reduce.call_args[0]
            assert args[0] == operator.or_  # operator should be OR
            assert result == 'or_combined_expression'

    def test_filter_all_invalid_join_with(self):
        """Test filter_all with invalid join_with parameter."""
        register = FilterRegister()

        # filter_all doesn't validate join_with, it just passes it to reduce
        # But we can test that it handles the parameter correctly
        with patch('mafw.db.db_filter.reduce') as mock_reduce:
            mock_reduce.return_value = True
            register.filter_all(join_with='OR')

            # Should call reduce with operator.or_
            mock_reduce.assert_called_once()
            args = mock_reduce.call_args[0]
            assert args[0] == operator.or_


@pytest.mark.integration_test
class TestIntegration:
    """Integration tests combining Filter and FilterRegister."""

    def test_filter_register_workflow(self):
        """Test typical workflow with FilterRegister and Filter."""
        # Create configuration
        conf = {
            'TestProcessor': {
                'Filter': {
                    'MockModel': {'name': 'test*', 'active': True},
                    'AnotherMockModel': {'description': 'sample'},
                }
            }
        }

        # Create filters from configuration
        flt1 = Filter.from_conf('TestProcessor.Filter.MockModel', conf)
        flt2 = Filter.from_conf('TestProcessor.Filter.AnotherMockModel', conf)

        # Create register and add filters
        register = FilterRegister()
        register['MockModel'] = flt1
        register['AnotherMockModel'] = flt2

        # Bind all filters
        models = [MockModel, AnotherMockModel]
        register.bind_all(models)

        # Verify filters are bound
        assert register['MockModel'].is_bound
        assert register['AnotherMockModel'].is_bound

        # Verify filter generation works
        assert register['MockModel'].filter() is not True  # Should generate expressions
        assert register['AnotherMockModel'].filter() is not True

    @pytest.mark.parametrize(
        'global_new_only,expected',
        [
            (True, True),
            (False, False),
            (None, True),  # Default value
        ],
    )
    def test_global_filter_new_only_integration(self, global_new_only, expected):
        """Test global filter new_only flag integration."""
        register = FilterRegister()
        if global_new_only is not None:
            register.new_only = global_new_only

        assert register.new_only == expected


# Integration tests for the enhanced functionality
@pytest.mark.integration_test
class TestEnhancedIntegration:
    """Integration tests for enhanced functionality."""

    def test_explicit_operations_end_to_end(self):
        """Test explicit operations from configuration to query generation."""
        # Create configuration with explicit operations
        conf = {
            'TestProcessor': {
                'Filter': {
                    'MockModel': {
                        'flags': {'op': 'BIT_AND', 'value': 5},
                        'count': {'op': '>=', 'value': 10},
                        'name': {'op': 'LIKE', 'value': 'test%'},
                    }
                }
            }
        }

        # Create filter from configuration
        flt = Filter.from_conf('TestProcessor.Filter.MockModel', conf)

        # Verify the filter was created with correct conditions
        assert flt._conditions['flags'].operation == LogicalOp.BIT_AND
        assert flt._conditions['count'].operation == LogicalOp.GE
        assert flt._conditions['name'].operation == LogicalOp.LIKE

        # Bind to model
        flt.bind(MockModel)
        assert flt.is_bound

        # Test that filter generation works by mocking the reduce function
        mock_expr1 = Mock()
        mock_expr2 = Mock()
        mock_expr3 = Mock()

        # Mock the field operations to return expressions
        mock_flags_field = Mock()
        mock_count_field = Mock()
        mock_name_field = Mock()

        mock_bin_and_result = Mock()
        mock_flags_field.bin_and = Mock(return_value=mock_bin_and_result)
        mock_bin_and_result.__ne__ = Mock(return_value=mock_expr1)
        mock_count_field.__ge__ = Mock(return_value=mock_expr2)
        mock_name_field.__pow__ = Mock(return_value=mock_expr3)

        with (
            patch.object(MockModel, 'flags', mock_flags_field),
            patch.object(MockModel, 'count', mock_count_field),
            patch.object(MockModel, 'name', mock_name_field),
            patch('mafw.db.db_filter.reduce') as mock_reduce,
        ):
            mock_reduce.return_value = 'combined_expression'
            result = flt.filter()

            # Verify reduce was called with the correct expressions
            mock_reduce.assert_called_once()
            args = mock_reduce.call_args[0]
            assert args[0] == operator.and_
            assert mock_expr1 in args[1]
            assert mock_expr2 in args[1]
            assert mock_expr3 in args[1]
            assert result == 'combined_expression'

    def test_mixed_operations_with_filter_register(self):
        """Test mixed traditional and explicit operations with FilterRegister."""
        # Create filters with mixed operation types
        flt1 = Filter(
            'Proc.Filter.MockModel',
            name='test*',  # traditional
            flags={'op': 'BIT_AND', 'value': 5},
        )  # explicit

        flt2 = Filter(
            'Proc.Filter.MockModel2',
            active=True,  # traditional
            score={'op': '>=', 'value': 75},
        )  # explicit

        register = FilterRegister({'MockModel': flt1, 'MockModel2': flt2})

        # Bind filters
        models = {'MockModel': MockModel, 'MockModel2': MockModel}
        register.bind_all(models)

        # Verify all filters are bound
        assert register['MockModel'].is_bound
        assert register['MockModel2'].is_bound

        # Test that combined filtering works by mocking individual filter results
        mock_filter_expr1 = Mock()
        mock_filter_expr2 = Mock()

        with (
            patch.object(flt1, 'filter', return_value=mock_filter_expr1),
            patch.object(flt2, 'filter', return_value=mock_filter_expr2),
            patch('mafw.db.db_filter.reduce') as mock_reduce,
        ):
            mock_reduce.return_value = 'combined_register_expression'
            result = register.filter_all()

            # Verify reduce was called with both filter expressions
            mock_reduce.assert_called_once()
            args = mock_reduce.call_args[0]
            assert args[0] == operator.and_
            assert mock_filter_expr1 in args[1]
            assert mock_filter_expr2 in args[1]
            assert result == 'combined_register_expression'
