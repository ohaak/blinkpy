"""
Test all camera attributes.

Tests the camera initialization and attributes of
individual BlinkCamera instantiations once the
Blink system is set up.
"""

import unittest
from unittest import mock
from blinkpy import blinkpy
from blinkpy.helpers.util import create_session, BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCamera, MAX_CLIPS
import tests.mock_responses as mresp

USERNAME = 'foobar'
PASSWORD = 'deadbeef'

CAMERA_CFG = {
    'camera': [
        {
            'battery_voltage': 90,
            'motion_alert': True,
            'wifi_strength': -30,
            'temperature': 68
        }
    ]
}


@mock.patch('blinkpy.helpers.util.Session.send',
            side_effect=mresp.mocked_session_send)
class TestBlinkCameraSetup(unittest.TestCase):
    """Test the Blink class in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = blinkpy.Blink(username=USERNAME,
                                   password=PASSWORD)
        header = {
            'Host': 'abc.zxc',
            'TOKEN_AUTH': mresp.LOGIN_RESPONSE['authtoken']['authtoken']
        }
        # pylint: disable=protected-access
        self.blink._auth_header = header
        self.blink.session = create_session()
        self.blink.urls = BlinkURLHandler('test')
        self.blink.sync = BlinkSyncModule(self.blink)
        self.camera = BlinkCamera(self.blink.sync)
        self.camera.name = 'foobar'
        self.blink.sync.cameras['foobar'] = self.camera

    def tearDown(self):
        """Clean up after test."""
        self.blink = None

    def test_check_for_motion(self, mock_sess):
        """Test check for motion function."""
        self.assertEqual(self.camera.last_record, [])
        self.assertEqual(self.camera.motion_detected, None)
        self.camera.sync.record_dates = {'foobar': [1, 3, 2, 4]}
        self.camera.check_for_motion()
        self.assertEqual(self.camera.last_record, [4])
        self.assertEqual(self.camera.motion_detected, False)
        self.camera.sync.record_dates = {'foobar': [7, 1, 3, 4]}
        self.camera.check_for_motion()
        self.assertEqual(self.camera.last_record, [7, 4])
        self.assertEqual(self.camera.motion_detected, True)
        self.camera.check_for_motion()
        self.assertEqual(self.camera.last_record, [7, 4])
        self.assertEqual(self.camera.motion_detected, False)

    def test_max_motion_clips(self, mock_sess):
        """Test that we only maintain certain number of records."""
        for i in range(0, MAX_CLIPS):
            self.camera.last_record.append(i)
        self.camera.sync.record_dates['foobar'] = [MAX_CLIPS+2]
        self.assertEqual(len(self.camera.last_record), MAX_CLIPS)
        self.camera.check_for_motion()
        self.assertEqual(self.camera.motion_detected, True)
        self.assertEqual(len(self.camera.last_record), MAX_CLIPS)

    def test_camera_update(self, mock_sess):
        """Test that we can properly update camera properties."""
        config = {
            'name': 'new',
            'camera_id': 1234,
            'network_id': 5678,
            'serial': '12345678',
            'enabled': False,
            'battery_voltage': 90,
            'battery_state': 'ok',
            'temperature': 68,
            'wifi_strength': 4,
            'thumbnail': '/thumb',
        }
        self.camera.last_record = ['1']
        self.camera.sync.all_clips = {'new': {'1': '/test.mp4'}}
        mock_sess.side_effect = [
            'test',
            'foobar'
        ]
        self.camera.update(config)
        self.assertEqual(self.camera.name, 'new')
        self.assertEqual(self.camera.camera_id, '1234')
        self.assertEqual(self.camera.network_id, '5678')
        self.assertEqual(self.camera.serial, '12345678')
        self.assertEqual(self.camera.motion_enabled, False)
        self.assertEqual(self.camera.battery, 50)
        self.assertEqual(self.camera.temperature, 68)
        self.assertEqual(self.camera.temperature_c, 20)
        self.assertEqual(self.camera.wifi_strength, 4)
        self.assertEqual(self.camera.thumbnail,
                         'https://rest.test.immedia-semi.com/thumb.jpg')
        self.assertEqual(self.camera.clip,
                         'https://rest.test.immedia-semi.com/test.mp4')
        self.assertEqual(self.camera.image_from_cache, 'test')
        self.assertEqual(self.camera.video_from_cache, 'foobar')
