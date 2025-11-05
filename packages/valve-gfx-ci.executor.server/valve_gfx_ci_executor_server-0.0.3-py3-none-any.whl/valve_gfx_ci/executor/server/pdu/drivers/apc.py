from functools import cached_property

from .snmp import SnmpPDU
from .. import PDUPowerState, PDUPortState, PDUPowerChannel


class ApcMasterswitchPDU(SnmpPDU):
    # Documentation: https://mibbrowser.online/mibdb_search.php?mib=POWERNET-MIB

    driver_name = 'apc_masterswitch'
    outlet_labels = '1.3.6.1.4.1.318.1.1.4.4.2.1.4'
    outlet_status = '1.3.6.1.4.1.318.1.1.4.4.2.1.3'
    outlet_power = '1.3.6.1.4.1.318.1.1.26.9.4.3.1.7'
    outlet_power_multiplier = 10

    power_phase_count_oid = '1.3.6.1.4.1.318.1.1.12.2.1.2.0'
    power_bank_count_oid = '1.3.6.1.4.1.318.1.1.12.2.1.4.0'
    power_load_oid = '1.3.6.1.4.1.318.1.1.12.2.3.1.1.2'

    state_mapping = {
        PDUPortState.ON: 1,
        PDUPortState.OFF: 2,
        PDUPortState.REBOOT: 3,
    }

    @cached_property
    def power_phase_count(self) -> int:
        return int(self.session.get(self.power_phase_count_oid).value)

    @cached_property
    def power_bank_count(self) -> int:
        return int(self.session.get(self.power_bank_count_oid).value)

    @cached_property
    def voltage(self):
        # If no voltage is set, we assume 230 since it is the most common value across countries
        return float(self.config.get("voltage", 230))

    @cached_property
    def power_factor(self) -> float:
        # 80 PLUS certification requires at least a 0.9 PF, but older PSUs may be as low as 0.6
        return float(self.config.get("power_factor", 0.9))

    @property
    def power_state(self) -> PDUPowerState:
        state = PDUPowerState()

        # From the documentation:
        # Getting this OID will return the measured Outlet load for an Outlet Monitored Rack PDU in tenths of Amps.
        # Number of entries = #phases + #banks.
        # NOTE: If a device has phase and bank information, all phase information shall precede the bank information.
        # If a device has total information, it shall precede both the bank and the phase information.
        raw_loads = self.session.walk(self.power_load_oid)

        # Early exit in case the APC does not support power monitoring
        if len(raw_loads) == 0:
            return state

        # Enforce that the number of entries matches expectations. See comment above raw_loads.
        expected_entries = self.power_phase_count + self.power_bank_count
        if (len(raw_loads) - expected_entries) not in [0, 1]:
            raise ValueError((f"Unexpected amount of load entries. Expected {expected_entries} or "
                              f"{expected_entries + 1} entries but got {len(raw_loads)}"))
        has_total = len(raw_loads) != expected_entries

        # Create the PDU Power Channel objects, and assign them to total/phases/bank
        phases = []
        banks = []
        for i, raw_load in enumerate(raw_loads):
            # NOTE: Raw loads are expressed in tenths of Amps. See comment above raw_loads.
            channel = PDUPowerChannel(instant_power=self.voltage * float(raw_load.value) * self.power_factor / 10)

            if i == 0 and has_total:
                state.total_power = channel
            elif i < int(has_total) + self.power_phase_count:
                phases.append(channel)
            else:
                banks.append(channel)

        # Make sure we expose the total amount of power if the PDU did not expose it
        if state.total_power is None:
            if len(phases) == 1:
                state.total_power = phases.pop()
            elif len(banks) == 1:
                state.total_power = banks.pop()
            elif len(phases) > 0:
                state.total_power = sum(phases, PDUPowerChannel())
            elif len(banks) > 0:
                state.total_power = sum(banks, PDUPowerChannel())

        # Add all the power and bank channels
        for i, phase in enumerate(phases):
            state.power_channels[f"Phase #{i+1}"] = phase
        for i, bank in enumerate(banks):
            state.power_channels[f"Bank #{i+1}"] = bank

        return state
