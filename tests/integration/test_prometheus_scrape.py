#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio

import pytest
import requests
from pytest_operator.plugin import OpsTest
from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential as wexp

PROMETHEUS = "prometheus-k8s"
N8N = "n8n-k8s"


@pytest.mark.abort_on_fail
async def test_prometheus_k8s(ops_test: OpsTest, n8n_charm, n8n_oci_image):
    """Test that n8n can be related with Prometheus to scrape its metrics."""
    apps = [N8N, PROMETHEUS]

    await asyncio.gather(
        ops_test.model.deploy(
            await n8n_charm,
            application_name=N8N,
            resources={"n8n-image": n8n_oci_image},
            trust=True,
        ),
        ops_test.model.deploy(
            PROMETHEUS,
            application_name=PROMETHEUS,
            channel="candidate",
            trust=True,
        ),
        ops_test.model.wait_for_idle(apps=apps, status="active", timeout=1000),
    )

    # Create the relation
    await ops_test.model.add_relation(N8N, PROMETHEUS)
    # Wait for the two apps to quiesce
    await ops_test.model.wait_for_idle(apps=apps, status="active", timeout=1000)

    # Check if n8n is in Prometheus' targets
    address = await _get_address(ops_test, PROMETHEUS)
    r = requests.get(f"http://{address}:9090/api/v1/targets")
    scraped_applications = [
        target["labels"]["juju_application"] for target in r.json()["data"]["activeTargets"]
    ]
    assert N8N in scraped_applications


@pytest.mark.abort_on_fail
@retry(wait=wexp(multiplier=2, min=1, max=30), stop=stop_after_attempt(10), reraise=True)
async def test_prometheus_scrapes_correctly(ops_test: OpsTest):
    """Test that the up metric from scraping n8n eventually appears in Prometheus."""
    address = await _get_address(ops_test, PROMETHEUS)
    r = requests.get(f"http://{address}:9090/api/v1/query?query=up")
    up_applications = [app["metric"]["juju_application"] for app in r.json()["data"]["result"]]
    assert N8N in up_applications


async def _get_address(ops_test: OpsTest, application_name) -> str:
    """Utility function to get the Prometheus IP address."""
    status = await ops_test.model.get_status()
    unit = list(status.applications[application_name].units)[0]
    address = status["applications"][application_name]["units"][unit]["address"]
    return address
