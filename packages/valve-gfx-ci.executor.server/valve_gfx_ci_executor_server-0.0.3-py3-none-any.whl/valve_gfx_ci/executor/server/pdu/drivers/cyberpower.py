from .snmp import SnmpPDU
from .. import PDUPortState


class PDU41004(SnmpPDU):
    driver_name = 'cyberpower_pdu41004'
    outlet_labels = '1.3.6.1.4.1.3808.1.1.3.3.3.1.1.2'
    outlet_status = '1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4'

    state_mapping = {
        PDUPortState.ON: 1,
        PDUPortState.OFF: 2,
        PDUPortState.REBOOT: 3,
    }

    state_transition_delay_seconds = 5


class PDU15SWHVIEC12ATNET(SnmpPDU):
    driver_name = 'cyberpower_pdu15swhviec12atnet'
    outlet_labels = '1.3.6.1.4.1.3808.1.1.5.6.3.1.2'
    outlet_status = '1.3.6.1.4.1.3808.1.1.5.6.3.1.3'
    outlet_ctrl = '1.3.6.1.4.1.3808.1.1.5.6.5.1.3'

    state_mapping = {
        PDUPortState.ON: 2,
        PDUPortState.OFF: 3,
        PDUPortState.REBOOT: 4,
    }

    # The RMCARD205 management card in this PDU kindly chooses
    # different ints for control vs status codes.
    inverse_state_mapping = {
        1: PDUPortState.ON,
        2: PDUPortState.OFF,
        3: PDUPortState.REBOOT,
    }

    state_transition_delay_seconds = 5
