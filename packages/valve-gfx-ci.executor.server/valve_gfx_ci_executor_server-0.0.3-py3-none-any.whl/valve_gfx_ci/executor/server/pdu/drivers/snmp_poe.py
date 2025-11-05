from .snmp import SnmpPDU
from .. import PDUPortState, PDUPowerState, PDUPowerChannel


class SnmpPoePDU(SnmpPDU):
    driver_name = 'snmp_poe'

    outlet_labels = '1.3.6.1.2.1.105.1.1.1.9.1'
    outlet_status = '1.3.6.1.2.1.105.1.1.1.3.1'

    state_mapping = {
        PDUPortState.ON: 1,
        PDUPortState.OFF: 2,
        PDUPortState.REBOOT: 3,
    }

    @property
    def default_min_off_time(self):
        return 10.0

    @property
    def power_state(self) -> PDUPowerState:
        state = PDUPowerState()
        try:
            total_power_load_oid = '1.3.6.1.2.1.105.1.3.1.1.4.1'
            total_power_in_watts = int(self.session.get(total_power_load_oid).value)
            state.total_power = PDUPowerChannel(instant_power=total_power_in_watts)
        except Exception:  # pragma: no cover
            pass
        return state


class SnmpPoeTpLinkPDU(SnmpPDU):
    driver_name = 'snmp_poe_tplink'

    # MiB: https://mibbrowser.online/mibdb_search.php?mib=TPLINK-POWER-OVER-ETHERNET-MIB
    outlet_labels = '1.3.6.1.4.1.11863.6.56.1.1.2.1.1.1'
    outlet_status = '1.3.6.1.4.1.11863.6.56.1.1.2.1.1.2'
    outlet_power = '1.3.6.1.4.1.11863.6.56.1.1.2.1.1.7'
    outlet_power_multiplier = 0.1

    state_mapping = {
        PDUPortState.ON: 1,
        PDUPortState.OFF: 0,
        PDUPortState.REBOOT: 2,
    }

    @property
    def default_min_off_time(self):
        return 10.0
