"""init.py."""

import logging

from strangeworks_core.types import Resource, SDKCredentials
from strangeworks_extensions.plugins.plugin import ExtensionsPlugin

from .extensions import QiskitIonQPlugin

logger = logging.getLogger(__name__)

QISKIT_IOONQ_PRODUCT_SLUG = "qiskit-ionq"


class IonqExtension(ExtensionsPlugin):
    # TODO: see if we can also do cirq from here too.
    def __init__(self, resource: Resource, credentials: SDKCredentials):
        logger.debug("initializing IonqExtension object")
        self.qiskit_plugin: QiskitIonQPlugin = QiskitIonQPlugin(
            resource=resource,
            credentials=credentials,
        )

    def enable(self, *args, **kwargs):
        logger.debug("enabling qiskit-ionq extension")
        self.qiskit_plugin.enable()

    def disable(self, *args, **kwargs):
        logger.debug("disabling qiskit-ionq extension")
        self.qiskit_plugin.disable()


def setup(resource: Resource, credentials: SDKCredentials):
    logging.debug("starting qiskit-ionq extension setup")
    return IonqExtension(resource=resource, credentials=credentials)
