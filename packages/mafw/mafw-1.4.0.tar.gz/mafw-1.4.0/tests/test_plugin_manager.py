#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Test suite for the mafw plugin manager module.

This module validates the behavior of the plugin management system based on
the Pluggy framework. It ensures that plugins and hook specifications are
correctly registered and invoked, and that the manager behaves as a singleton
unless explicitly recreated.

Test coverage includes:
- Plugin manager instantiation and recreation
- Hook specification and implementation registration
- Hook invocation and expected return structure
"""

import pluggy
import pytest

from mafw import plugin_manager, plugins


class TestPluginManagerLifecycle:
    """
    Tests related to the lifecycle and internal state of the plugin manager.
    These tests verify that the plugin manager behaves like a singleton unless
    forced to recreate and that the correct components are registered.
    """

    def test_singleton_behavior(self):
        """
        Test that the plugin manager returns the same instance by default.

        Ensures:
            - No duplication of plugin managers when `force_recreate` is False
        """
        pm1 = plugin_manager.get_plugin_manager()
        pm2 = plugin_manager.get_plugin_manager()
        assert pm1 is pm2

    def test_force_recreate(self):
        """
        Test that the plugin manager can be recreated with `force_recreate=True`.

        Ensures:
            - A new plugin manager instance is created when explicitly requested
        """
        pm1 = plugin_manager.get_plugin_manager()
        pm2 = plugin_manager.get_plugin_manager(force_recreate=True)
        assert pm1 is not pm2

    def test_plugin_manager_type(self):
        """
        Test that the plugin manager is an instance of `pluggy.PluginManager`.

        Ensures:
            - The returned object is correctly typed
            - The manager has the expected project name
        """
        pm = plugin_manager.get_plugin_manager(force_recreate=True)
        assert isinstance(pm, pluggy.PluginManager)
        assert pm.project_name == 'mafw'

    def test_hookspecs_registered(self):
        """
        Test that all expected hook specifications are registered with the plugin manager.

        Ensures:
            - Hooks defined in `hookspecs` are recognized by the plugin manager
        """
        pm = plugin_manager.get_plugin_manager(force_recreate=True)
        hook_names = pm.hook.__dir__()
        expected_hooks = ['register_processors', 'register_user_interfaces', 'register_standard_tables']
        for name in expected_hooks:
            assert name in hook_names

    def test_plugins_registered(self):
        """
        Test that the `plugins` module is registered as a plugin implementation.

        Ensures:
            - At least one of the registered plugins is the `plugins` module
        """
        pm = plugin_manager.get_plugin_manager(force_recreate=True)
        assert any(p is plugins for p in pm.get_plugins())


class TestPluginHookCalls:
    """
    Tests for validating hook call results from registered plugins.

    These tests verify:
    - That hook return types conform to expectations
    - That the results contain a minimum number of items
    """

    @pytest.mark.parametrize(
        'hook_name, expected_type, min_expected_len',
        [
            ('register_processors', object, 5),
            ('register_user_interfaces', object, 1),
            ('register_standard_tables', object, 0),
        ],
    )
    def test_hooks_return_expected_results(self, hook_name, expected_type, min_expected_len):
        """
        Test that hook calls return valid lists of expected types.

        Parameters:
            hook_name (str): Name of the hook to invoke
            expected_type (type): Expected base type of items in the result
            min_expected_len (int): Minimum length of the flattened result list

        Ensures:
            - Hooks return a list of types (e.g., processor classes or interfaces)
            - Results meet expected length thresholds
        """
        pm = plugin_manager.get_plugin_manager(force_recreate=True)
        hook = getattr(pm.hook, hook_name)
        results = hook()
        # flatten list of lists
        flat_results = [item for sublist in results for item in sublist]
        assert isinstance(flat_results, list)
        assert all(isinstance(p, type) for p in flat_results)
        assert len(flat_results) >= min_expected_len
