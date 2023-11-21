'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: end_to_end

brief: This test will verify that the Slack integeration works correctly. This integration allows reporting alerts
       through messages sent to Slack.

components:
    - logcollector
    - integration

targets:
    - manager

daemons:
    - cyware-logcollector
    - cyware-integratord
    - cyware-analysisd

os_platform:
    - linux

os_version:
    - CentOS 8

references:
    - https://github.com/cyware/cyware-automation/wiki/Cyware-demo:-Execution-guide#slack
    - https://documentation.cyware.khulnasoft.com/current/proof-of-concept-guide/poc-integrate-slack.html
tags:
    - demo
    - slack
    - integration
'''
import os
import json
import re
import pytest
from tempfile import gettempdir

import cyware_testing as fw
from cyware_testing.tools.file import remove_file
from cyware_testing import end_to_end as e2e
from cyware_testing import event_monitor as evm
from cyware_testing.tools import configuration as config
from cyware_testing.modules import TIER0, LINUX


# Test cases data
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_cases_path = os.path.join(test_data_path, 'test_cases')
test_cases_file_path = os.path.join(test_cases_path, 'cases_slack_integration.yaml')
slack_messages_log = os.path.join(gettempdir(), 'slack_messages.log')

# Playbooks
configuration_playbooks = ['configuration.yaml']
events_playbooks = ['generate_events.yaml']
teardown_playbooks = ['teardown.yaml']

# Configuration
configuration, metadata, cases_ids = config.get_test_cases_data(test_cases_file_path)

# Custom paths
slack_api_script = os.path.join(test_data_path, 'configuration', 'slack_api_script.py')

# Update configuration with custom paths
metadata = config.update_configuration_template(metadata, ['CUSTOM_SLACK_SCRIPT_PATH'], [slack_api_script])
configuration_extra_vars = configuration[0]

# Marks
pytestmark = [TIER0, LINUX]


@pytest.fixture(scope='function')
def remove_slack_log():
    """Delete the temporary file containing the Slack messages.
    """
    yield

    remove_file(slack_messages_log)


@pytest.mark.skip(reason='https://github.com/cyware/cyware-qa/issues/3286')
@pytest.mark.parametrize('metadata', metadata, ids=cases_ids)
@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_slack_integration(metadata, configure_environment, get_indexer_credentials, get_manager_ip, generate_events,
                           remove_slack_log, clean_alerts_index):
    '''
    description: Check that an alert is generated and sent to Slack.

    test_phases:
        - Set a custom Cyware configuration.
        - Execute a brute force attack to generate the event.
        - Check in the alerts.json log that the expected alert has been triggered and get its timestamp.
        - Check that the obtained alert from alerts.json has been indexed.
        - Check that the alert was sent to Slack.

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
        - remove_slack_log:
            type: fixture
            brief: Deleted obtained Slack log.
        - clean_alerts_index:
            type: fixture
            brief: Delete obtained alerts.json and alerts index.

    assertions:
        - Verify that the alert has been triggered.
        - Verify that the same alert has been indexed.
        - Verify that the same alert was sent to Slack.

    input_description:
        - The `configuration.yaml` file provides the module configuration for this test.
        - The `generate_events.yaml`file provides the function configuration for this test.
    '''
    rule_description = metadata['rule.description']
    rule_id = metadata['rule.id']
    rule_level = metadata['rule.level']
    extra_srcuser = metadata['extra']['srcuser']
    timestamp_regex = r'\d+-\d+-\d+T\d+:\d+:\d+\.\d+[\+|-]\d+'

    expected_alert_json = fr".+timestamp\":\"({timestamp_regex})\",.+level\":{rule_level}.+description\"" \
                          fr":\"{rule_description}.+id.+{rule_id}.+srcuser.+{extra_srcuser}"

    expected_indexed_alert = fr".+srcuser.+{extra_srcuser}.+level.+{rule_level}.+description.+{rule_description}.+id" \
                             fr".+{rule_id}.+timestamp\": \"({timestamp_regex})\""

    expected_slack_log = fr".*{rule_description}.+{rule_id} _\(Level {rule_level}\)"

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
            "rule.description": f"{rule_description}"
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

    # Check if the alert received in Slack is the same as the triggered one
    evm.check_event(callback=expected_slack_log, file_to_monitor=slack_messages_log,
                    timeout=fw.T_5, error_message='The alert has not reached Slack').result()
