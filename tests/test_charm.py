# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from ops.model import ActiveStatus
from ops.testing import Harness

from charm import N8nCharm

# from unittest.mock import Mock


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(N8nCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed(self):
        self.assertEqual(self.harness.charm._external_hostname, self.harness.charm.app.name)
        self.harness.update_config({"external-hostname": "n8n.juju"})
        self.assertEqual(self.harness.charm._external_hostname, "n8n.juju")

    def test_n8n_pebble_ready(self):
        # Simulate making the Pebble socket available
        self.harness.set_can_connect("n8n", True)
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("n8n")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Expected plan after Pebble ready with default config
        expected_plan = {
            "services": {
                "n8n": {
                    "override": "replace",
                    "summary": "n8n",
                    "command": "n8n",
                    "startup": "enabled",
                    "environment": {"N8N_USER_FOLDER": "/home/node", "N8N_METRICS": True},
                }
            },
        }
        # Get the n8n container from the model
        container = self.harness.model.unit.get_container("n8n")
        # Emit the PebbleReadyEvent carrying the n8n container
        self.harness.charm.on.n8n_pebble_ready.emit(container)
        # Get the plan now we've run PebbleReady
        updated_plan = self.harness.get_container_pebble_plan("n8n").to_dict()
        # Check we've got the plan we expected
        self.assertEqual(expected_plan, updated_plan)
        # Check the service was started
        service = self.harness.model.unit.get_container("n8n").get_service("n8n")
        self.assertTrue(service.is_running())
        # Ensure we set an ActiveStatus with no message
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
