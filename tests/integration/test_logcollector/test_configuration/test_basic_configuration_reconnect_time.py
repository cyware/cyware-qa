'''
copyright: Copyright (C) 2015-2022 KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector detects invalid values for the
       'reconnect_time' tag. Log data collection is the real-time process of making sense out
       of the records generated by servers or devices. This component can receive logs through
       text files or Windows event logs. It can also directly receive logs via remote syslog
       which is useful for firewalls and other such devices.

components:
    - logcollector

suite: configuration

targets:
    - agent

daemons:
    - cyware-logcollector

os_platform:
    - windows

os_version:
    - Windows 10
    - Windows 8
    - Windows 7
    - Windows Server 2019
    - Windows Server 2016
    - Windows Server 2012
    - Windows Server 2003
    - Windows XP

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/localfile.html#reconnect-time

tags:
    - logcollector_configuration
'''
import os
import pytest
import sys
from cyware_testing.tools.configuration import load_cyware_configurations
import cyware_testing.logcollector as logcollector
from cyware_testing.tools.monitoring import FileMonitor
from cyware_testing.tools import LOG_FILE_PATH
from cyware_testing.tools.file import truncate_file
from cyware_testing.tools.services import control_service
import subprocess as sb

LOGCOLLECTOR_DAEMON = "cyware-logcollector"

# Configuration

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_basic_configuration.yaml')

# Marks
if sys.platform == 'win32':
    no_restart_windows_after_configuration_set = True
    force_restart_after_restoring = True
    pytestmark = pytest.mark.tier(level=0)
else:
    pytestmark = [pytest.mark.skip, pytest.mark.tier(level=0)]

location = r'Security'
cyware_configuration = 'ossec.conf'

parameters = [
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '3s'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '4000s'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '5m'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '99h'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '94201d'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '44sTesting'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': 'Testing44s'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '9hTesting'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '400mTesting'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': '3992'},
    {'LOG_FORMAT': 'eventchannel', 'LOCATION': f'{location}', 'RECONNECT_TIME': 'Testing'},
]

metadata = [
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '3s', 'valid_value': True},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '4000s', 'valid_value': True},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '5m', 'valid_value': True},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '99h', 'valid_value': True},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '94201d', 'valid_value': True},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '44sTesting', 'valid_value': False},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': 'Testing44s', 'valid_value': False},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '9hTesting', 'valid_value': False},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '400mTesting', 'valid_value': False},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': '3992', 'valid_value': False},
    {'log_format': 'eventchannel', 'location': f'{location}', 'reconnect_time': 'Testing', 'valid_value': False},
]

configurations = load_cyware_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['log_format']}_{x['location']}_{x['reconnect_time']}" for x in metadata]
problematic_values = ['44sTesting', '9hTesting', '400mTesting', '3992']


def check_configuration_reconnect_time_valid():
    """Check if Cyware module correctly runs and analyzes the desired eventchannel.

    Ensure logcollector is running with the specified configuration, analyzing the designate eventchannel.

    Raises:
        TimeoutError: If the "Analyzing eventchannel" callback is not generated.
    """
    cyware_log_monitor = FileMonitor(LOG_FILE_PATH)

    log_callback = logcollector.callback_eventchannel_analyzing('Security')
    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")


def check_configuration_reconnect_time_invalid(cfg):
    """Check if Cyware fails due to a invalid reconnect time attribute configuration value.

    Args:
        cfg (dict): Dictionary with the localfile configuration.

    Raises:
        TimeoutError: If error callback are not generated.
    """
    cyware_log_monitor = FileMonitor(LOG_FILE_PATH)

    log_callback = logcollector.callback_invalid_reconnection_time()
    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected invalid reconnection time error has not been produced")


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_configuration_reconnect_time(get_configuration, configure_environment):
    '''
    description: Check if the 'cyware-logcollector' daemon detects invalid settings for the 'reconnect_time' tag.
                 For this purpose, the test will set a 'localfile' section using both valid and invalid values
                 for that tag. Finally, the test will verify that the 'analyzing' event is triggered when using
                 a valid value or if the 'invalid' event is generated when using an invalid one.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.

    assertions:
        - Verify that the logcollector generates 'invalid' events when using invalid values
          for the 'reconnect_time' tag.
        - Verify that the logcollector monitors a log file when using valid values for the 'reconnect_time' tag.

    input_description: A configuration template (test_basic_configuration_reconnect_time) is contained in an
                       external YAML file (cyware_basic_configuration.yaml). That template is combined with
                       different test cases defined in the module. Those include configuration settings
                       for the 'cyware-logcollector' daemon.

    expected_output:
        - r'Analyzing event log.*'
        - r'Invalid reconnection time value. Changed to .* seconds.'

    tags:
        - invalid_settings
        - logs
    '''
    cfg = get_configuration['metadata']

    control_service('stop', daemon=LOGCOLLECTOR_DAEMON)
    truncate_file(LOG_FILE_PATH)

    if cfg['valid_value']:
        control_service('start', daemon=LOGCOLLECTOR_DAEMON)
        check_configuration_reconnect_time_valid()
    else:
        if cfg['reconnect_time'] in problematic_values:
            pytest.xfail("Logcolector accepts invalid values. Issue: https://github.com/cyware/cyware/issues/8158")
        else:
            control_service('start', daemon=LOGCOLLECTOR_DAEMON)
            check_configuration_reconnect_time_invalid(cfg)
