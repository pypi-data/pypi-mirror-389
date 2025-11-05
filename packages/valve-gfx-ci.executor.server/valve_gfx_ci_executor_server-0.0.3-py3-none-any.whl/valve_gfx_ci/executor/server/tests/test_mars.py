import tempfile

from server.mars import MarsDB


def test_MarsDB__load_serialize_deserialize_minimal_db():
    # This test is meant to test we can keep on loading an earlier version of the DB

    db = {
        "pdus": {
            "vpdu": {
                "driver": "apc_masterswitch",
                "config": {"hostname": "192.168.42.2"}
            }
        },
        "duts": {
            "6c:cf:39:00:2d:b6": {
                "base_name": "starfive-visionfive-2-v1.3b",
                "ip_address": "10.42.0.7",
                "tags": ["tag1", "tag2"],
                "mac_address": "6c:cf:39:00:2d:b6",
            }
        },
        "gitlab": {
            "freedesktop": {
                "expose_runners": False,
                "url": "https://gitlab.freedesktop.org/",
            }
        }
    }

    with tempfile.NamedTemporaryFile() as f:
        MarsDB(**db).save(f.name)

        marsdb = MarsDB.from_file(f.name)

        assert "vpdu" in marsdb.pdus
        assert "6c:cf:39:00:2d:b6" in marsdb.duts
        assert "freedesktop" in marsdb.gitlab
