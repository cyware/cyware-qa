'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: end_to_end

brief: This test will verify that the anomaly and malware detection works correctly. Anomaly detection refers to the
       action of finding patterns in the system that do not match the expected behavior. Once malware (e.g., a rootkit)
       is installed on a system, it modifies the system to hide itself from the user. Although malware uses a variety of
       techniques to accomplish this, Cyware uses a broad spectrum approach to finding anomalous patterns that indicate
       possible intruders.

components:
    - rootcheck

targets:
    - manager

daemons:
    - cyware-syscheckd
    - cyware-analysisd

os_platform:
    - linux

os_version:
    - CentOS 8

references:
    - https://github.com/cyware/cyware-automation/wiki/Cyware-demo:-Execution-guide#trojan
    - https://documentation.cyware.khulnasoft.com/current/proof-of-concept-guide/poc-detect-trojan.html

tags:
    - demo
    - rootcheck
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

# Test cases data
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_cases_path = os.path.join(test_data_path, 'test_cases')
test_cases_file_path = os.path.join(test_cases_path, 'cases_detecting_suspicious_binaries.yaml')
trojan_script_path = os.path.join(test_data_path, 'configuration', 'trojan_script.sh')

# Playbooks
configuration_playbooks = ['configuration.yaml']
events_playbooks = ['generate_events.yaml']
teardown_playbooks = ['teardown.yaml']
configuration_extra_vars = {'trojan_script_path': trojan_script_path}

# Configuration
configurations, configuration_metadata, cases_ids = config.get_test_cases_data(test_cases_file_path)

# Marks
pytestmark = [TIER0, LINUX]


@pytest.mark.parametrize('metadata', configuration_metadata, ids=cases_ids)
@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_detecting_suspicious_binaries(configure_environment, metadata, get_indexer_credentials, get_manager_ip,
                                       generate_events, clean_alerts_index):
    '''
    description: Check that an alert is generated and indexed when there is a trojaned system binary.

    test_phases:
        - Set a custom Cyware configuration.
        - Replace the content of a system binary to generate event.
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
    rule_description = metadata['rule.description']
    rule_id = metadata['rule.id']
    rule_level = metadata['rule.level']
    data_title = metadata['extra']['data.title']
    data_file = metadata['extra']['data.file']
    timestamp_regex = r'\d+-\d+-\d+T\d+:\d+:\d+\.\d+[\+|-]\d+'

    expected_alert_json = fr".+timestamp\":\"({timestamp_regex})\",.+level\":{rule_level}.+description\"" \
                          fr":\"{rule_description}.+id.+{rule_id}.+title.+{data_title}.+file.+{data_file}"

    expected_indexed_alert = fr".+file.+{data_file}.+title.+{data_title}.+level.+{rule_level}.+" \
                             fr"description.+{rule_description}.+id.+{rule_id}.+timestamp\": \"({timestamp_regex})\""

    # Check that alert has been raised and save timestamp
    raised_alert = evm.check_event(callback=expected_alert_json, file_to_monitor=e2e.fetched_alerts_json_path,
                                   timeout=fw.T_5, error_message='The alert has not occurred').result()
    raised_alert_timestamp = raised_alert.group(1)

    query = e2e.make_query([
        {
          "term": {
            "data.file": f"{data_file}"
          }
        },
        {
          "term": {
            "rule.id": f"{rule_id}"
          }
        },
        {
          "term": {
            "data.title": f"{data_title}"
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
