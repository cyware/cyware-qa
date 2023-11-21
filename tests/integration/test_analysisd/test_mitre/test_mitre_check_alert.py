'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-analysisd' daemon receives the log messages and compares them to the rules.
       It then creates an alert when a log message matches an applicable rule.
       Specifically, these tests will check if the 'cyware-analysisd' daemon generates alerts
       using custom rules that contains the 'mitre' field to enrich those alerts with
       MITREs IDs, techniques and tactics.

components:
    - analysisd

suite: mitre

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
    - https://attack.mitre.org/

tags:
    - events
    - mitre
'''
import os

import jsonschema
import pytest
from cyware_testing.mitre import (callback_detect_mitre_event, validate_mitre_event)
from cyware_testing.tools import ALERT_FILE_PATH
from cyware_testing.tools.monitoring import FileMonitor

# Marks

pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# variables

cyware_alert_monitor = FileMonitor(ALERT_FILE_PATH)
_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

invalid_configurations = []

configurations = []
for i in range(1, 15):
    file_test = os.path.join(_data_path, f"test{i}.xml")
    configurations.append(file_test)
    if i in range(5, 9):
        invalid_configurations.append(file_test)


# fixtures

@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# tests

def test_mitre_check_alert(get_configuration, configure_local_rules, restart_cyware_alerts):
    '''
    description: Check if MITRE alerts are syntactically and semantically correct.
                 For this purpose, customized rules with MITRE fields are inserted,
                 so that the alerts generated include this information which
                 will be finally validated.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_local_rules:
            type: fixture
            brief: Configure a custom rule in 'local_rules.xml' for testing.
        - restart_cyware_alerts:
            type: fixture
            brief: Reset 'alerts.json' and start a new monitor.

    assertions:
        - Verify that the MITRE alerts are generated and are correct.

    input_description: Different test cases that are contained in an external XML files ('data' directory)
                       that include both valid and invalid rules for detecting MITRE events.

    expected_output:
        - Multiple messages (mitre alert logs) corresponding to each test case,
          located in the external input data file.

    tags:
        - alerts
        - man_in_the_middle
        - wdb_socket
    '''
    # Wait until Mitre's event is detected
    if get_configuration not in invalid_configurations:
        event = cyware_alert_monitor.start(timeout=30, callback=callback_detect_mitre_event).result()
        validate_mitre_event(event)
    else:
        with pytest.raises(jsonschema.exceptions.ValidationError):
            event = cyware_alert_monitor.start(timeout=30, callback=callback_detect_mitre_event).result()
            validate_mitre_event(event)
