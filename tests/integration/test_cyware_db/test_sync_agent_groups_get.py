'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.
           Created by Cyware, Inc. <info@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
type: integration
brief: Cyware-db is the daemon in charge of the databases with all the Cyware persistent information, exposing a socket
       to receive requests and provide information. The Cyware core uses list-based databases to store information
       related to agent keys, and FIM/Rootcheck event data.
       This test checks the usage of the sync-agent-groups-get command used to allow the cluster getting the
       information to be synchronized..
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
import time
import pytest
import json

from cyware_testing.tools import CYWARE_PATH
from cyware_testing.cyware_db import query_wdb, insert_agent_into_group, clean_agents_from_db
from cyware_testing.cyware_db import clean_groups_from_db, clean_belongs, calculate_global_hash
from cyware_testing.modules import TIER0, SERVER, LINUX
from cyware_testing.tools.file import get_list_of_content_yml
from cyware_testing.tools.services import delete_dbs


# Marks
pytestmark = [LINUX, TIER0, SERVER]

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_file = os.path.join(os.path.join(test_data_path, 'global'), 'sync_agent_groups_get.yaml')
module_tests = get_list_of_content_yml(messages_file)

log_monitor_paths = []
wdb_path = os.path.join(os.path.join(CYWARE_PATH, 'queue', 'db', 'wdb'))
receiver_sockets_params = [(wdb_path, 'AF_UNIX', 'TCP')]
monitored_sockets_params = [('cyware-db', None, True)]
receiver_sockets = None  # Set in the fixtures


# Fixtures

# Insert agents into DB  and assign them into a group
@pytest.fixture(scope='function')
def pre_insert_agents_into_group():

    insert_agent_into_group(2)

    yield

    clean_agents_from_db()
    clean_groups_from_db()
    clean_belongs()


@pytest.fixture(scope='module')
def clean_databases():
    yield
    delete_dbs()


# Tests
@pytest.mark.parametrize('test_case',
                         [case['test_case'] for module_data in module_tests for case in module_data[0]],
                         ids=[f"{module_name}: {case['name']}"
                              for module_data, module_name in module_tests
                              for case in module_data]
                         )
def test_sync_agent_groups(restart_cyware_daemon, test_case, create_groups, pre_insert_agents_into_group,
                           clean_databases):
    '''
    description: Check that commands about sync_aget_groups_get works properly.
    cyware_min_version: 4.4.0
    parameters:
        - restart_cyware_daemon:
            type: fixture
            brief: Truncate ossec.log and restart Cyware.
        - test_case:
            type: fixture
            brief: List of test_case stages (dicts with input, output and agent_id and expected_groups keys).
        - pre_insert_agents_into_group:
            type: fixture
            brief: fixture in charge of insert agents and groups into DB.
        - clean_databases:
            type: fixture
            brief: Delete all databases after test execution.
    assertions:
        - Verify that the socket response matches the expected output.
    input_description:
        - Test cases are defined in the sync_agent_groups_get.yaml file.
    expected_output:
        - an array with all the agents that match with the search criteria
    tags:
        - cyware_db
        - wdb_socket
    '''
    # Set each case
    output = test_case["output"]

    # Check if it requires any special configuration
    if 'pre_input' in test_case:
        for command in test_case['pre_input']:
            query_wdb(command)

    # Check if it requires the global hash.
    if '[GLOBAL_HASH]' in output:
        global_hash = calculate_global_hash()
        output = output.replace('[GLOBAL_HASH]', global_hash)

    time.sleep(1)
    response = query_wdb(test_case["input"])

    # Validate response
    assert str(response) == output, "Did not get expected response: {output}, recieved: {response}"

    # Validate if the status of the group has change
    if "new_status" in test_case:
        agent_id = json.loads(test_case["agent_id"])
        for id in agent_id:
            response = query_wdb(f'global get-agent-info {id}')
            assert test_case["new_status"] == response[0]['group_sync_status']
