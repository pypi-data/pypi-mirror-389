#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Unit tests for the rich_user_interface module.

This module contains comprehensive tests for the RichInterface class,
ensuring good coverage of all methods and edge cases.
"""

from unittest.mock import Mock, patch

import pytest
from rich.progress import Progress, TaskID

from mafw.enumerators import ProcessorStatus
from mafw.ui.rich_user_interface import RichInterface


class TestRichInterfaceInitialization:
    """Test class for RichInterface initialization and setup."""

    def test_default_initialization(self):
        """Test RichInterface initialization with default parameters."""
        interface = RichInterface()

        assert interface.name == 'rich'
        assert isinstance(interface.progress, Progress)
        assert isinstance(interface.task_dict, dict)
        assert len(interface.task_dict) == 0

    def test_initialization_with_custom_progress_kws(self):
        """Test RichInterface initialization with custom progress keywords."""
        custom_kws = {'auto_refresh': False, 'expand': False, 'refresh_per_second': 5}

        with patch('mafw.ui.rich_user_interface.Progress') as mock_progress:
            RichInterface(progress_kws=custom_kws)

            # Verify Progress was called with custom keywords
            mock_progress.assert_called_once()
            call_args = mock_progress.call_args
            assert 'auto_refresh' in call_args.kwargs
            assert call_args.kwargs['auto_refresh'] is False
            assert call_args.kwargs['expand'] is False
            assert call_args.kwargs['refresh_per_second'] == 5

    def test_initialization_with_none_progress_kws(self):
        """Test RichInterface initialization when progress_kws is explicitly None."""
        with patch('mafw.ui.rich_user_interface.Progress') as mock_progress:
            RichInterface(progress_kws=None)

            # Should use default kwargs
            call_args = mock_progress.call_args
            assert 'auto_refresh' in call_args.kwargs
            assert call_args.kwargs['auto_refresh'] is True
            assert call_args.kwargs['expand'] is True


class TestRichInterfaceContextManager:
    """Test class for RichInterface context manager functionality."""

    def test_context_manager_enter(self):
        """Test __enter__ method starts progress and returns self."""
        interface = RichInterface()
        interface.progress = Mock()

        result = interface.__enter__()

        interface.progress.start.assert_called_once()
        assert result is interface

    def test_context_manager_exit(self):
        """Test __exit__ method stops progress."""
        interface = RichInterface()
        interface.progress = Mock()

        interface.__exit__(None, None, None)

        interface.progress.stop.assert_called_once()

    @pytest.mark.parametrize(
        'exception_type,exception_value,traceback',
        [
            (ValueError, ValueError('test error'), None),
            (RuntimeError, RuntimeError('runtime error'), Mock()),
            (None, None, None),
        ],
    )
    def test_context_manager_exit_with_exceptions(self, exception_type, exception_value, traceback):
        """Test __exit__ method with various exception scenarios."""
        interface = RichInterface()
        interface.progress = Mock()

        interface.__exit__(exception_type, exception_value, traceback)

        interface.progress.stop.assert_called_once()

    def test_context_manager_full_flow(self):
        """Test complete context manager flow."""
        interface = RichInterface()
        interface.progress = Mock()

        with interface as ctx:
            assert ctx is interface
            interface.progress.start.assert_called_once()

        interface.progress.stop.assert_called_once()


class TestRichInterfaceTaskManagement:
    """Test class for RichInterface task creation and updates."""

    def test_create_task_basic(self):
        """Test basic task creation."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id = TaskID(1)
        interface.progress.add_task.return_value = mock_task_id

        interface.create_task('test_task', 'Test Description')

        interface.progress.add_task.assert_called_once_with('Test Description', total=None, completed=0, increment=None)
        assert interface.task_dict['test_task'] == mock_task_id

    @pytest.mark.parametrize(
        'task_name,task_description,completed,increment,total',
        [
            ('task1', 'Description 1', 0, None, None),
            ('task2', 'Description 2', 10, 5, 100),
            ('task3', '', 25, None, 50),
            ('task4', 'Long description with details', 0, 1, None),
        ],
    )
    def test_create_task_with_parameters(self, task_name, task_description, completed, increment, total):
        """Test task creation with various parameter combinations."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id = TaskID(1)
        interface.progress.add_task.return_value = mock_task_id

        interface.create_task(task_name, task_description, completed, increment, total)

        interface.progress.add_task.assert_called_once_with(
            task_description, total=total, completed=completed, increment=increment
        )
        assert interface.task_dict[task_name] == mock_task_id

    def test_create_task_with_kwargs(self):
        """Test task creation with additional keyword arguments."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id = TaskID(1)
        interface.progress.add_task.return_value = mock_task_id

        interface.create_task('test_task', 'Test Description', custom_arg='value', another_arg=42)

        # Should still work even with extra kwargs (they're ignored)
        interface.progress.add_task.assert_called_once_with('Test Description', total=None, completed=0, increment=None)

    @patch('mafw.ui.rich_user_interface.log')
    def test_create_task_duplicate_name_warning(self, mock_log):
        """Test warning when creating task with duplicate name."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id1 = TaskID(1)
        mock_task_id2 = TaskID(2)
        interface.progress.add_task.side_effect = [mock_task_id1, mock_task_id2]

        # Create first task
        interface.create_task('duplicate_task', 'First Description')

        # Create second task with same name
        interface.create_task('duplicate_task', 'Second Description')

        # Check warnings were logged
        assert mock_log.warning.call_count == 2
        mock_log.warning.assert_any_call(
            'A task with this name (%s) already exists. Replacing it with the new one.' % 'duplicate_task'
        )
        mock_log.warning.assert_any_call('Be sure to use unique names.')

        # Check task was replaced
        assert interface.task_dict['duplicate_task'] == mock_task_id2

    def test_update_task_basic(self):
        """Test basic task update."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id = TaskID(1)
        interface.task_dict['existing_task'] = mock_task_id

        interface.update_task('existing_task', completed=50)

        interface.progress.update.assert_called_once_with(
            mock_task_id,
            completed=50,
            advance=None,
            total=None,
            visible=True,  # completed != total (None)
        )

    @pytest.mark.parametrize(
        'completed,increment,total,expected_visible',
        [
            (0, None, None, True),
            (50, 10, 100, True),
            (100, None, 100, False),  # completed == total
            (0, 5, 10, True),
            (10, None, 10, False),  # completed == total
        ],
    )
    def test_update_task_visibility(self, completed, increment, total, expected_visible):
        """Test task update visibility based on completion status."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id = TaskID(1)
        interface.task_dict['test_task'] = mock_task_id

        interface.update_task('test_task', completed=completed, increment=increment, total=total)

        interface.progress.update.assert_called_once_with(
            mock_task_id, completed=completed, advance=increment, total=total, visible=expected_visible
        )

    @patch('mafw.ui.rich_user_interface.log')
    def test_update_task_nonexistent(self, mock_log):
        """Test updating a non-existent task logs warning and returns early."""
        interface = RichInterface()
        interface.progress = Mock()

        interface.update_task('nonexistent_task', completed=50)

        # Check warnings were logged
        assert mock_log.warning.call_count == 2
        mock_log.warning.assert_any_call('A task with this name (%s) does not exist.' % 'nonexistent_task')
        mock_log.warning.assert_any_call('Skipping updates')

        # Check progress.update was not called
        interface.progress.update.assert_not_called()

    def test_update_task_with_kwargs(self):
        """Test task update with additional keyword arguments."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id = TaskID(1)
        interface.task_dict['test_task'] = mock_task_id

        interface.update_task('test_task', completed=25, increment=5, total=100, extra_arg='ignored')

        interface.progress.update.assert_called_once_with(
            mock_task_id, completed=25, advance=5, total=100, visible=True
        )


