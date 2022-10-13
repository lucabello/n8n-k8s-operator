#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import re

import pytest
import requests

INGRESS = "nginx-ingress-integrator"
N8N = "n8n-k8s"

EXTERNAL_HOSTNAME = "n8n.juju"


@pytest.mark.abort_on_fail
async def test_ingress_k8s(ops_test, n8n_charm, n8n_oci_image):
    """Test that n8n can be related with Nginx Ingress Integrator for ingress."""
    apps = [N8N, INGRESS]

    await asyncio.gather(
        ops_test.model.deploy(
            await n8n_charm,
            application_name=N8N,
            resources={"n8n-image": n8n_oci_image},
            trust=True,
            config={"external-hostname": EXTERNAL_HOSTNAME},
        ),
        ops_test.model.deploy(
            INGRESS,
            application_name=INGRESS,
            trust=True,
        ),
        ops_test.model.wait_for_idle(apps=apps, status="active", timeout=1000),
    )

    # Create the relation
    await ops_test.model.add_relation(N8N, INGRESS)
    # Wait for the two apps to quiesce
    await ops_test.model.wait_for_idle(apps=apps, status="active", timeout=1000)

    result = await _retrieve_proxied_endpoints(ops_test, INGRESS)
    # assert result.get(N8N, None) == {"url": f"http://{EXTERNAL_HOSTNAME}:80/"}
    assert EXTERNAL_HOSTNAME in result


@pytest.mark.abort_on_fail
async def test_ingress_functions_correctly(ops_test):
    """Test that the ingress functionality is working correctly."""
    r = requests.get(
        "http://127.0.0.1:80/api/v1/docs/",
        headers={"Host": f"{EXTERNAL_HOSTNAME}"},
    )

    assert r.status_code == 200


async def _retrieve_proxied_endpoints(ops_test, ingress_application_name):
    """Utility function to retrieve n8n's external hostname from ingress."""
    ingress_application = ops_test.model.applications[ingress_application_name]
    ingress_first_unit = next(iter(ingress_application.units))
    action = await ingress_first_unit.run_action("describe-ingresses")
    await action.wait()
    result = await ops_test.model.get_action_output(action.id)

    pattern = re.compile(r"'host': '(?P<ingress>.*?)'")
    matches = re.findall(pattern, result["ingresses"])

    return matches
