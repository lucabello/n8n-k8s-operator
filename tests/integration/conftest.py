# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
import logging
from pathlib import Path

import yaml
from pytest import fixture
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@fixture(scope="module")
async def n8n_charm(ops_test: OpsTest):
    """n8n charm used for integration testing."""
    charm = await ops_test.build_charm(".")
    return charm


@fixture(scope="module")
def n8n_metadata(ops_test: OpsTest):
    return yaml.safe_load(Path("./metadata.yaml").read_text())


@fixture(scope="module")
def n8n_oci_image(ops_test: OpsTest, n8n_metadata):
    return n8n_metadata["resources"]["n8n-image"]["upstream-source"]