class TestRichInterfaceProgressMessages:
    """Test class for RichInterface progress message display."""

    @patch('mafw.ui.rich_user_interface.log')
    def test_display_progress_message_with_n_item(self, mock_log):
        """Test progress message display with known total items."""
        interface = RichInterface()

        # Mock the _is_time_to_display_lopping_message method to always return True
        interface._is_time_to_display_lopping_message = Mock(return_value=True)

        interface.display_progress_message('Processing item', 4, 100, 0.1)

        # Check that log.info was called with properly formatted message
        expected_message = '[  5/100] Processing item'
        mock_log.info.assert_called_once_with(expected_message)

    @patch('mafw.ui.rich_user_interface.log')
    def test_display_progress_message_without_n_item(self, mock_log):
        """Test progress message display without known total items."""
        interface = RichInterface()
        interface._is_time_to_display_lopping_message = Mock(return_value=True)

        interface.display_progress_message('Processing item', 4, None, 0.1)

        expected_message = '[   5/1000] Processing item'
        mock_log.info.assert_called_once_with(expected_message)

    @patch('mafw.ui.rich_user_interface.log')
    def test_display_progress_message_large_i_item(self, mock_log):
        """Test progress message display with large i_item value."""
        interface = RichInterface()
        interface._is_time_to_display_lopping_message = Mock(return_value=True)

        interface.display_progress_message('Processing item', 1500, None, 0.1)

        # When i_item > 1000, n_item should be i_item
        expected_message = '[1501/1500] Processing item'
        mock_log.info.assert_called_once_with(expected_message)

    @patch('mafw.ui.rich_user_interface.log')
    def test_display_progress_message_not_time_to_display(self, mock_log):
        """Test progress message when it's not time to display."""
        interface = RichInterface()
        interface._is_time_to_display_lopping_message = Mock(return_value=False)

        interface.display_progress_message('Processing item', 4, 100, 0.1)

        # Should not log anything
        mock_log.info.assert_not_called()

    @patch('mafw.ui.rich_user_interface.log')
    @pytest.mark.parametrize(
        'i_item,n_item,expected_width,expected_counter',
        [
            (0, 10, 2, '[ 1/10] '),
            (9, 100, 3, '[ 10/100] '),
            (99, 1000, 4, '[ 100/1000] '),
            (1999, 10000, 5, '[ 2000/10000] '),
        ],
    )
    def test_display_progress_message_formatting(self, mock_log, i_item, n_item, expected_width, expected_counter):
        """Test progress message formatting with different widths."""
        interface = RichInterface()
        interface._is_time_to_display_lopping_message = Mock(return_value=True)

        interface.display_progress_message('Test message', i_item, n_item, 0.1)

        expected_message = expected_counter + 'Test message'
        mock_log.info.assert_called_once_with(expected_message)


