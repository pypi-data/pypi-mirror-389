"""_submit.py."""

import json
import logging

from qiskit import qasm2
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


def submit_generator(resource: Resource) -> EventGenerator:

    def _generator(fn_call: CallRecord) -> ExtensionEvent:
        """Generate an ExtensionEvent from IonQ Qiskit Job Submission."""
        tags = QISKIT_IONQ_TAGS.copy()
        job_id = None
        artifacts = []

        # Extract remote job ID from return value
        if isinstance(fn_call.return_value, dict):
            remote_id = fn_call.return_value.get("id")
            if remote_id:
                job_id = RemoteID(id=remote_id)

            # Create artifact with submission response
            artifacts.append(
                Artifact(data=json.dumps(fn_call.return_value), name="submission.json")
            )

        # Extract IonQJob from args or kwargs
        # submit_job(job) where job is an IonQJob with ._backend and .circuit attributes
        ionq_job = None
        if fn_call.args and len(fn_call.args) > 0:
            ionq_job = fn_call.args[0]
        elif fn_call.kwargs and "job" in fn_call.kwargs:
            ionq_job = fn_call.kwargs["job"]

        if ionq_job:
            # Extract device/backend name
            if hasattr(ionq_job, "_backend") and ionq_job._backend:
                backend = ionq_job._backend
                if hasattr(backend, "name") and backend.name:
                    tags.append(backend.name)

            # Create artifact with qiskit circuit
            if hasattr(ionq_job, "circuit") and ionq_job.circuit:
                try:
                    circuit_qasm = qasm2.dumps(ionq_job.circuit)
                    artifacts.append(Artifact(data=circuit_qasm, name="circuit.qasm"))
                except Exception as ex:
                    logger.warning(f"Failed to serialize circuit to QASM: {ex}")

        return ExtensionEvent(
            resource_slug=resource.slug,
            product_slug=QISKIT_IOONQ_PRODUCT_SLUG,
            event_type=EventType.CREATE,
            payload=EventPayload(
                job_id=job_id,
                sw_status=JobStatus.CREATED,
                tags=tags,
                artifacts=artifacts if artifacts else None,
            ),
        )

    return _generator


def submit_wrapper(gen: EventGenerator, credentials: SDKCredentials) -> RuntimeWrapper:
    return local_call_handler(
        credentials=credentials,
        event_generator=gen,
    )


def get_extension(resource: Resource, credentials: SDKCredentials) -> ExtensionsPlugin:
    # create job
    _submitter_spec: ClassMethodSpec = ClassMethodSpec(
        module_name=_MODULE_NAME,
        class_name=_CLASS_NAME,
        method_name="submit_job",
    )
    event_generator = submit_generator(resource=resource)
    wrapper: RuntimeWrapper = submit_wrapper(
        gen=event_generator, credentials=credentials
    )
    return Instrumentation(
        name="qiskit_ionq_job_submit_plugin", handler_func=wrapper, spec=_submitter_spec
    )
