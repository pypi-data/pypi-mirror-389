"""ABOUTME: Event generator for IonQ job status retrieval.
ABOUTME: Maps IonQ job status to Strangeworks JobStatus and creates UPDATE events."""

import json
import logging

from strangeworks_core.types import JobStatus, Resource, SDKCredentials
from strangeworks_extensions.plugins.instrumentation import Instrumentation
from strangeworks_extensions.plugins.plugin import ExtensionsPlugin
from strangeworks_extensions.plugins.serverless import local_call_handler
from strangeworks_extensions.plugins.types import (
    CallRecord,
    ClassMethodSpec,
    EventGenerator,
    RuntimeWrapper,
)
from strangeworks_extensions.types import EventPayload, EventType, ExtensionEvent
from strangeworks_extensions.types._artifact import Artifact
from strangeworks_extensions.types._services import RemoteID

logger = logging.getLogger(__name__)

QISKIT_IOONQ_PRODUCT_SLUG = "qiskit-ionq"
QISKIT_IONQ_TAGS = ["qiskit-ionq", "ionq"]
_PLUGIN_NAME = "QiskitIonQPlugin"
_CLASS_NAME = "IonQClient"
_MODULE_NAME = "qiskit_ionq.ionq_client"

# IonQ status to Strangeworks JobStatus mapping
STATUS_MAP = {
    "submitted": JobStatus.CREATED,
    "ready": JobStatus.QUEUED,
    "running": JobStatus.RUNNING,
    "canceled": JobStatus.CANCELLED,
    "completed": JobStatus.COMPLETED,
    "failed": JobStatus.FAILED,
}


def retrieve_generator(resource: Resource) -> EventGenerator:
    def _generator(fn_call: CallRecord) -> ExtensionEvent:
        """Generate an ExtensionEvent from IonQ job retrieval."""
        tags = QISKIT_IONQ_TAGS.copy()
        job_id = None
        sw_status = None
        artifacts = []

        # Extract data from return value
        if isinstance(fn_call.return_value, dict):
            remote_id = fn_call.return_value.get("id")
            if remote_id:
                job_id = RemoteID(id=remote_id)

            # Map IonQ status to Strangeworks JobStatus
            ionq_status = fn_call.return_value.get("status")
            if ionq_status:
                sw_status = STATUS_MAP.get(ionq_status)

            # Create artifact with retrieve response
            artifacts.append(
                Artifact(data=json.dumps(fn_call.return_value), name="retrieve.json")
            )

        return ExtensionEvent(
            resource_slug=resource.slug,
            product_slug=QISKIT_IOONQ_PRODUCT_SLUG,
            event_type=EventType.UPDATE,
            payload=EventPayload(
                job_id=job_id,
                sw_status=sw_status,
                tags=tags,
                artifacts=artifacts if artifacts else None,
            ),
        )

    return _generator


def retrieve_wrapper(
    gen: EventGenerator, credentials: SDKCredentials
) -> RuntimeWrapper:
    return local_call_handler(
        credentials=credentials,
        event_generator=gen,
    )


def get_extension(resource: Resource, credentials: SDKCredentials) -> ExtensionsPlugin:
    # retrieve job status
    _retrieve_spec: ClassMethodSpec = ClassMethodSpec(
        module_name=_MODULE_NAME,
        class_name=_CLASS_NAME,
        method_name="retrieve_job",
    )
    event_generator = retrieve_generator(resource=resource)
    wrapper: RuntimeWrapper = retrieve_wrapper(
        gen=event_generator, credentials=credentials
    )
    return Instrumentation(
        name="qiskit_ionq_job_retrieve_plugin",
        handler_func=wrapper,
        spec=_retrieve_spec,
    )
