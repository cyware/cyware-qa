'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: end_to_end

brief: This test will verify that the integration with audit is working correctly.
       Audit logging is used to capture and log execve system calls.

components:
    - logcollector

targets:
    - manager

daemons:
    - cyware-logcollector
    - cyware-analysisd

os_platform:
    - linux

os_version:
    - CentOS 8

references:
    - https://github.com/cyware/cyware-automation/wiki/Cyware-demo:-Execution-guide#audit
    - https://documentation.cyware.khulnasoft.com/current/proof-of-concept-guide/audit-commands-run-by-user.html
    - https://documentation.cyware.khulnasoft.com/current/learning-cyware/audit-commands.html#learning-cyware-audit-commands

tags:
    - demo
    - auditd
    - audit_rules
'''
import os
import json
import re
import pytest

import cyware_testing as fw
from cyware_testing import end_to_end as e2e
from cyware_testing import event_monitor as evm
from cyware_testing.tools import configuration as config
from cyware_testing.modules import TIER0, LINUX


test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_cases_file_path = os.path.join(test_data_path, 'test_cases', 'cases_audit.yaml')
configuration_playbooks = ['configuration.yaml']
events_playbooks = ['generate_events.yaml']
teardown_playbooks = ['teardown.yaml']

configurations, configuration_metadata, cases_ids = config.get_test_cases_data(test_cases_file_path)

# Marks
pytestmark = [TIER0, LINUX]


@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
@pytest.mark.parametrize('metadata', configuration_metadata, ids=cases_ids)
def test_audit(configure_environment, metadata, get_indexer_credentials, get_manager_ip, generate_events,
               clean_alerts_index):
    '''
    description: Check that an alert is generated and indexed when a command is executed.

    test_phases:
        - Set a custom Cyware configuration.
        - Run ping command to generate event.
        - Check in the alerts.json log that the expected alert has been triggered and get its timestamp.
        - Check that the obtained alert from alerts.json has been indexed.

    cyware_min_version: 4.4.0

    tier: 0

    parameters:
        - configurate_environment:
            type: fixture
            brief: Set the cyware configuration according to the configuration playbook.
        - metadata:
            type: dict
            brief: Cyware configuration metadata.
        - get_indexer_credentials:
            type: fixture
            brief: Get the cyware indexer credentials.
        - generate_events:
            type: fixture
            brief: Generate events that will trigger the alert according to the generate_events playbook.
        - clean_alerts_index:
            type: fixture
            brief: Delete obtained alerts.json and alerts index.

    assertions:
        - Verify that the alert has been triggered.
        - Verify that the same alert has been indexed.

    input_description:
        - The `configuration.yaml` file provides the module configuration for this test.
        - The `generate_events.yaml`file provides the function configuration for this test.
    '''
    level = metadata['level']
    description = metadata['description']
    rule_id = metadata['rule.id']
    a3 = metadata['extra']['a3']
    data_audit_command = metadata['extra']['data.audit.command']
    timestamp_regex = r'\d+-\d+-\d+T\d+:\d+:\d+\.\d+[\+|-]\d+'

    expected_alert_json = fr'\{{"timestamp":"({timestamp_regex})","rule"\:{{"level"\:{level},' \
                          fr'"description"\:"{description}","id"\:"{rule_id}".*a3={a3}.*\}}'
    expected_indexed_alert = fr'.*"rule":.*"level": {level}, "description": "{description}".*"id": "{rule_id}".*' \
                             fr'comm=\\"{data_audit_command}\\".*a3={a3}.*' \
                             fr'"timestamp": "({timestamp_regex})".*'

    # Check that alert has been raised and save timestamp
    raised_alert = evm.check_event(callback=expected_alert_json, file_to_monitor=e2e.fetched_alerts_json_path,
                                   timeout=fw.T_5, error_message='The alert has not occurred').result()
    raised_alert_timestamp = raised_alert.group(1)

    query = e2e.make_query([
        {
           "term": {
              "rule.id": f"{rule_id}"
           }
        },
        {
           "term": {
              "data.audit.command": f"{data_audit_command}"
           }
        },
        {
           "term": {
              "timestamp": f"{raised_alert_timestamp}"
           }
        }
    ])

    # Check if the alert has been indexed and get its data
    response = e2e.get_alert_indexer_api(query=query, credentials=get_indexer_credentials, ip_address=get_manager_ip)
    indexed_alert = json.dumps(response.json())

    # Check that the alert data is the expected one
    alert_data = re.search(expected_indexed_alert, indexed_alert)
    assert alert_data is not None, 'Alert triggered, but not indexed'
