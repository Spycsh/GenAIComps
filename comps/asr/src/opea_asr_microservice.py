# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import List

from fastapi import File, Form, UploadFile
from integrations.opea_whisper import OpeaWhisperAsr

from comps import (
    Base64ByteStrDoc,
    CustomLogger,
    LLMParamsDoc,
    OpeaComponentController,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import AudioTranscriptionResponse

logger = CustomLogger("opea_asr_microservice")
logflag = os.getenv("LOGFLAG", False)

# Initialize OpeaComponentController
controller = OpeaComponentController()

# Register components
try:
    # Instantiate ASR components
    opea_whisper = OpeaWhisperAsr(
        name="OpeaWhisperAsr",
        description="OPEA Whisper ASR Service",
    )

    # Register components with the controller
    controller.register(opea_whisper)

    # Discover and activate a healthy component
    controller.discover_and_activate(retries=10, interval=10, timeout=5)
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")


@register_microservice(
    name="opea_service@asr",
    service_type=ServiceType.ASR,
    endpoint="/v1/audio/transcriptions",
    host="0.0.0.0",
    port=9099,
    input_datatype=Base64ByteStrDoc,
    output_datatype=LLMParamsDoc,
)
@register_statistics(names=["opea_service@asr"])
async def audio_to_text(
    file: UploadFile = File(...),  # Handling the uploaded file directly
    model: str = Form("openai/whisper-small"),
    language: str = Form("english"),
    prompt: str = Form(None),
    response_format: str = Form("json"),
    temperature: float = Form(0),
    timestamp_granularities: List[str] = Form(None),
) -> AudioTranscriptionResponse:
    start = time.time()

    if logflag:
        logger.info("ASR file uploaded.")

    try:
        # Use the controller to invoke the active component
        asr_response = await controller.invoke(
            file=file,
            model=model,
            language=language,
            prompt=prompt,
            response_format=response_format,
            temperature=temperature,
            timestamp_granularities=timestamp_granularities,
        )
        if logflag:
            logger.info(asr_response)
        statistics_dict["opea_service@asr"].append_latency(time.time() - start, None)
        return asr_response

    except Exception as e:
        logger.error(f"Error during asr invocation: {e}")
        raise


if __name__ == "__main__":
    logger.info("OPEA ASR Microservice is starting....")
    opea_microservices["opea_service@asr"].start()
