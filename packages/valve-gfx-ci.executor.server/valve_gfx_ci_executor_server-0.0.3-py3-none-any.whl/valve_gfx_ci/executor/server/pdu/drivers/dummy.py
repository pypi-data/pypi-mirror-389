from dataclasses import replace

from .. import PDU, PDUPort, PDUPortState, PDUPortFullState


class DummyPDU(PDU):
    driver_name = 'dummy'

    def __init__(self, name, config, reserved_port_ids=[]):
        self._ports = []

        for i, port_label in enumerate(config.get('ports', [])):
            port = PDUPort(self, i, port_label)
            port._full_state = PDUPortFullState(state=PDUPortState.ON)
            self._ports.append(port)

        super().__init__(name, config, reserved_port_ids)

    @property
    def ports(self):
        return self._ports

    def set_port_state(self, port_id, state):
        port = self.ports[int(port_id)]
        port._full_state.state = state

    def get_port_full_state(self, port_id):
        port = self.ports[int(port_id)]

        # Return a **COPY** of the current state, without modification, so that
        # users may mutate it without impacting the next read
        return replace(port._full_state)

    def get_port_state(self, port_id):
        return self.get_port_full_state(port_id).state
