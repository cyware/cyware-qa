# Copyright (C) 2015-2022, KhulnaSoft Ltd.
# Created by Cyware, Inc. <info@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import os

import pytest
from cyware_testing.tools import CYWARE_PATH, CYWARE_LOGS_PATH
from cyware_testing.tools.monitoring import HostMonitor
from cyware_testing.tools.system import HostManager


pytestmark = [pytest.mark.cluster, pytest.mark.enrollment_cluster_env]

# Hosts
testinfra_hosts = ["cyware-master", "cyware-worker1", "cyware-agent1"]

inventory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                              'provisioning', 'enrollment_cluster', 'inventory.yml')
host_manager = HostManager(inventory_path)
local_path = os.path.dirname(os.path.abspath(__file__))
messages_path = os.path.join(local_path, 'data/messages.yml')
tmp_path = os.path.join(local_path, 'tmp')


# Remove the agent once the test has finished
@pytest.fixture(scope='module')
def clean_environment():
    yield
    agent_id = host_manager.run_command('cyware-master', f'cut -c 1-3 {CYWARE_PATH}/etc/client.keys')
    host_manager.get_host('cyware-master').ansible("command", f'{CYWARE_PATH}/bin/manage_agents -r {agent_id}',
                                                  check=False)
    host_manager.control_service(host='cyware-agent1', service='cyware', state="stopped")
    host_manager.clear_file(host='cyware-agent1', file_path=os.path.join(CYWARE_PATH, 'etc', 'client.keys'))
    host_manager.clear_file(host='cyware-agent1', file_path=os.path.join(CYWARE_LOGS_PATH, 'ossec.log'))


def test_agent_enrollment(clean_environment):
    """Check agent enrollment process works as expected. An agent pointing to a worker should be able to register itself
    into the master by starting Cyware-agent process."""
    # Clean ossec.log and cluster.log
    host_manager.clear_file(host='cyware-master', file_path=os.path.join(CYWARE_LOGS_PATH, 'ossec.log'))
    host_manager.clear_file(host='cyware-worker1', file_path=os.path.join(CYWARE_LOGS_PATH, 'ossec.log'))
    host_manager.clear_file(host='cyware-master', file_path=os.path.join(CYWARE_LOGS_PATH, 'cluster.log'))
    host_manager.clear_file(host='cyware-worker1', file_path=os.path.join(CYWARE_LOGS_PATH, 'cluster.log'))

    # Start the agent enrollment process by restarting the cyware-agent
    host_manager.control_service(host='cyware-master', service='cyware', state="restarted")
    host_manager.control_service(host='cyware-worker1', service='cyware', state="restarted")
    host_manager.get_host('cyware-agent1').ansible('command', f'service cyware-agent restart', check=False)

    # Run the callback checks for the ossec.log and the cluster.log
    HostMonitor(inventory_path=inventory_path,
                messages_path=messages_path,
                tmp_path=tmp_path).run()

    # Make sure the worker's client.keys is not empty
    assert host_manager.get_file_content('cyware-worker1', os.path.join(CYWARE_PATH, 'etc', 'client.keys'))

    # Make sure the agent's client.keys is not empty
    assert host_manager.get_file_content('cyware-agent1', os.path.join(CYWARE_PATH, 'etc', 'client.keys'))

    # Check if the agent is active
    agent_id = host_manager.run_command('cyware-master', f'cut -c 1-3 {CYWARE_PATH}/etc/client.keys')
    assert host_manager.run_command('cyware-master', f'{CYWARE_PATH}/bin/agent_control -i {agent_id} | grep Active')
