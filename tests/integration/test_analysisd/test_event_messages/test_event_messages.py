'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-analysisd' daemon receives the log messages and compares them to the rules.
       It then creates an alert when a log message matches an applicable rule.
       Specifically, these tests will check if the 'cyware-analysisd' daemon correctly handles
       incoming events related to file modification.

components:
    - analysisd

suite: event_messages

targets:
    - manager

daemons:
    - cyware-analysisd
    - cyware-db

os_platform:
    - linux

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - Debian Buster
    - Red Hat 8
    - Ubuntu Focal
    - Ubuntu Bionic

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/daemons/cyware-analysisd.html

tags:
    - events
    - fim
'''
import os

import pytest
import yaml
from cyware_testing import global_parameters
from cyware_testing.analysis import callback_fim_alert, callback_analysisd_message, validate_analysis_alert, \
    callback_cyware_db_message
from cyware_testing.tools import ALERT_FILE_PATH, LOG_FILE_PATH, CYWARE_PATH
from cyware_testing.tools.monitoring import ManInTheMiddle

# Marks

pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configurations

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_path = os.path.join(test_data_path, 'event_messages.yaml')
with open(messages_path) as f:
    test_cases = yaml.safe_load(f)

# Variables

log_monitor_paths = [LOG_FILE_PATH, ALERT_FILE_PATH]
wdb_path = os.path.join(os.path.join(CYWARE_PATH, 'queue', 'db', 'wdb'))
analysis_path = os.path.join(os.path.join(CYWARE_PATH, 'queue', 'sockets', 'queue'))

receiver_sockets_params = [(analysis_path, 'AF_UNIX', 'UDP')]

mitm_wdb = ManInTheMiddle(address=wdb_path, family='AF_UNIX', connection_protocol='TCP')
mitm_analysisd = ManInTheMiddle(address=analysis_path, family='AF_UNIX', connection_protocol='UDP')
# monitored_sockets_params is a List of daemons to start with optional ManInTheMiddle to monitor
# List items -> (cyware_daemon: str,(
#                mitm: ManInTheMiddle
#                daemon_first: bool))
# Example1 -> ('cyware-clusterd', None)              Only start cyware-clusterd with no MITM
# Example2 -> ('cyware-clusterd', (my_mitm, True))   Start MITM and then cyware-clusterd
monitored_sockets_params = [('cyware-db', mitm_wdb, True), ('cyware-analysisd', mitm_analysisd, True)]

receiver_sockets, monitored_sockets, log_monitors = None, None, None  # Set in the fixtures


# Tests

@pytest.mark.parametrize('test_case',
                         [test_case['test_case'] for test_case in test_cases],
                         ids=[test_case['name'] for test_case in test_cases])
def test_event_messages(configure_sockets_environment, connect_to_sockets_module, wait_for_analysisd_startup,
                        test_case: list):
    '''
    description: Check if when the 'cyware-analysisd' daemon socket receives a message with
                 a file modification-related event, it generates the corresponding alert
                 that sends to the 'cyware-db' daemon socket.
                 The 'validate_analysis_alert' function checks if an 'analysisd' event
                 is properly formatted.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - configure_sockets_environment:
            type: fixture
            brief: Configure environment for sockets and MITM.
        - connect_to_sockets_module:
            type: fixture
            brief: Module scope version of 'connect_to_sockets' fixture.
        - wait_for_analysisd_startup:
            type: fixture
            brief: Wait until the 'cyware-analysisd' has begun and the 'alerts.json' file is created.
        - test_case:
            type: list
            brief: List of tests to be performed.

    assertions:
        - Verify that the alerts generated are consistent with the events received.

    input_description: Different test cases that are contained in an external YAML file (event_messages.yaml)
                       that includes 'syscheck' events data and the expected output.

    expected_output:
        - Multiple messages (alert logs) corresponding to each test case,
          located in the external input data file.

    tags:
        - alerts
        - man_in_the_middle
        - wdb_socket
    '''
    for stage in test_case:
        expected = callback_analysisd_message(stage['output'])
        receiver_sockets[0].send(stage['input'])
        response = monitored_sockets[0].start(timeout=global_parameters.default_timeout,
                                              callback=callback_cyware_db_message).result()
        assert response == expected, 'Failed test case stage {}: {}'.format(test_case.index(stage) + 1, stage['stage'])
        alert = log_monitors[1].start(timeout=global_parameters.default_timeout,
                                      callback=callback_fim_alert).result()
        validate_analysis_alert(alert)
