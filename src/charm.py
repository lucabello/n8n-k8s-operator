#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from ops.charm import CharmBase, WorkloadEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class N8nCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.n8n_pebble_ready, self._on_n8n_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        # Integration for the ingress relation
        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": self._external_hostname,
                "service-name": self.app.name,
                "service-port": 5678,
            },
        )
        # Integration for the prometheus relation
        jobs = [{"static_configs": [{"targets": ["*:5678"]}]}]
        self.monitoring = MetricsEndpointProvider(self, jobs=jobs)

    def _on_n8n_pebble_ready(self, event: WorkloadEvent):
        """Define and start a workload using the Pebble API."""
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("n8n", self._n8n_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()

        self.unit.status = ActiveStatus()

    def _on_config_changed(self, _):
        """Handle the config-changed event."""
        # Get the n8n container to configure/manipulate it
        container = self.unit.get_container("n8n")
        # Create a new config layer
        layer = self._n8n_layer.to_dict()

        if container.can_connect():
            # Get the current config
            services = container.get_plan().to_dict().get("services", {})
            # Check if there are nayy changes to services
            if services != layer["services"]:
                container.add_layer("n8n", layer, combine=True)
                logging.info("Added updated layer 'n8n' to Pebble plan")
                container.restart("n8n")
                logging.info("Restarted n8n service")
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

        self.ingress.update_config({"service-hostname": self._external_hostname})

    @property
    def _external_hostname(self) -> str:
        """Return the external hostname to be passed to ingress via the relation."""
        return self.config["external-hostname"] or self.app.name

    @property
    def _disable_authentication(self) -> bool:
        """Return the flag for disabling user management."""
        return self.config["disable-authentication"]

    @property
    def _n8n_layer(self) -> Layer:
        return Layer(
            {
                "summary": "n8n layer",
                "description": "pebble config layer for n8n",
                "services": {
                    "n8n": {
                        "override": "replace",
                        "summary": "n8n",
                        "command": "n8n",
                        "startup": "enabled",
                        "environment": {
                            "N8N_USER_FOLDER": "/home/node",
                            "N8N_METRICS": True,
                            "N8N_USER_MANAGEMENT_DISABLED": self._disable_authentication,
                        },
                    }
                },
            }
        )


if __name__ == "__main__":
    main(N8nCharm)
