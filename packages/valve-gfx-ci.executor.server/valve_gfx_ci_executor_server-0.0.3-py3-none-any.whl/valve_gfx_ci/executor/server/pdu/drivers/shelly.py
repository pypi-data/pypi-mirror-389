from functools import cached_property
from typing import Self
import re
import traceback

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests

from .. import PDU, PDUPort, PDUPortState, PDUPortFullState


class ShellyPDU(PDU):
    driver_name = 'shelly'

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
        r = self.requests_retry_session.get(self.url(path), timeout=1)
        r.raise_for_status()
        return r.json()

    @property
    def gen(self):
        if gen := self.raw_dev.get('gen'):  # Gen 2+ hardware
            return gen
        else:
            return 1

    @cached_property
    def num_ports(self):
        # NOTE: We really want to have a stable amount of ports, even in the presence
        # of network issues, so let's depend on the one thing we have: `/shelly`

        if self.gen == 1:
            return self.raw_dev.get('num_outputs')
        elif app := self.raw_dev.get('app'):
            if app in ['PlusPlugS']:
                return 1
            elif m := re.match(r'^(Pro|Plus)(\d)(PM)?$', app):
                return int(m.groups()[1])

        # Assume the worst: no controllable ports
        return 0

    def __init__(self, name, config, reserved_port_ids=[]):
        super().__init__(name, config, reserved_port_ids)

        self.raw_dev = self.get('/shelly')

        if self.gen not in [1, 2] or self.num_ports == 0:
            t = self.raw_dev.get('type')
            m = self.raw_dev.get('model')
            a = self.raw_dev.get('app')
            raise ValueError(f"Unknown Shelly device: gen={self.gen}, type={t}, model={m}, app={a}")

        self._ports = [PDUPort(self, str(oid)) for oid in range(self.num_ports)]

    @classmethod
    def network_probe(cls, ip_address: str, mac_address: str, dhcp_client_name: str = None) -> Self:
        return cls(dhcp_client_name or f"{cls.driver_name}-{mac_address}", config={"hostname": ip_address})

    @property
    def ports(self):
        # Update the ports, in case their name changed
        for port in self._ports:
            if self.gen == 1:
                raw_port = self.get(f'/settings/relay/{port.port_id}')
                port.label = raw_port.get('name')
            else:
                raw_port = self.get(f'/rpc/Switch.GetConfig?id={port.port_id}')
                port.label = raw_port.get('name')

        return self._ports

    def __ison_to_PDUPortState(self, ison):
        return PDUPortState.ON if ison else PDUPortState.OFF

    def set_port_state(self, port_id, state):
        if self.gen == 1:
            raw_port = self.get(f'/relay/{port_id}?turn={state.name.lower()}')
            return self.__ison_to_PDUPortState(raw_port.get('ison')) == state
        else:
            ison = str(state == PDUPortState.ON).lower()
            self.get(f'/rpc/Switch.Set?id={port_id}&on={ison}')
            return True

    def _get_port_state(self, port_id, full=False):
        state = PDUPortFullState()

        if self.gen == 1:
            raw_port = self.get(f'/relay/{port_id}')
            state.state = self.__ison_to_PDUPortState(raw_port.get('ison'))

            if full:
                try:
                    raw_meter = self.get(f'/meter/{port_id}')
                    if raw_meter.get("is_valid", False):
                        state.instant_power = raw_meter.get("power")

                        # NOTE: We are ignoring the reported energy because it only gets updated every minute, rather
                        # than at every sample.
                except requests.exceptions.JSONDecodeError:  # pragma: nocover
                    pass
                except Exception:
                    traceback.print_exc()
        else:
            raw_port = self.get(f'/rpc/Switch.GetStatus?id={port_id}')
            state.state = self.__ison_to_PDUPortState(raw_port.get('output'))

            if full:
                state.instant_power = raw_port.get("apower")

                # `aenergy.total`: Last counter value of the total energy consumed in Watt-hours
                # Source: https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Switch#status
                state.energy = raw_port.get("aenergy", {}).get("total", 0) * 3600

        return state

    def get_port_state(self, port_id):
        return self._get_port_state(port_id, full=False).state

    def get_port_full_state(self, port_id):
        return self._get_port_state(port_id, full=True)
