# -*- coding: utf-8 -*-
"""
Proxmox VE Hypervisor - FortiSOAR native connector.
Proxmox VE REST API with token authentication.
"""

from connectors.core.connector import Connector, get_logger, ConnectorError
from .operations import operations, _check_health

logger = get_logger("Proxmox VE Hypervisor")


class ProxmoxApiConnector(Connector):

    def execute(self, config, operation_name, params, **kwargs):
        try:
            op = operations.get(operation_name)
            if not op:
                raise ConnectorError("Unknown operation: {}".format(operation_name))
            if not isinstance(params, dict):
                params = {}
            result = op(config, params)
            return result
        except ConnectorError:
            raise
        except Exception as e:
            logger.exception("Operation {} failed: {}".format(operation_name, str(e)))
            raise ConnectorError(str(e))

    def check_health(self, config):
        try:
            _check_health(config)
            return True
        except Exception as e:
            logger.exception("check_health failed: {}".format(str(e)))
            raise ConnectorError(str(e))
