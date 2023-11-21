'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-analysisd' daemon receives the log messages and compares them to the rules.
       It then creates an alert when a log message matches an applicable rule.
       Specifically, these tests will verify if the 'cyware-analysisd' daemon generates valid
       alerts from Linux 'syscheck' events.

components:
    - analysisd

suite: all_syscheckd_configurations

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
'''
import os

import pytest
import yaml
from cyware_testing.analysis import validate_analysis_alert_complex
from cyware_testing.tools import CYWARE_PATH, LOG_FILE_PATH, ALERT_FILE_PATH
from cyware_testing.tools.monitoring import ManInTheMiddle

# Marks

pytestmark = [pytest.mark.linux, pytest.mark.tier(level=2), pytest.mark.server]

# Configurations

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_path = os.path.join(test_data_path, 'syscheck_events.yaml')
with open(messages_path) as f:
    test_cases = yaml.safe_load(f)

# Variables

log_monitor_paths = [LOG_FILE_PATH, ALERT_FILE_PATH]
analysis_path = os.path.join(os.path.join(CYWARE_PATH, 'queue', 'sockets', 'queue'))

receiver_sockets_params = [(analysis_path, 'AF_UNIX', 'UDP')]

mitm_analysisd = ManInTheMiddle(address=analysis_path, family='AF_UNIX', connection_protocol='UDP')
# monitored_sockets_params is a List of daemons to start with optional ManInTheMiddle to monitor
# List items -> (cyware_daemon: str,(
#                mitm: ManInTheMiddle
#                daemon_first: bool))
# Example1 -> ('cyware-clusterd', None)              Only start cyware-clusterd with no MITM
# Example2 -> ('cyware-clusterd', (my_mitm, True))   Start MITM and then cyware-clusterd
monitored_sockets_params = [('cyware-db', None, None), ('cyware-analysisd', mitm_analysisd, True)]

receiver_sockets, monitored_sockets, log_monitors = None, None, None  # Set in the fixtures

events_dict = {}
alerts_list = []
analysisd_injections_per_second = 200


# Fixtures


@pytest.fixture(scope='module', params=range(len(test_cases)))
def get_alert(request):
    return alerts_list[request.param]


# Tests


def test_validate_all_linux_alerts(configure_sockets_environment, connect_to_sockets_module, wait_for_analysisd_startup,
                                   generate_events_and_alerts, get_alert):
    '''
    description: Check if the alerts generated by the 'cyware-analysisd' daemon from
                 Linux 'syscheck' events are valid. The 'validate_analysis_alert_complex'
                 function checks if an 'analysisd' alert is properly formatted in
                 reference to its 'syscheck' event.

    cyware_min_version: 4.2.0

    tier: 2

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
        - generate_events_and_alerts:
            type: fixture
            brief: Read the specified YAML and generate every event and alert using the input from every test case.
        - get_alert:
            type: fixture
            brief: List of alerts to be validated.

    assertions:
        - Verify that the alerts generated are consistent with the events received.

    input_description: Different test cases that are contained in an external YAML file (syscheck_events.yaml)
                       that includes 'syscheck' events data and the expected output.

    inputs:
        - 12280 test cases distributed among 'syscheck' events of type 'added', 'modified', and 'deleted'.

    expected_output:
        - Multiple messages (alert logs) corresponding to each test case,
          located in the external input data file.

    tags:
        - alerts
        - man_in_the_middle
        - wdb_socket
    '''
    alert = get_alert
    path = alert['syscheck']['path']
    mode = alert['syscheck']['event'].title()
    validate_analysis_alert_complex(alert, events_dict[path][mode])
