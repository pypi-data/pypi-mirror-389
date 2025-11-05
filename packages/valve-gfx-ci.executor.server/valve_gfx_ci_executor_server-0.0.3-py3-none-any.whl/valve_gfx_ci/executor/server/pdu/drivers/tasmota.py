from functools import cached_property

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests

from .. import PDU, PDUPort, PDUPortState, PDUSimpleNetworkProbeMixin


class TasmotaPDU(PDU, PDUSimpleNetworkProbeMixin):
    driver_name = 'tasmota'

    @property
    def requests_retry_session(self, retries=3, backoff_factor=1,
                               status_forcelist=[], session=None):  # pragma: nocover
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def url(self, path):
        hostname = self.config['hostname']
        return f"http://{hostname}{path}"

    def get(self, path):
        r = self.requests_retry_session.get(self.url(path))
        r.raise_for_status()
        return r.json()

    @cached_property
    def num_ports(self):
        # NOTE: We really want to have a stable amount of ports, even in the presence
        # of network issues, so let's depend on the one thing we have: the status

        status = self.raw_status.get('Status', {})

        friendly_names = status.get("FriendlyName")
        if type(friendly_names) is list:
            port_count = len(friendly_names)
        else:  # pragma: nocover
            port_count = 1

        return port_count

    def __init__(self, name, config, reserved_port_ids=[]):
        super().__init__(name, config, reserved_port_ids)

        self.raw_status = self.get('/cm?cmnd=Status')

        self._ports = [PDUPort(self, str(p)) for p in range(self.num_ports)]

    @property
    def ports(self):
        return self._ports

    def __Power_to_PDUPortState(self, power):  # pragma: nocover
        if power in ["ON", "OFF"]:
            return PDUPortState[power]
        elif power.lower() in ['1', 'true']:
            return PDUPortState.ON
        elif power.lower() in ['0', 'false']:
            return PDUPortState.OFF
        else:
            raise ValueError(f"Unknown power status '{power}'")

    def __port_id_to_power_id(self, port_id):
        return int(port_id) + 1

    def _get_port_state(self, poid, raw_port):
        state = raw_port.get('POWER')
        if not state:
            state = raw_port.get(f'POWER{poid}')
        return self.__Power_to_PDUPortState(state)

    def set_port_state(self, port_id, state):
        if state in [PDUPortState.ON, PDUPortState.OFF]:
            poid = self.__port_id_to_power_id(port_id)
            raw_port = self.get(f'/cm?cmnd=Power{poid}%20{state.name}')
            return self._get_port_state(poid, raw_port) == state

    def get_port_state(self, port_id):
        poid = self.__port_id_to_power_id(port_id)
        raw_port = self.get(f'/cm?cmnd=Power{poid}')
        return self._get_port_state(poid, raw_port)
