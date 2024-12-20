# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

import requests
from fastapi.responses import StreamingResponse

from comps import CustomLogger, OpeaComponent, ServiceType
from comps.cores.proto.api_protocol import AudioSpeechRequest

logger = CustomLogger("opea_speecht5_tts")
logflag = os.getenv("LOGFLAG", False)


class OpeaSpeecht5Tts(OpeaComponent):
    """A specialized TTS (Text To Speech) component derived from OpeaComponent for SpeechT5 TTS services.

    Attributes:
        model_name (str): The name of the TTS model used.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.TTS.name.lower(), description, config)
        self.base_url = os.getenv("TTS_ENDPOINT", "http://localhost:7055")

    def invoke(
        self,
        request: AudioSpeechRequest,
    ) -> requests.models.Response:
        """Involve the TTS service to generate speech for the provided input."""
        # validate the request parameters
        if request.model not in ["microsoft/speecht5_tts"]:
            raise Exception("TTS model mismatch! Currently only support model: microsoft/speecht5_tts")
        if request.voice not in ["default", "male"] or request.speed != 1.0:
            logger.warning("Currently parameter 'speed' can only be 1.0 and 'voice' can only be default or male!")

        response = requests.post(f"{self.base_url}/v1/audio/speech", data=request.json())
        return response

    def check_health(self, retries=3, interval=10, timeout=5) -> bool:
        """Checks the health of the tts service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        while retries > 0:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=timeout)
                # If status is 200, the service is considered alive
                if response.status_code == 200:
                    return True
            except requests.RequestException as e:
                # Handle connection errors, timeouts, etc.
                print(f"Health check failed: {e}")
            retries -= 1
            time.sleep(interval)
        return False
