from dataclasses import fields
from unittest.mock import MagicMock

from deepdiff import DeepDiff

from server.boots_db import USBMatcher, FastbootDeviceMatcher, BootsDB
from server import config

usb_device_fields = dict(idVendor=0x4242, idProduct=0x1234, iManufacturer="MuPuF TMI",
                         iProduct="CI-tron", iSerialNumber="serialno")
usb_device = MagicMock(**usb_device_fields)


def test_USBMatcher():
    # Make sure the list of fields is up to date
    assert set(usb_device_fields.keys()) == {f.name for f in fields(USBMatcher)}

    # Empty matcher matches everything
    assert USBMatcher().matches(usb_device)

    # Single field match
    assert USBMatcher(iManufacturer=usb_device.iManufacturer).matches(usb_device)

    # Full match with direct values
    assert USBMatcher(idVendor=usb_device.idVendor, idProduct=usb_device.idProduct,
                      iManufacturer=usb_device.iManufacturer, iProduct=usb_device.iProduct,
                      iSerialNumber=usb_device.iSerialNumber).matches(usb_device)

    # Full match with lists of acceptable values
    assert USBMatcher(idVendor=[usb_device.idVendor, 0x4343],
                      idProduct=[0x4321, usb_device.idProduct],
                      iManufacturer=["Someone else", usb_device.iManufacturer],
                      iProduct=["OtherProduct", usb_device.iProduct],
                      iSerialNumber=[usb_device.iSerialNumber, "OtherSerial"]).matches(usb_device)

    # Make sure that every field is important for the match
    for key, value in usb_device_fields.items():
        new_fields = dict(usb_device_fields)

        if isinstance(value, int):
            new_fields[key] += 1
        elif isinstance(value, str):
            new_fields[key] += "-"

        assert not USBMatcher(**new_fields).matches(usb_device)


def test_FastbootDeviceMatcher():
    usb_matcher = USBMatcher(**usb_device_fields)
    full_variables = {"product": "myproduct", "manufacturer": "MuPuF TMI", "serialno": "123456"}

    # Empty means matches everything!
    assert FastbootDeviceMatcher().matches(MagicMock())

    # USB match only
    assert FastbootDeviceMatcher(usb=usb_matcher).matches(MagicMock(device=usb_device))
    assert not FastbootDeviceMatcher(usb=USBMatcher(idVendor=0x1234)).matches(MagicMock(device=usb_device))

    # Make sure that no variables set means a match!
    assert FastbootDeviceMatcher(variables={}).matches(MagicMock(variables=full_variables))

    # Try adding variables and make sure it still matches
    match_variables = {}
    for var, value in full_variables.items():
        match_variables[var] = value
        assert FastbootDeviceMatcher(variables=match_variables).matches(MagicMock(variables=full_variables))

    # Ensure that missing variables do not count as a match
    assert not FastbootDeviceMatcher(variables={"missing": "value"}).matches(MagicMock(variables={}))

    # Ensure that variables with different values do not count as a match
    assert not FastbootDeviceMatcher(variables={"key": "value"}).matches(MagicMock(variables={"key": "othervalue"}))


def test_BootsDB_render():
    # Make sure we can parse the default database, without any parameter
    boots_db1 = BootsDB.from_path(config.BOOTS_DB_FILE)
    boots_db2 = BootsDB.from_path(config.BOOTS_DB_FILE)

    # Ensure that two fresh loads agree that the objects are the same
    assert boots_db1 == boots_db2
    assert DeepDiff(boots_db1, boots_db2) == {}
