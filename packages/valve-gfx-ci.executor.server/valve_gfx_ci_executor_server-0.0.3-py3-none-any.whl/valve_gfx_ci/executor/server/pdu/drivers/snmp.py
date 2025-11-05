from easysnmp import Session
import easysnmp.exceptions
from .. import logger, PDU, PDUPort, PDUPortState, PDUPortFullState, PDUSimpleNetworkProbeMixin
from functools import cached_property

import random
import time


def _is_int(s):
    try:
        s = int(s)
        return True
    except ValueError:
        return False


def retry_on_known_errors(func):
    def retry(*args, **kwargs):
        retries = 3

        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except (SystemError, easysnmp.exceptions.EasySNMPError) as e:
                logger.warning(f"Caught the error '{str(e)}', retrying ({i+1}/{retries})")
                # Wait 1 second, plus a random [0,1] second delay to reduce the chances of concurrent requests
                time.sleep(1 + random.random())
                continue

        raise ValueError(f"The function {func} failed {retries} times in a row")

    return retry


class SnmpPDU(PDU, PDUSimpleNetworkProbeMixin):
    @retry_on_known_errors
    def _refresh_port_labels(self):
        try:
            self._port_labels_cached = self.session.walk(self.outlet_labels_oid)
            return self._port_labels_cached
        except SystemError as e:
            raise ValueError(f"The snmp_walk() call failed with the following error: {e}")

    def __init__(self, name, config, reserved_port_ids=[]):
        super().__init__(name, config, reserved_port_ids)

        assert self.outlet_labels
        assert self.outlet_status

        if not hasattr(self, 'outlet_ctrl'):
            # Some PDUs offer a RW status tree, others require a separate
            # tree for writes. Default to the seemingly more common case
            # of a RW tree.
            self.outlet_ctrl = self.outlet_status

        if not hasattr(self, 'outlet_power'):
            self.outlet_power = None

        # Multiplier to be applied to the power reporting to obtain Watts
        if not hasattr(self, 'outlet_power_multiplier'):
            self.outlet_power_unit = 1

        # FIXME: The UNKNOWN status is a bit of an odd one, not all PDUs expose such a concept.
        assert self.state_mapping.keys() == set([PDUPortState.ON, PDUPortState.OFF, PDUPortState.REBOOT])
        if not hasattr(self, 'inverse_state_mapping'):
            self.inverse_state_mapping: dict[int, PDUPortState] = \
                dict([(value, key) for key, value in self.state_mapping.items()])
        else:
            assert self.inverse_state_mapping.keys() == set([PDUPortState.ON, PDUPortState.OFF, PDUPortState.REBOOT])

        # Validate the configuration by getting the list of ports
        self._ports = []
        self._port_labels_cached = []
        self.ports

    @cached_property
    def session(self):
        config = self.config

        if 'hostname' not in config:
            raise ValueError('SnmpPDU requires a "hostname" configuration key')

        version = config.get('version', 1)
        if version in [1, 2]:
            session = Session(hostname=config['hostname'], community=config.get('community', 'private'),
                              version=version, timeout=config.get('timeout', 1))
        elif version == 3:
            # Only keep supported keys
            supported_keys = {'hostname', 'security_username', 'privacy_protocol', 'privacy_password',
                              'auth_protocol', 'auth_password', 'context_engine_id', 'security_engine_id',
                              'version', 'timeout'}
            session_cfg = {k: v for k, v in config.items() if k in supported_keys}

            auth_protocol = session_cfg.get('auth_protocol')
            privacy_protocol = session_cfg.get('privacy_protocol')
            if auth_protocol is not None and privacy_protocol is not None:
                session_cfg['security_level'] = 'auth_with_privacy'
            elif auth_protocol is not None and privacy_protocol is None:
                session_cfg['security_level'] = 'auth_without_privacy'
            elif auth_protocol is None and privacy_protocol is None:
                session_cfg['security_level'] = 'no_auth_or_privacy'
            else:
                raise ValueError("Unsupported security level: Can't have a privacy protocol with no auth protocol")

            session = Session(**session_cfg)
        else:
            raise ValueError(f"SNMP version {version} is unsupported")

        return session

    @property
    def outlet_labels_oid(self):
        return self.outlet_labels

    def outlet_oid_index(self, port_id: int):
        assert port_id >= 1, "The port ID should be 1-indexed"
        assert port_id <= len(self._port_labels_cached), "The port ID is outside the available range"
        return int(self._port_labels_cached[port_id - 1].oid.split(".")[-1])

    def outlet_status_oid(self, port_id: int):
        assert isinstance(port_id, int)
        return f'{self.outlet_status}.{self.outlet_oid_index(port_id)}'

    def outlet_ctrl_oid(self, port_id: int):
        assert isinstance(port_id, int)
        return f'{self.outlet_ctrl}.{self.outlet_oid_index(port_id)}'

    def outlet_power_oid(self, port_id: int):
        assert isinstance(port_id, int)
        if self.outlet_power:
            return f'{self.outlet_power}.{self.outlet_oid_index(port_id)}'

    @property
    def ports(self):
        labels = [label.value for label in self._refresh_port_labels()]
        for i, label in enumerate(labels):
            if len(self._ports) <= i:
                port = PDUPort(pdu=self, port_id=i+1)
                self._ports.append(port)
            else:
                port = self._ports[i]

            # Update the label
            port.label = labels[i]

        # Truncate the list of ports if it shrank
        self._ports = self._ports[0:len(labels)]

        return self._ports

    def _port_spec_to_int(self, port_spec):
        if _is_int(port_spec):
            return port_spec
        else:
            for port in self.ports:
                if port.label == port_spec:
                    return port.port_id
            raise ValueError(
                f"{port_spec} can not be interpreted as a valid port")

    @retry_on_known_errors
    def set_port_state(self, port_spec, state):
        SNMP_INTEGER_TYPE = 'i'

        port_id = self._port_spec_to_int(port_spec)
        logger.debug('setting OID %s to state %s with value %d',
                     self.outlet_ctrl_oid(port_id),
                     state,
                     self.state_mapping[state])
        ret = self.session.set(self.outlet_ctrl_oid(port_id),
                               self.state_mapping[state],
                               SNMP_INTEGER_TYPE)

        if self.state_transition_delay_seconds is not None:
            logger.debug("Enforcing %s seconds of delay for state change", self.state_transition_delay_seconds)
            # TODO: keep track of state changes to avoid a forced sleep.
            # TODO: Polling for the state change would be better in general.
            # The root cause of this is because PDUs maintain their
            # own configurables how long to delay between
            # transitions, we should probably control that via SNMP,
            # as well.
            time.sleep(self.state_transition_delay_seconds)

        return ret

    @retry_on_known_errors
    def get_port_state(self, port_spec):
        port_id = self._port_spec_to_int(port_spec)
        vs = self.session.get(self.outlet_status_oid(port_id))
        value = int(vs.value)
        logger.debug('retrieved OID %s with value %d, maps to state %s',
                     self.outlet_status_oid(port_id),
                     value,
                     self.inverse_state_mapping[value])
        return self.inverse_state_mapping[value]

    @retry_on_known_errors
    def get_port_full_state(self, port_spec):
        full_state = PDUPortFullState()

        full_state.state = self.get_port_state(port_spec)

        if self.outlet_power:
            # Allow the polling to fail, as some drivers work for multiple models that may have different feature-set
            try:
                full_state.instant_power = int(self.session.get(self.outlet_power_oid(port_spec)).value)
                full_state.instant_power *= self.outlet_power_multiplier
            except Exception:  # pragma: nocover
                pass

        return full_state

    def __eq__(self, other):
        return not any([
            getattr(self, attr, None) != getattr(other, attr, None)
            for attr in ["name",
                         "config",
                         "system_id",
                         "outlet_labels",
                         "outlet_status",
                         "outlet_ctrl",
                         "outlet_power",
                         "state_mapping",
                         "inverse_state_mapping"]])


