"""Test data for vendor workflow e2e tests."""

import json
import pytest
from codemie_sdk.models.vendor_assistant import VendorType
from codemie_sdk.models.integration import CredentialTypes

from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager


vendor_workflow_test_data = [
    pytest.param(
        VendorType.AWS,
        CredentialTypes.AWS,
        CredentialsManager.aws_credentials(),
        "codemie-autotests-flow-object-input",
        json.dumps({"genre": "pop", "number": 3}),
        """
            # Pop Playlist: Just Three Hits

            1. "As It Was" by Harry Styles
            2. "Blinding Lights" by The Weeknd
            3. "Levitating" by Dua Lipa

            These three modern pop classics offer a perfect mini-playlist with upbeat tempos and catchy hooks. Enjoy!
        """,
        marks=[pytest.mark.aws, pytest.mark.bedrock],
        id="AWS_Bedrock_Object_Input",
    ),
    # pytest.param(
    #     VendorType.AZURE,
    #     CredentialTypes.AZURE,
    #     CredentialsManager.azure_credentials(),
    #     "workflow-name",
    #     json.dumps({"genre": "rock", "number": 5}),
    #     "Rock Playlist",
    #     marks=[pytest.mark.azure],
    #     id="Azure_AI_Object_Input",
    # ),
    # pytest.param(
    #     VendorType.GCP,
    #     CredentialTypes.GCP,
    #     CredentialsManager.gcp_credentials(),
    #     "workflow-name",
    #     json.dumps({"genre": "jazz", "number": 4}),
    #     "Jazz Playlist",
    #     marks=[pytest.mark.gcp],
    #     id="GCP_Vertex_AI_Object_Input",
    # ),
]
