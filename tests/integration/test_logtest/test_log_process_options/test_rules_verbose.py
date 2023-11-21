'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logtest' tool allows the testing and verification of rules and decoders against provided log examples
       remotely inside a sandbox in 'cyware-analysisd'. This functionality is provided by the manager, whose work
       parameters are configured in the ossec.conf file in the XML rule_test section. Test logs can be evaluated through
       the 'cyware-logtest' tool or by making requests via RESTful API. These tests will check if the logtest
       configuration is valid. Also checks rules, decoders, decoders, alerts matching logs correctly.

components:
    - logtest

suite: log_process_option

targets:
    - manager

daemons:
    - cyware-analysisd

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
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/tools/cyware-logtest.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/cyware-logtest/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/daemons/cyware-analysisd.html

tags:
    - logtest_configuration
'''
import json
import os
import shutil
import re

import pytest
import yaml
from cyware_testing.tools import (CYWARE_PATH, LOGTEST_SOCKET_PATH,
                                 CYWARE_UNIX_USER, LOG_FILE_PATH,
                                 LOCAL_RULES_PATH, CYWARE_UNIX_GROUP)
from cyware_testing.logtest import callback_logtest_started
from cyware_testing.tools.services import control_service
from cyware_testing.tools.monitoring import FileMonitor
from cyware_testing.tools.file import truncate_file


# Marks
pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/')
messages_path = os.path.join(test_data_path, 'rules_verbose.yaml')
logtest_startup_timeout = 30

with open(messages_path) as f:
    test_cases = yaml.safe_load(f)

# Variables
receiver_sockets_params = [(LOGTEST_SOCKET_PATH, 'AF_UNIX', 'TCP')]
receiver_sockets = None

local_rules_debug_messages = ['Trying rule: 880000 - Parent rules verbose', '*Rule 880000 matched',
                              '*Trying child rules', 'Trying rule: 880001 - test last_match', '*Rule 880001 matched',
                              '*Trying child rules', 'Trying rule: 880002 - test_child test_child']


# Fixtures
@pytest.fixture(scope='function')
def configure_rules_list(get_configuration, request):
    """Configure a custom rules for testing.

    Restart Cyware is not needed for applying the configuration, is optional.
    """

    # save current rules
    shutil.copy(LOCAL_RULES_PATH, LOCAL_RULES_PATH + '.cpy')

    file_test = get_configuration['rule_file']
    # copy test rules
    shutil.copy(test_data_path + file_test, LOCAL_RULES_PATH)
    shutil.chown(LOCAL_RULES_PATH, CYWARE_UNIX_USER, CYWARE_UNIX_GROUP)

    yield

    # restore previous configuration
    shutil.move(LOCAL_RULES_PATH + '.cpy', LOCAL_RULES_PATH)
    shutil.chown(LOCAL_RULES_PATH, CYWARE_UNIX_USER, CYWARE_UNIX_GROUP)


@pytest.fixture(scope='module', params=test_cases, ids=[test_case['name'] for test_case in test_cases])
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.fixture(scope='module')
def wait_for_logtest_startup(request):
    """Wait until logtest has begun."""
    log_monitor = FileMonitor(LOG_FILE_PATH)
    log_monitor.start(timeout=logtest_startup_timeout, callback=callback_logtest_started)


@pytest.fixture(scope='module')
def restart_required_logtest_daemons():
    """Cyware logtests daemons handler."""
    required_logtest_daemons = ['cyware-analysisd']

    truncate_file(LOG_FILE_PATH)

    for daemon in required_logtest_daemons:
        control_service('restart', daemon=daemon)

    yield

    for daemon in required_logtest_daemons:
        control_service('stop', daemon=daemon)


# Tests
def test_rules_verbose(get_configuration, restart_required_logtest_daemons,
                       configure_rules_list, wait_for_logtest_startup,
                       connect_to_sockets_function):
    '''
    description: Check if 'cyware-logtest' works correctly in 'verbose' mode for rules debugging. To do this, it sends
                 the inputs through a socket, receives and decodes the message. Then, it checks
                 if any invalid token or session token is not caught.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configuration from the module.
        - restart_required_logtest_daemons:
            type: fixture
            brief: Cyware logtests daemons handler.
        - configure_rules_list:
            type: fixture
            brief: Configure a custom rules for testing. Restart Cyware is not needed for applying the configuration
                   is optional.
        - wait_for_logtest_startup:
            type: fixture
            brief: Wait until logtest has begun.
        - connect_to_sockets_function:
            type: fixture
            brief: Function scope version of 'connect_to_sockets' which connects to the specified sockets for the test.

    assertions:
        - Verify that the logtest reply message has no run error.
        - Verify that the 'rule_id' within the reply message is correct.
        - Verify that logtest is running in verbose mode.
        - Verify that when running in verbose mode the local rule debug messages has been written
        - Verify that when running in verbose mode the local rule debug messages written are the expected count.
        - Verify that if a warning message is caught it matches with any test case message.

    input_description: Some test cases are defined in the module. These include some input configurations stored in
                       the 'rules_verbose.yaml'.

    expected_output:
        - 'The rules_debug field was not found in the response data'
        - 'The warning message was not found in the response data'
        - 'Error when executing .* in daemon .*. Exit status: .*'

    tags:
        - settings
        - analysisd
    '''
    # send the logtest request
    receiver_sockets[0].send(get_configuration['input'], size=True)

    # receive logtest reply and parse it
    response = receiver_sockets[0].receive(size=True).rstrip(b'\x00').decode()
    result = json.loads(response)

    assert result['error'] == 0
    assert result['data']['output']['rule']['id'] == get_configuration['rule_id']

    if 'verbose_mode' in get_configuration and get_configuration['verbose_mode']:
        if 'rules_debug' in result['data']:
            assert result['data']['rules_debug'][-len(local_rules_debug_messages):] == local_rules_debug_messages
        else:
            assert False, 'The rules_debug field was not found in the response data'

    else:
        assert 'rules_debug' not in result['data']

    if 'warning_message' in get_configuration:
        r = re.compile(get_configuration['warning_message'])
        match_list = list(filter(r.match, result['data']['messages']))
        assert match_list, 'The warning message was not found in the response data'
