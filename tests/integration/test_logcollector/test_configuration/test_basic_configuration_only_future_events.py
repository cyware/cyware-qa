'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector detects invalid values for
       the 'only-future-events' and 'max-size' tags.
       Log data collection is the real-time process of making sense out of the records generated by
       servers or devices. This component can receive logs through text files or Windows event logs.
       It can also directly receive logs via remote syslog which is useful for firewalls and
       other such devices.

components:
    - logcollector

suite: configuration

targets:
    - agent
    - manager

daemons:
    - cyware-logcollector

os_platform:
    - linux
    - macos
    - windows

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - Debian Buster
    - Red Hat 8
    - macOS Catalina
    - macOS Server
    - Ubuntu Focal
    - Ubuntu Bionic
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/localfile.html#only-future-events

tags:
    - logcollector_configuration
'''
import os
import pytest
import sys
import time

from cyware_testing.tools.configuration import load_cyware_configurations
import cyware_testing.generic_callbacks as gc
import cyware_testing.logcollector as logcollector
from cyware_testing.tools.monitoring import WINDOWS_AGENT_DETECTOR_PREFIX, FileMonitor, LOG_COLLECTOR_DETECTOR_PREFIX
from cyware_testing.tools import get_service, LOG_FILE_PATH
from tempfile import gettempdir
from cyware_testing.tools.utils import lower_case_key_dictionary_array
from cyware_testing.tools.services import control_service

LOGCOLLECTOR_DAEMON = "cyware-logcollector"
prefix = LOG_COLLECTOR_DETECTOR_PREFIX

# Marks
pytestmark = pytest.mark.tier(level=0)

# Configuration
no_restart_windows_after_configuration_set = True
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_basic_configuration.yaml')

cyware.khulnasoft.component = get_service()
first_macos_log_process = False
macos_process_timeout_init = 10

cyware_log_monitor = FileMonitor(LOG_FILE_PATH)

temp_file_path = os.path.join(gettempdir(), 'testing.log')


log_format_list = ['syslog', 'json', 'snort-full', 'mysql_log', 'postgresql_log', 'nmapg', 'iis', 'djb-multilog',
                   'multi-line:3', 'squid', 'audit']
tcases = []


if sys.platform == 'win32':
    prefix = WINDOWS_AGENT_DETECTOR_PREFIX
    log_format_list += ['eventchannel']
elif sys.platform == 'darwin':
    log_format_list += ['macos']

for log_format in log_format_list:
    if log_format == 'djb-multilog':
        location = '/var/log/testing/current'
    elif log_format == 'eventchannel':
        location = 'Security'
    elif log_format == 'macos':
        location = log_format
    else:
        location = temp_file_path

    tcases += [
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no',
            'MAX-SIZE': '9999999999999999999999999999999B', 'INVALID_VALUE': 'max-size'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '20B',
         'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '5000B',
         'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '500KB',
         'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '50MB',
         'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '5GB',
         'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no',
         'MAX-SIZE': '43423423423', 'INVALID_VALUE': 'max-size'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '-12345',
         'INVALID_VALUE': 'max-size'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': 'test',
         'INVALID_VALUE': 'max-size'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '{/}',
         'INVALID_VALUE': 'max-size'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'MAX-SIZE': '!32817--',
         'INVALID_VALUE': 'max-size'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'yes', 'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'yesTesting',
         'INVALID_VALUE': 'only-future-events'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'noTesting',
         'INVALID_VALUE': 'only-future-events'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'testingvalue',
         'INVALID_VALUE': 'only-future-events'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': '1234',
         'INVALID_VALUE': 'only-future-events'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'yes', 'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'no', 'INVALID_VALUE': ''},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'yesTesting',
         'INVALID_VALUE': 'only-future-events'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'noTesting',
         'INVALID_VALUE': 'only-future-events'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': 'testingvalue',
         'INVALID_VALUE': 'only-future-events'},
        {'LOCATION': f"{location}", 'LOG_FORMAT': f'{log_format}', 'ONLY-FUTURE-EVENTS': '1234',
         'INVALID_VALUE': 'only-future-events'}
    ]

metadata = lower_case_key_dictionary_array(tcases)

for element in tcases:
    element.pop('INVALID_VALUE')

parameters = tcases

configurations = load_cyware_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['log_format']}_{x['only-future-events']}_{x['max-size']}" + f"" if 'max-size' in x
                     else f"{x['log_format']}_{x['only-future-events']}" for x in metadata]


@pytest.fixture(scope="module")
def generate_macos_logs(get_configuration):
    """Get configurations from the module."""
    global first_macos_log_process
    if not first_macos_log_process and sys.platform == 'darwin' and \
       get_configuration['metadata']['log_format'] == 'macos':
        control_service('restart', 'cyware-logcollector')
        time.sleep(macos_process_timeout_init)

        first_macos_log_process = True


def check_only_future_events_valid(cfg):
    """Check if Cyware runs correctly with the specified only future events field.

    Ensure logcollector allows the specified future events attribute.

    Raises:
        TimeoutError: If the "Analyzing file" callback is not generated.
    """
    error_message = logcollector.GENERIC_CALLBACK_ERROR_ANALYZING_FILE

    if sys.platform == 'win32' and cfg['log_format'] == 'eventchannel':
        error_message = logcollector.GENERIC_CALLBACK_ERROR_ANALYZING_EVENTCHANNEL
        log_callback = logcollector.callback_eventchannel_analyzing(cfg['location'])

    elif sys.platform == 'darwin' and cfg['log_format'] == 'macos':
        error_message = logcollector.GENERIC_CALLBACK_ERROR_ANALYZING_MACOS
        if cfg['only-future-events'] == 'no':
            log_callback = logcollector.callback_monitoring_macos_logs(True)
            cyware_log_monitor.start(timeout=5, callback=log_callback,
                                    error_message=error_message)

        log_callback = logcollector.callback_monitoring_macos_logs()

    else:
        log_callback = logcollector.callback_analyzing_file(cfg['location'])

    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=error_message)


def check_only_future_events_invalid(cfg):
    """Check if Cyware fails due to a invalid only future events configuration value.

    Args:
        cfg (dict): Dictionary with the localfile configuration.

    Raises:
        TimeoutError: If error callbacks are not generated.
    """

    invalid_value = cfg['invalid_value']

    if invalid_value == 'max-size':
        option_value = cfg['max-size']
        log_callback = gc.callback_invalid_attribute('only-future-events', 'max-size', option_value,
                                                     prefix, severity="WARNING")
    else:
        option_value = cfg['only-future-events']
        log_callback = gc.callback_invalid_value(invalid_value, option_value, prefix, severity="WARNING")

    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=gc.GENERIC_CALLBACK_ERROR_MESSAGE)


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.skip("This test needs refactor/fixes. Has flaky behaviour. Skipped by Issue #3218")
def test_only_future_events(get_configuration, configure_environment, generate_macos_logs, restart_logcollector):
    '''
    description: Check if the 'cyware-logcollector' daemon detects invalid settings for the 'only-future-events',
                 and 'max-size' tags. For this purpose, the test will set a 'localfile' section using both
                 valid and invalid values for those tags. Finally, it will verify that the 'analyzing' or
                 'monitoring' event (depending on the OS) is triggered when using a valid value, or if an
                 error event is generated when using an invalid one.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - generate_macos_logs:
            type: fixture
            brief: Restart the logcollector daemon to get the first macos log process.
        - restart_logcollector:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.

    assertions:
        - Verify that the logcollector generates error events when using invalid values
          for the 'only-future-events' tag.
        - Verify that the logcollector generates 'analyzing' or 'monitoring' events when using valid values
          for the 'only-future-events' tag.

    input_description: A configuration template (test_basic_configuration_only_future_events) is contained in an
                       external YAML file (cyware_basic_configuration.yaml). That template is combined with
                       different test cases defined in the module. Those include configuration settings
                       for the 'cyware-logcollector' daemon.

    expected_output:
        - r'Analyzing file.*'
        - r'INFO.* Analyzing event log.*' (on Windows systems)
        - r'Monitoring macOS .* logs' (on macOS systems)
        - r'Invalid value .* for attribute .* in .* option'
        - r'Invalid value for element .*'

    tags:
        - invalid_settings
        - logs
    '''
    cfg = get_configuration['metadata']

    if cfg['invalid_value'] == '':
        check_only_future_events_valid(cfg)
    else:
        check_only_future_events_invalid(cfg)
