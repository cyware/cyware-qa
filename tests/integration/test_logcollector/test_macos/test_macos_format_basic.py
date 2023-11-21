'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector properly processes the macOS
       unified logging system (ULS) events. Log data collection is the real-time process of making
       sense out of the records generated by servers or devices. This component can receive logs
       through text files or Windows event logs. It can also directly receive logs via remote
       syslog which is useful for firewalls and other such devices.

components:
    - logcollector

suite: macos

targets:
    - agent

daemons:
    - cyware-logcollector

os_platform:
    - macos

os_version:
    - macOS Catalina
    - macOS Server

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/localfile.html
    - https://developer.apple.com/documentation/os/logging

tags:
    - logcollector_macos
'''
import os
import pytest
import time

import cyware_testing.logcollector as logcollector
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools.services import control_service

# Marks
pytestmark = [pytest.mark.darwin, pytest.mark.tier(level=0)]

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_macos_format_basic.yaml')

configurations = load_cyware_configurations(configurations_path, __name__)

daemons_handler_configuration = {'daemons': ['cyware-logcollector']}

local_internal_options = {'logcollector.debug': 2,
                          'logcollector.sample_log_length': 200}

macos_timeout_process_init = 3

macos_log_messages = [
    {
        'command': 'os_log',
        'type': 'log',
        'level': 'error',
        'subsystem': 'testing.cyware-agent.macos',
        'category': 'category',
        'id': 'os_log_command'
    },
    {
        'command': 'logger',
        'message': 'Logger message example',
        'id': 'logger_command'
    }
]

macos_log_message_timeout = 40
macos_monitoring_macos_log_timeout = 30


# fixtures
@pytest.fixture(scope="module", params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.fixture(scope="function")
def restart_logcollector_function():
    control_service('restart', 'cyware-logcollector')


@pytest.mark.parametrize('macos_message', macos_log_messages,
                         ids=[log_message['id'] for log_message in macos_log_messages])
def test_macos_format_basic(restart_logcollector_required_daemons_package, get_configuration, configure_environment,
                            configure_local_internal_options_module, macos_message, file_monitoring,
                            daemons_handler_module, restart_logcollector_function):
    '''
    description: Check if the 'cyware-logcollector' gathers properly macOS unified logging system (ULS) events.
                 For this purpose, the test will configure a 'localfile' section using the macOS settings.
                 Once the logcollector is started, it will check if the 'monitoring' event is triggered,
                 indicating that the logcollector starts to monitor the macOS logs, and then, the test
                 will generate a ULS event by using a logger tool. After this, it will create a custom
                 callback from the testing ULS event, and finally, the test will verify that
                 the logcollector event with the testing log message has been generated.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - restart_logcollector_required_daemons_package:
            type: fixture
            brief: Restart the 'cyware-agentd', 'cyware-logcollector', and 'cyware-modulesd' daemons.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - configure_local_internal_options_module:
            type: fixture
            brief: Set internal configuration for testing.
        - macos_message:
            type: dict
            brief: Dictionary with the testing macOS ULS event.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
        - daemons_handler_module:
            type: fixture
            brief: Handler of Cyware daemons.
        - restart_logcollector_function:
            type: fixture
            brief: Restart the 'cyware-logcollector' daemon on each test case.

    assertions:
        - Verify that the logcollector starts monitoring the macOS ULS log messages.
        - Verify that the logcollector generates events from the macOS ULS log messages.

    input_description: A configuration template (test_macos_format_basic) is contained in an external YAML file
                       (cyware_macos_format_basic.yaml). That template is combined with two test cases defined
                       in the module. Those include configuration settings for the 'cyware-logcollector' daemon.

    expected_output:
        - r'Monitoring macOS logs with.*'
        - r'Logger message example'
        - r'Custom os_log event message'

    tags:
        - logs
    '''
    expected_macos_message = ""
    log_command = macos_message['command']

    log_monitor.start(timeout=macos_monitoring_macos_log_timeout,
                      callback=logcollector.callback_monitoring_macos_logs,
                      error_message=logcollector.GENERIC_CALLBACK_ERROR_TARGET_SOCKET)

    time.sleep(macos_timeout_process_init)

    if log_command == 'logger':
        logcollector.generate_macos_logger_log(macos_message['message'])
        expected_macos_message = logcollector.format_macos_message_pattern(macos_message['command'],
                                                                           macos_message['message'])

    elif log_command == 'os_log':
        logcollector.generate_macos_custom_log(macos_message['type'], macos_message['level'],
                                               macos_message['subsystem'], macos_message['category'])
        expected_macos_message = logcollector.format_macos_message_pattern('custom_log',
                                                                           logcollector.TEMPLATE_OSLOG_MESSAGE,
                                                                           'log', macos_message['subsystem'],
                                                                           macos_message['category'])

    log_monitor.start(timeout=macos_log_message_timeout,
                      callback=logcollector.callback_macos_log(expected_macos_message),
                      error_message=logcollector.GENERIC_CALLBACK_ERROR_TARGET_SOCKET)
