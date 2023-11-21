'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.
           Created by Cyware, Inc. <info@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
type: integration
brief: Cyware-db is the daemon in charge of the databases with all the Cyware persistent information, exposing a socket
       to receive requests and provide information. The Cyware core uses list-based databases to store information
       related to agent keys, and FIM/Rootcheck event data.
       This test checks the usage of the cywaredb getconfig command used to get the current configuration
tier: 0
modules:
    - cyware_db
components:
    - manager
daemons:
    - cyware-db
os_platform:
    - linux
os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - CentOS 6
    - Ubuntu Focal
    - Ubuntu Bionic
    - Ubuntu Xenial
    - Ubuntu Trusty
    - Debian Buster
    - Debian Stretch
    - Debian Jessie
    - Debian Wheezy
    - Red Hat 8
    - Red Hat 7
    - Red Hat 6
references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/daemons/cyware-db.html
tags:
    - cyware_db
'''
import os
import pytest
import yaml
from cyware_testing.tools import CYWARE_PATH
from cyware_testing.cyware_db import query_wdb
from cyware_testing.tools.file import get_list_of_content_yml

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_file = os.path.join(os.path.join(test_data_path, 'global'), 'cywaredb_getconfig.yaml')
module_tests = get_list_of_content_yml(messages_file)
log_monitor_paths = []
wdb_path = os.path.join(os.path.join(CYWARE_PATH, 'queue', 'db', 'wdb'))
receiver_sockets_params = [(wdb_path, 'AF_UNIX', 'TCP')]
monitored_sockets_params = [('cyware-db', None, True)]
receiver_sockets = None  # Set in the fixtures


# Tests
@pytest.mark.parametrize('test_case',
                         [case['test_case'] for module_data in module_tests for case in module_data[0]],
                         ids=[f"{module_name}: {case['name']}"
                              for module_data, module_name in module_tests
                              for case in module_data]
                         )
def test_sync_agent_groups(configure_sockets_environment, connect_to_sockets_module, test_case):
    '''
    description: Check that commands about cywaredb getconfig works properly.
    cyware_min_version: 4.4.0
    parameters:
        - configure_sockets_environment:
            type: fixture
            brief: Configure environment for sockets and MITM.
        - connect_to_sockets_module:
            type: fixture
            brief: Module scope version of 'connect_to_sockets' fixture.
        - test_case:
            type: fixture
            brief: List of test_case stages (dicts with input, output and agent_id and expected_groups keys).
    assertions:
        - Verify that the socket response matches the expected output.
    input_description:
        - Test cases are defined in the cywaredb_getconfig.yaml file.
    expected_output:
        - an array with the configuration of DB.
    tags:
        - cyware_db
        - wdb_socket
    '''
    # Set each case
    case_data = test_case[0]
    output = case_data["output"]

    response = query_wdb(case_data["input"])

    # Validate response
    assert output in str(response), f"The expected output: {output} was not found in response: {response}"
