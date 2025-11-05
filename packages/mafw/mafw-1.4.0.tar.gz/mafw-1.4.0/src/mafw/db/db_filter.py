#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
The module provides the capability to filter model classes with information taken from the steering file.
"""

import operator
import warnings
from collections import UserDict
from copy import copy
from functools import reduce
from typing import Any, Self, cast

import peewee
from peewee import Model

from mafw.enumerators import LogicalOp


class FilterCondition:
    """
    Represents a single filter condition with operation and value(s).

    This allows for explicit specification of logical operations beyond
    the automatic type-based determination.

    .. versionadded:: 1.3.0
       Before only implicit types of conditions were allowed.
    """

    def __init__(self, operation: LogicalOp | str, value: Any, field_name: str | None = None):
        """
        Initialize a filter condition.

        :param operation: The logical operation to apply
        :param value: The value(s) to compare against
        :param field_name: Optional field name for error reporting
        """
        if isinstance(operation, str):
            try:
                self.operation = LogicalOp(operation)
            except ValueError:
                raise ValueError(f'Unsupported operation: {operation}')
        else:
            self.operation = operation
        self.value = value
        self.field_name = field_name

    def to_expression(self, model_field: peewee.Field) -> peewee.Expression:
        """
        Convert this condition to a Peewee expression.

        :param model_field: The Peewee model field
        :return: The expression
        """
        op = self.operation
        val = self.value

        # the code is full of cast and redundant checks to make mypy happy.
        # I do not know to which extent they make the code safer, but for sure they make it less readable.
        if op == LogicalOp.EQ:
            return cast(peewee.Expression, model_field == val)
        elif op == LogicalOp.NE:
            return cast(peewee.Expression, model_field != val)
        elif op == LogicalOp.LT:
            return cast(peewee.Expression, model_field < val)
        elif op == LogicalOp.LE:
            return cast(peewee.Expression, model_field <= val)
        elif op == LogicalOp.GT:
            return cast(peewee.Expression, model_field > val)
        elif op == LogicalOp.GE:
            return cast(peewee.Expression, model_field >= val)
        elif op == LogicalOp.GLOB:
            return cast(peewee.Expression, model_field % val)
        elif op == LogicalOp.LIKE:
            return cast(peewee.Expression, model_field**val)
        elif op == LogicalOp.REGEXP:
            if hasattr(model_field, 'regexp') and callable(getattr(model_field, 'regexp')):
                return cast(peewee.Expression, getattr(model_field, 'regexp')(val))
            else:
                raise ValueError(f'REGEXP operation not supported for field type {type(model_field)}')
        elif op == LogicalOp.IN:
            if not isinstance(val, (list, tuple)):
                raise TypeError(f'IN operation requires list/tuple, got {type(val)}')
            if hasattr(model_field, 'in_') and callable(getattr(model_field, 'in_')):
                return cast(peewee.Expression, getattr(model_field, 'in_')(val))
            else:
                raise ValueError(f'IN operation not supported for field type {type(model_field)}')  # no cov
        elif op == LogicalOp.NOT_IN:
            if not isinstance(val, (list, tuple)):
                raise TypeError(f'NOT_IN operation requires list/tuple, got {type(val)}')
            if hasattr(model_field, 'not_in') and callable(getattr(model_field, 'not_in')):
                return cast(peewee.Expression, getattr(model_field, 'not_in')(val))
            else:
                raise ValueError(f'NOT_IN operation not supported for field type {type(model_field)}')  # no cov
        elif op == LogicalOp.BETWEEN:
            if not isinstance(val, (list, tuple)) or len(val) != 2:
                raise TypeError(f'BETWEEN operation requires list/tuple of 2 elements, got {val}')
            if hasattr(model_field, 'between') and callable(getattr(model_field, 'between')):
                return cast(peewee.Expression, getattr(model_field, 'between')(val[0], val[1]))
            else:
                raise ValueError(f'BETWEEN operation not supported for field type {type(model_field)}')  # no cov
        elif op == LogicalOp.BIT_AND:
            if hasattr(model_field, 'bin_and') and callable(getattr(model_field, 'bin_and')):
                return cast(peewee.Expression, getattr(model_field, 'bin_and')(val) != 0)
            else:
                raise ValueError(f'BIT_AND operation not supported for field type {type(model_field)}')  # no cov
        elif op == LogicalOp.BIT_OR:
            if hasattr(model_field, 'bin_or') and callable(getattr(model_field, 'bin_or')):
                return cast(peewee.Expression, getattr(model_field, 'bin_or')(val) != 0)
            else:
                raise ValueError(f'BIT_OR operation not supported for field type {type(model_field)}')  # no cov
        elif op == LogicalOp.IS_NULL:
            return model_field.is_null()
        elif op == LogicalOp.IS_NOT_NULL:
            return model_field.is_null(False)
        else:
            raise ValueError(f'Unsupported operation: {op}')


class Filter:
    r"""
    Class to filter rows from a model.

    The filter object can be used to generate a where clause to be applied to Model.select().

    The construction of a Filter is normally done via a configuration file using the :meth:`from_conf` class method.
    The name of the filter is playing a key role in this. If it follows a dot structure like:

        *ProcessorName.Filter.ModelName*

    then the corresponding table from the TOML configuration object will be used.

    For each processor, there might be many Filters, up to one for each Model used to get the input list. If a
    processor is joining together three Models when performing the input select, there will be up to three Filters
    collaborating on making the selection.

    The filter configuration can contain the following key, value pair:

        - key / string pairs, where the key is the name of a field in the corresponding Model

        - key / numeric pairs

        - key / arrays

        - key / dict pairs with 'op' and 'value' keys for explicit operation specification

    All fields from the configuration file will be added to the instance namespace, thus accessible with the dot
    notation. Moreover, the field names and their filter value will be added to a private dictionary to simplify the
    generation of the filter SQL code.

    The user can use the filter object to store selection criteria. He can construct queries using the filter
    contents in the same way as he could use processor parameters.

    If he wants to automatically generate valid filtering expression, he can use the :meth:`filter` method. In order
    for this to work, the Filter object be :meth:`bound <bind>` to a Model. Without this binding the Filter will not
    be able to automatically generate expressions.

    For each field in the filter, one condition will be generated according to the following scheme:

    =================   =================   ==================
    Filter field type   Logical operation      Example
    =================   =================   ==================
    Numeric, boolean        ==               Field == 3.14
    String                 GLOB             Field GLOB '\*ree'
    List                   IN               Field IN [1, 2, 3]
    Dict (explicit)     op from dict         Field BIT_AND 5
    =================   =================   ==================

    All conditions will be joined with a AND logic by default, but this can be changed.

    Consider the following example:

    .. code-block:: python
        :linenos:

        class MeasModel(MAFwBaseModel):
            meas_id = AutoField(primary_key=True)
            sample_name = TextField()
            successful = BooleanField()
            flags = IntegerField()


        # Traditional simplified usage
        flt = Filter(
            'MyProcessor.Filter.MyModel',
            sample_name='sample_00*',
            meas_id=[1, 2, 3],
            successful=True,
        )

        # New explicit operation usage
        flt = Filter(
            'MyProcessor.Filter.MyModel',
            sample_name={'op': 'LIKE', 'value': 'sample_00%'},
            flags={'op': 'BIT_AND', 'value': 5},
            meas_id={'op': 'IN', 'value': [1, 2, 3]},
        )

        flt.bind(MeasModel)
        filtered_query = MeasModel.select().where(flt.filter())

    The explicit operation format allows for bitwise operations and other advanced filtering.

    TOML Configuration Examples:

    .. code-block:: toml

        [MyProcessor.Filter.MyModel]
        sample_name = "sample_00*"  # Traditional GLOB
        successful = true           # Traditional equality

        # Explicit operations
        flags = { op = "BIT_AND", value = 5 }
        score = { op = ">=", value = 75.0 }
        category = { op = "IN", value = ["A", "B", "C"] }
        date_range = { op = "BETWEEN", value = ["2024-01-01", "2024-12-31"] }

    """

    def __init__(self, name_: str, **kwargs: Any) -> None:
        """
        Constructor parameters:

        :param `name_`: The name of the filter. It should be in dotted format to facilitate the configuration via the
            steering file. The _ is used to allow the user to have a keyword argument named name.
        :type `name_`: str
        :param kwargs: Keyword parameters corresponding to fields and filter values.

        .. versionchanged:: 1.2.0
            The parameter *name* has been renamed as *name_*.

        .. versionchanged:: 1.3.0
           From this version also explicit operations are implemented.
           When more conditions are provided, it is now possible to decide how to
           join them.

        """
        self.name = name_
        self.model_name = name_.split('.')[-1]
        self.model: type[Model] | None = None
        self._model_bound: bool = False
        self._fields = {}
        self._conditions: dict[str, FilterCondition] = {}

        for k, v in kwargs.items():
            self._fields[k] = v
            setattr(self, k, v)

            # Parse the value to create appropriate FilterCondition
            if isinstance(v, dict) and 'op' in v and 'value' in v:
                # Explicit operation specification
                self._conditions[k] = FilterCondition(v['op'], v['value'], k)
            else:
                # Traditional automatic type-based operation
                self._conditions[k] = self._create_condition_from_value(v, k)

    @staticmethod
    def _create_condition_from_value(value: Any, field_name: str) -> FilterCondition:
        """
        Create a FilterCondition based on value type (backward compatibility).

        :param value: The filter value
        :param field_name: The field name
        :return: A FilterCondition
        """
        if isinstance(value, (int, float, bool)):
            return FilterCondition(LogicalOp.EQ, value, field_name)
        elif isinstance(value, str):
            return FilterCondition(LogicalOp.GLOB, value, field_name)
        elif isinstance(value, list):
            return FilterCondition(LogicalOp.IN, value, field_name)
        else:
            raise TypeError(f'Filter value of unsupported type {type(value)} for field {field_name}.')

    def bind(self, model: type[Model] | None = None) -> None:
        """
        Connects a filter to a Model class.

        If no model is provided, the method will try to bind a class from with global dictionary with a name matching
        the model name used during the Filter configuration. It only works when the Model is defined as global.

        :param model: Model to be bound. Defaults to None
        :type model: Model, Optional
        """
        if model is None:
            if self.model_name in globals():
                self.model = globals()[self.model_name]
                self._model_bound = True
        else:
            self.model = model
            self._model_bound = True

    @property
    def is_bound(self) -> bool:
        """Returns true if the Filter has been bound to a Model"""
        return self._model_bound

    def get_field(self, key: str) -> Any:
        """
        Gets a field by name.

        :param key: The name of the field.
        :type key: str
        :return: The value of the field.
        :rtype: Any
        :raises KeyError: if the requested field does not exist.
        """
        return self._fields[key]

    def set_field(self, key: str, value: Any) -> None:
        """
        Sets the value of a field by name

        :param key: The name of the field.
        :type key: str
        :param value: The value of the field.
        :type value: Any
        """
        self._fields[key] = value
        # Update the condition as well
        if isinstance(value, dict) and 'op' in value and 'value' in value:
            self._conditions[key] = FilterCondition(value['op'], value['value'], key)
        else:
            self._conditions[key] = self._create_condition_from_value(value, key)

    def get_condition(self, key: str) -> FilterCondition:
        """
        Gets a filter condition by field name.

        .. versionadded:: 1.3.0

        :param key: The field name
        :return: The FilterCondition
        :raises KeyError: if the field does not exist
        """
        return self._conditions[key]

    def set_condition(self, key: str, operation: LogicalOp | str, value: Any) -> None:
        """
        Sets a filter condition explicitly.

        .. versionadded:: 1.3.0

        :param key: The field name
        :param operation: The logical operation
        :param value: The filter value
        """
        condition = FilterCondition(operation, value, key)
        self._conditions[key] = condition

        # Also update the fields dict and attribute for backward compatibility
        if isinstance(operation, LogicalOp):
            op_str = operation.value
        else:
            op_str = operation
        self._fields[key] = {'op': op_str, 'value': value}
        setattr(self, key, {'op': op_str, 'value': value})

    @property
    def field_names(self) -> list[str]:
        """The list of field names."""
        return list(self._fields.keys())

    @classmethod
    def from_conf(cls, name: str, conf: dict[str, Any], default: dict[str, Any] | None = None) -> Self:
        """
        Builds a Filter object from a steering file dictionary.

        If the name is in dotted notation, then this should be corresponding to the table in the configuration file.
        If a default configuration is provided, this will be used as a starting point for the filter, and it will be
        updated by the actual configuration in ``conf``.

        In normal use, you would provide the specific configuration via the conf parameter and the global filter
        configuration as default.

        See details in the :class:`class documentation <Filter>`

        :param name: The name of the filter in dotted notation.
        :type name: str
        :param conf: The configuration dictionary.
        :type conf: dict
        :param default: Default configuration dictionary
        :type default: dict
        :return: A Filter object
        :rtype: Filter
        """
        param = default or {}

        # split the name from dotted notation
        # ProcessorName.ModelName.Filter
        names = name.split('.')
        if len(names) == 3 and names[1] == 'Filter':
            proc_name, _, model_name = names
            if proc_name in conf and 'Filter' in conf[proc_name] and model_name in conf[proc_name]['Filter']:
                param.update(copy(conf[proc_name]['Filter'][model_name]))

        # if the name is not in the expected dotted notation, then param will be the default, that very likely means
        # the global filter configuration.
        return cls(name, **param)

    def filter(self, join_with: str = 'AND') -> peewee.Expression | bool:
        """
        Generates a filtering expression joining all filtering fields.

        See details in the :class:`class documentation <Filter>`

        .. versionchanged:: 1.3.0
           Add the possibility to specify a `join_with` function

        :param join_with: How to join conditions ('AND' or 'OR'). Defaults to 'AND'.
        :type join_with: str
        :return: The filtering expression.
        :rtype: peewee.Expression | bool
        :raises TypeError: when the field value type is not supported.
        :raises ValueError: when join_with is not 'AND' or 'OR'.
        """
        if not self.is_bound:
            warnings.warn('Unable to generate the filter. Did you bind the filter to the model?')
            return True

        if join_with not in ['AND', 'OR']:
            raise ValueError("join_with must be 'AND' or 'OR'")

        expression_list = []
        for field_name, condition in self._conditions.items():
            if hasattr(self.model, field_name):
                model_field = getattr(self.model, field_name)
                try:
                    expression = condition.to_expression(model_field)
                    expression_list.append(expression)
                except (TypeError, ValueError) as e:
                    raise TypeError(f'Error creating filter for field {field_name}: {e}')

        if not expression_list:
            return True

        if join_with == 'AND':
            return reduce(operator.and_, expression_list)
        else:  # OR
            return reduce(operator.or_, expression_list)


class FilterRegister(UserDict[str, Filter]):
    """
    A special dictionary to store all :class:`Filters <mafw.db.db_filter.Filter>` in a processors.

    It contains a publicly accessible dictionary with the configuration of each Filter using the Model name as
    keyword.

    It contains a private dictionary with the global filter configuration as well.
    The global filter is not directly accessible, but only some of its members will be exposed via properties.
    In particular, the new_only flag that is relevant only at the Processor level can be accessed directly using the
    :attr:`new_only`. If not specified in the configuration file, the new_only is by default True.
    """

    def __init__(self, data: dict[str, Filter] | None = None, /, **kwargs: Any) -> None:
        """
        Constructor parameters:

        :param data: Initial data
        :type data: dict
        :param kwargs: Keywords arguments
        """
        self._global_filter: dict[str, Any] = {}
        super().__init__(data, **kwargs)

    @property
    def new_only(self) -> bool:
        """
        The new only flag.

        :return: True, if only new items, not already in the output database table must be processed.
        :rtype: bool
        """
        return cast(bool, self._global_filter.get('new_only', True))

    @new_only.setter
    def new_only(self, v: bool) -> None:
        self._global_filter['new_only'] = v

    def __setitem__(self, key: str, value: Filter) -> None:
        """
        Set a new value at key.

        If value is not a Filter, then it will be automatically and silently discarded.

        :param key: Dictionary key. Normally the name of the model linked to the filter.
        :type key: str
        :param value: The Filter.
        :type value: Filter
        """
        if not isinstance(value, Filter):
            return
        super().__setitem__(key, value)

    def bind_all(self, models: list[type[Model]] | dict[str, type[Model]]) -> None:
        """
        Binds all filters to their models.

        The ``models`` list or dictionary should contain a valid model for all the Filter in the registry.
        In the case of a dictionary, the key value should be the model name.

        If the user provides a model for which there is no corresponding filter in the register, then a new filter
        for that model is created using the GlobalFilter default.

        This can happen if the user did not provide a specific table for the Processor/Model, but simply put all
        filtering conditions in the GlobalFilter table. Even though, this behaviour is allowed and working,
        it may result in unexpected results. Also listing more than needed models in the input list can be dangerous
        because they will anyhow use the default filters.

        :param models: List or dictionary of a databank of Models from which the Filter can be bound.
        :type models:  list[type(Model)] | dict[str,type(Model)]
        """
        if isinstance(models, list):
            models = {m.__name__: m for m in models}

        # check, if we have a filter for each listed models, if not create one using the default configuration.
        for model_name in models.keys():
            if model_name not in self.data:
                self.data[model_name] = Filter.from_conf(f'{model_name}', conf={}, default=self._global_filter)

        for k, v in self.data.items():
            if k in self.data and k in models:
                v.bind(models[k])
            else:
                v.bind()

    def filter_all(self, join_with: str = 'AND'):  # type: ignore[no-untyped-def]
        """
        Generates a where clause joining all filters.

        If one Filter is not bound, then True is returned.

        .. versionchanged:: 1.3.0
           Add the `join_with` parameter to decide if to AND or OR all filters in the register.

        :param join_with: How to join filters ('AND' or 'OR'). Defaults to 'AND'.
        :type join_with: str
        """
        filter_list = [flt.filter() for flt in self.data.values() if flt.is_bound]
        if join_with == 'AND':
            return reduce(operator.and_, filter_list, True)
        else:
            return reduce(operator.or_, filter_list, True)
