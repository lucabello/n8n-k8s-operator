#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import asyncio

import requests
from pytest import mark
from pytest_operator.plugin import OpsTest
from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential as wexp

N8N = "n8n-k8s"


@mark.abort_on_fail
async def test_deploy(ops_test: OpsTest, n8n_charm, n8n_oci_image):
    await asyncio.gather(
        ops_test.model.deploy(
            await n8n_charm,
            application_name=N8N,
            resources={"n8n-image": n8n_oci_image},
            trust=True,
            config={"disable-authentication": True},
        ),
        ops_test.model.wait_for_idle(apps=[N8N], status="active", timeout=1000),
    )


@mark.abort_on_fail
@retry(wait=wexp(multiplier=2, min=1, max=30), stop=stop_after_attempt(10), reraise=True)
async def test_application_is_up(ops_test: OpsTest):
    status = await ops_test.model.get_status()
    unit = list(status.applications[N8N].units)[0]
    address = status["applications"][N8N]["units"][unit]["address"]
    response = requests.get(f"http://{address}:5678/api/v1/docs/")
    return response.status_code == 200