class ManualSnmpPDU(SnmpPDU):
    driver_name = 'snmp'

    def __init__(self, name, config, reserved_port_ids=[]):
        if inverse_state_mapping := config.get('inverse_state_mapping'):
            self.inverse_state_mapping = self.__generate_state_mapping(inverse_state_mapping)

        super().__init__(name, config, reserved_port_ids)

    @property
    def system_id(self):
        # NOTE: We used to require a system_id which acted as a prefix that was appended to
        # 1.3.6.1.4.1. We dropped that in favour of requiring the full path every time, but
        # we try here to keep the backwards compatibility to previous configs
        if system_id := self.config.get('system_id'):
            return f"1.3.6.1.4.1.{system_id}"
        else:
            return ""

    @property
    def outlet_labels(self):
        outlet_labels = self.config['outlet_labels']

        if self.config.get('system_id'):
            return f"{self.system_id}.{outlet_labels}"
        else:
            return outlet_labels

    @property
    def outlet_status(self):
        outlet_status = self.config['outlet_status']

        if self.config.get('system_id'):
            return f"{self.system_id}.{outlet_status}"
        else:
            return outlet_status

    # Some PDUs offer a RW status tree, others require a separate
    # tree for writes. Default to the seemingly more common case
    # of a RW tree.
    @property
    def outlet_ctrl(self):
        if outlet_ctrl := self.config.get('outlet_ctrl'):
            if self.config.get('system_id'):
                return f"{self.system_id}.{outlet_ctrl}"
            else:
                return outlet_ctrl
        else:
            return self.outlet_status

    @property
    def outlet_power(self):
        if outlet_power := self.config.get('outlet_power'):
            if self.config.get('system_id'):
                return f"{self.system_id}.{outlet_power}"
            else:
                return outlet_power

    def __generate_state_mapping(self, d):
        state_mapping = dict()

        for state, internal_value in d.items():
            v = int(internal_value)
            if state.lower() == "on":
                state_mapping[PDUPortState.ON] = v
            elif state.lower() == "off":
                state_mapping[PDUPortState.OFF] = v
            elif state.lower() == "reboot":
                state_mapping[PDUPortState.REBOOT] = v
                # Unknown deliberately excluded.

        return state_mapping

    @property
    def state_mapping(self):
        return self.__generate_state_mapping(self.config.get('state_mapping', {}))