class TestRichInterfaceStatusChanges:
    """Test class for RichInterface processor status changes."""

    @patch('mafw.ui.rich_user_interface.log')
    @pytest.mark.parametrize(
        'processor_name,old_status,new_status',
        [
            ('processor1', ProcessorStatus.Unknown, ProcessorStatus.Init),
            ('processor2', ProcessorStatus.Init, ProcessorStatus.Run),
            ('processor3', ProcessorStatus.Run, ProcessorStatus.Finish),
            ('long_processor_name', ProcessorStatus.Finish, ProcessorStatus.Unknown),
        ],
    )
    def test_change_of_processor_status(self, mock_log, processor_name, old_status, new_status):
        """Test processor status change logging."""
        interface = RichInterface()

        interface.change_of_processor_status(processor_name, old_status, new_status)

        expected_message = f'[red]{processor_name}[/red] is [bold]{new_status}[/bold]'
        mock_log.debug.assert_called_once_with(expected_message)

    @patch('mafw.ui.rich_user_interface.log')
    def test_change_of_processor_status_with_special_characters(self, mock_log):
        """Test processor status change with special characters in name."""
        interface = RichInterface()
        processor_name = 'processor-with-dashes_and_underscores.123'

        interface.change_of_processor_status(processor_name, ProcessorStatus.Init, ProcessorStatus.Run)

        expected_message = f'[red]{processor_name}[/red] is [bold]{ProcessorStatus.Run}[/bold]'
        mock_log.debug.assert_called_once_with(expected_message)


@pytest.mark.integration_test
class TestRichInterfaceIntegration:
    """Integration tests for RichInterface."""

    def test_complete_workflow(self):
        """Test a complete workflow with task creation, updates, and status changes."""
        interface = RichInterface()
        interface.progress = Mock()
        mock_task_id = TaskID(1)
        interface.progress.add_task.return_value = mock_task_id

        # Test context manager
        with interface:
            # Create task
            interface.create_task('workflow_task', 'Processing workflow', total=100)

            # Update task multiple times
            interface.update_task('workflow_task', completed=25)
            interface.update_task('workflow_task', completed=50)
            interface.update_task('workflow_task', completed=100)

            # Test status change
            interface.change_of_processor_status('test_processor', ProcessorStatus.Unknown, ProcessorStatus.Init)

        # Verify all calls
        interface.progress.start.assert_called_once()
        interface.progress.add_task.assert_called_once()
        assert interface.progress.update.call_count == 3
        interface.progress.stop.assert_called_once()

    @patch('mafw.ui.rich_user_interface.log')
    def test_multiple_tasks_management(self, mock_log):
        """Test managing multiple tasks simultaneously."""
        interface = RichInterface()
        interface.progress = Mock()
        interface.progress.add_task.side_effect = [TaskID(1), TaskID(2), TaskID(3)]

        # Create multiple tasks
        tasks = [
            ('task1', 'First task', 0, None, 100),
            ('task2', 'Second task', 10, 5, 200),
            ('task3', 'Third task', 25, None, 50),
        ]

        for task_name, description, completed, increment, total in tasks:
            interface.create_task(task_name, description, completed, increment, total)

        # Update all tasks
        interface.update_task('task1', completed=50)
        interface.update_task('task2', completed=75, increment=10)
        interface.update_task('task3', completed=50, total=50)  # This should be invisible

        # Verify all tasks were created and updated
        assert len(interface.task_dict) == 3
        assert interface.progress.add_task.call_count == 3
        assert interface.progress.update.call_count == 3

        # Check the last update call for task3 (should be invisible)
        last_call = interface.progress.update.call_args_list[-1]
        assert last_call.kwargs['visible'] is False

    def test_inheritance_from_base_class(self):
        """Test that RichInterface properly inherits from UserInterfaceBase."""
        from mafw.ui.abstract_user_interface import UserInterfaceBase

        interface = RichInterface()
        assert isinstance(interface, UserInterfaceBase)

        # Test that all required methods are implemented
        required_methods = ['create_task', 'update_task', 'display_progress_message', 'change_of_processor_status']
        for method_name in required_methods:
            assert hasattr(interface, method_name)
            assert callable(getattr(interface, method_name))

    def test_progress_message_integration_with_base_class(self):
        """Test that progress message display integrates with base class logic."""
        interface = RichInterface()

        # Test that the base class method is used for determining when to display
        with patch.object(interface, '_is_time_to_display_lopping_message', return_value=True) as mock_method:
            with patch('mafw.ui.rich_user_interface.log') as mock_log:
                interface.display_progress_message('Test', 5, 100, 0.1)

                mock_method.assert_called_once_with(5, 100, 0.1)
                mock_log.info.assert_called_once()
