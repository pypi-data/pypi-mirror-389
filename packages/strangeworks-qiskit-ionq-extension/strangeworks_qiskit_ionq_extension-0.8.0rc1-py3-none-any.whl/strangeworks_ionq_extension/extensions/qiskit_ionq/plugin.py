"""plugin.py."""

from strangeworks_core.types import Credentials, Resource
from strangeworks_extensions.plugins.plugin import ExtensionsPlugin
from strangeworks_extensions.plugins.types import ClassMethodSpec

from strangeworks_ionq_extension.extensions.qiskit_ionq._result import (
    get_extension as get_result_extension,
)
from strangeworks_ionq_extension.extensions.qiskit_ionq._retrieve import (
    get_extension as get_retrieve_extension,
)
from strangeworks_ionq_extension.extensions.qiskit_ionq._submit import (
    get_extension as get_submit_extension,
)

_PLUGIN_NAME = "QiskitIonQPlugin"
_CLASS_NAME = "IonQClient"
_MODULE_NAME = "qiskit_ionq.ionq_client"

# create job
_submitter_spec = ClassMethodSpec(
    module_name=_MODULE_NAME,
    class_name=_CLASS_NAME,
    method_name="submit_job",
)

_status_spec = ClassMethodSpec(
    module_name=_MODULE_NAME,
    class_name=_CLASS_NAME,
    method_name="retrieve_job",
)

_results_spec = ClassMethodSpec(
    module_name=_MODULE_NAME,
    class_name=_CLASS_NAME,
    method_name="get_results",
)


class QiskitIonQPlugin(ExtensionsPlugin):
    """Metaclass for instrumenting Qiskit-IonQ

    There are three(?) methods to instrument:
    - submit
    - status
    - result

    Also look at following:
    - cancel

    Design:
    Instrument using multiple Instrumentations. Each instrumented function/method should
    have its own Instrumentation object

    TODOs:
    - check out estimate_job method
    """

    def __init__(self, resource: Resource, credentials: Credentials):
        """Initialize Plugin Object"""
        self.submit_handler = get_submit_extension(
            resource=resource,
            credentials=credentials,
        )
        self.status_handler = get_retrieve_extension(
            resource=resource,
            credentials=credentials,
        )
        self.result_handler = get_result_extension(
            resource=resource,
            credentials=credentials,
        )
        super().__init__(name=_PLUGIN_NAME)

    def enable(self, *args, **kwargs):
        self.submit_handler.enable()
        self.status_handler.enable()
        self.result_handler.enable()

    def disable(self, *args, **kwargs):
        self.submit_handler.disable()
        self.status_handler.disable()
        self.result_handler.disable()
