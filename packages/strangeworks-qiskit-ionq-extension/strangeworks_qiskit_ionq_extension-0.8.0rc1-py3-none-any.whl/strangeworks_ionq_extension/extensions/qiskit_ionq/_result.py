"""ABOUTME: Event generator for IonQ job result retrieval.
ABOUTME: Extracts job_id from results URL and creates RESULTS events with result artifacts."""

import json
import logging
import re

from strangeworks_core.types import Resource, SDKCredentials
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

# Regex pattern to extract job_id from results URL
# Matches patterns like: /v0.4/jobs/{job_id}/results/probabilities
# Also handles: /jobs/{job_id}/results/... and full URLs
JOB_ID_PATTERN = re.compile(r"/jobs/([^/]+)/results")


def _extract_job_id_from_url(results_url: str) -> str | None:
    """Extract job_id from results URL.

    Args:
        results_url: The results URL, e.g. /v0.4/jobs/{job_id}/results/probabilities

    Returns:
        The extracted job_id or None if not found
    """
    match = JOB_ID_PATTERN.search(results_url)
    if match:
        return match.group(1)
    return None


def result_generator(resource: Resource) -> EventGenerator:
    def _generator(fn_call: CallRecord) -> ExtensionEvent:
        """Generate an ExtensionEvent from IonQ job result retrieval."""
        tags = QISKIT_IONQ_TAGS.copy()
        job_id = None
        artifacts = []

        # Extract results_url from args or kwargs
        results_url = None
        if fn_call.args and len(fn_call.args) > 0:
            results_url = fn_call.args[0]
        elif fn_call.kwargs and "results_url" in fn_call.kwargs:
            results_url = fn_call.kwargs["results_url"]

        # Extract job_id from results_url
        if results_url:
            job_id_str = _extract_job_id_from_url(results_url)
            if job_id_str:
                job_id = RemoteID(id=job_id_str)

        # Create artifact with result data if return value is a dict
        if isinstance(fn_call.return_value, dict):
            artifacts.append(
                Artifact(data=json.dumps(fn_call.return_value), name="result.json")
            )

        return ExtensionEvent(
            resource_slug=resource.slug,
            product_slug=QISKIT_IOONQ_PRODUCT_SLUG,
            event_type=EventType.RESULTS,
            payload=EventPayload(
                job_id=job_id,
                sw_status=None,  # Do not update status
                tags=tags,
                artifacts=artifacts if artifacts else None,
            ),
        )

    return _generator


def result_wrapper(gen: EventGenerator, credentials: SDKCredentials) -> RuntimeWrapper:
    return local_call_handler(
        credentials=credentials,
        event_generator=gen,
    )


def get_extension(resource: Resource, credentials: SDKCredentials) -> ExtensionsPlugin:
    # retrieve job results
    _result_spec: ClassMethodSpec = ClassMethodSpec(
        module_name=_MODULE_NAME,
        class_name=_CLASS_NAME,
        method_name="get_results",
    )
    event_generator = result_generator(resource=resource)
    wrapper: RuntimeWrapper = result_wrapper(
        gen=event_generator, credentials=credentials
    )
    return Instrumentation(
        name="qiskit_ionq_job_result_plugin", handler_func=wrapper, spec=_result_spec
    )
