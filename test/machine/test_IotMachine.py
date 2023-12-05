import unittest
from datetime import datetime

from iot.machine.IotMachine import OnlineStatus, IotMachine


class DryerConstructionTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual(IotMachine('super machine').name, 'super machine')

    def test_watt(self):
        self.assertEqual(IotMachine('machine', None).watt, None)
        self.assertEqual(IotMachine('machine', 354).watt, 354)

    def test_online_status(self):
        self.assertEqual(IotMachine('machine').online_status(), OnlineStatus.UNKNOWN)
        machine_updated_now_and_online_delta_ten_seconds = IotMachine('machine', online_delta_in_seconds=10,
                                                                      last_updated_at=datetime.now())
        self.assertEqual(machine_updated_now_and_online_delta_ten_seconds.online_status(), OnlineStatus.ONLINE)
        machine_without_online_delta = IotMachine('machine', online_delta_in_seconds=0,
                                                  last_updated_at=datetime.now())
        self.assertEqual(machine_without_online_delta.online_status(), OnlineStatus.OFFLINE)

    def test_to_dict_has_mandatory_fields(self):
        last_updated_at = datetime.now()
        dryer = IotMachine("test", 312.5, last_updated_at=last_updated_at)
        self.assertDictEqual(dryer.to_dict(),
                             {"name": "test", "watt": 312.5, "online_status": OnlineStatus.ONLINE,
                              "last_updated_at": last_updated_at.isoformat()})


if __name__ == '__main__':
    unittest.main()
