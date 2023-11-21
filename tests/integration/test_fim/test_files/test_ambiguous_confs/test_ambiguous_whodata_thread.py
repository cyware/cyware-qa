'''
copyright: Copyright (C) 2015-2023, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: These tests will check if the 'who-data' feature of the File Integrity Monitoring (FIM)
       system works properly. 'who-data' information contains the user who made the changes
       on the monitored files and also the program name or process used to carry them out.
       The FIM capability is managed by the 'cyware-syscheckd' daemon, which checks
       configured files for changes to the checksums, permissions, and ownership.

components:
    - fim

suite: files_ambiguous_complex

targets:
    - manager

daemons:
    - cyware-syscheckd

os_platform:
    - linux
    - windows

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
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/auditing-whodata/who-linux.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/file-integrity/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/syscheck.html

pytest_args:
    - fim_mode:
        realtime: Enable real-time monitoring on Linux (using the 'inotify' system calls) and Windows systems.
        whodata: Implies real-time monitoring but adding the 'who-data' information.
    - tier:
        0: Only level 0 tests are performed, they check basic functionalities and are quick to perform.
        1: Only level 1 tests are performed, they check functionalities of medium complexity.
        2: Only level 2 tests are performed, they check advanced functionalities and are slow to perform.

tags:
    - fim_ambiguous_confs
'''
import os

import pytest
from cyware_testing import LOG_FILE_PATH, T_30
from cyware_testing.tools import configuration, PREFIX
from cyware_testing.tools.monitoring import FileMonitor
from cyware_testing.modules.fim.event_monitor import detect_whodata_start
from cyware_testing.modules.fim import FIM_DEFAULT_LOCAL_INTERNAL_OPTIONS as local_internal_options


# Marks
pytestmark = [pytest.mark.linux, pytest.mark.win32, pytest.mark.tier(level=2)]

# Variables
test_directories = os.path.join(PREFIX, 'testidr1')

# Configurations
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
CONFIGURATIONS_PATH = os.path.join(TEST_DATA_PATH, 'configuration_templates')
TEST_CASES_PATH = os.path.join(TEST_DATA_PATH, 'test_cases')


# Configuration and cases data
test_cases_path = os.path.join(TEST_CASES_PATH, 'cases_whodata_thread.yaml')
configurations_path = os.path.join(CONFIGURATIONS_PATH, 'configuration_whodata_thread.yaml')

# Test configurations
configuration_parameters, configuration_metadata, test_case_ids = configuration.get_test_cases_data(test_cases_path)
for count, value in enumerate(configuration_parameters):
    configuration_parameters[count]['TEST_DIR1'] = test_directories
    configuration_parameters[count]['TEST_DIR2'] = test_directories
configurations = configuration.load_configuration_template(configurations_path, configuration_parameters,
                                                           configuration_metadata)


# Tests
@pytest.mark.parametrize('configuration, metadata', zip(configurations, configuration_metadata), ids=test_case_ids)
def test_ambiguous_whodata_thread(configuration, metadata, set_cyware_configuration,
                                  configure_local_internal_options_function, restart_syscheck_function):
    '''
    description: Check if the 'cyware-syscheckd' daemon starts the 'whodata' thread when the configuration
                 is ambiguous. For example, when using 'whodata' on the same directory using conflicting
                 values ('yes' and 'no'). For this purpose, the configuration is applied and it checks
                 that the last value detected for 'whodata' in the 'ossec.conf' file is the one used.

    test_phases:
        - setup:
            - Set cyware configuration and local_internal_options.
            - Create custom folder for monitoring
            - Clean logs files and restart cyware to apply the configuration.
        - test:
            - Detect if real-time whodata thread has been started
        - teardown:
            - Delete custom monitored folder
            - Restore configuration
            - Stop cyware

    cyware_min_version: 4.2.0

    tier: 2

    parameters:
        - configuration:
            type: dict
            brief: Configuration values for ossec.conf.
        - metadata:
            type: dict
            brief: Test case data.
        - set_cyware_configuration:
            type: fixture
            brief: Set ossec.conf configuration.
        - configure_local_internal_options_function:
            type: fixture
            brief: Set local_internal_options.conf file.
        - restart_syscheck_function:
            type: fixture
            brief: restart syscheckd daemon, and truncate the ossec.log.

    assertions:
        - Verify that 'whodata' thread is started when the last 'whodata' value detected is set to 'yes'.
        - Verify that 'whodata' thread is not started when the last 'whodata' value detected is set to 'no'.

    input_description: Two test cases are contained in external YAML file (cyware_conf_whodata_thread.yaml)
                       which includes configuration settings for the 'cyware-syscheckd' daemon and testing
                       directories to monitor.

    expected_output:
        - r'File integrity monitoring real-time Whodata engine started'

    tags:
        - who_data
    '''
    cyware_log_monitor = FileMonitor(LOG_FILE_PATH)

    if metadata['whodata_enabled']:
        detect_whodata_start(cyware_log_monitor, timeout=T_30)
    else:
        with pytest.raises(TimeoutError):
            detect_whodata_start(cyware_log_monitor, timeout=T_30)
            raise AttributeError(f'Unexpected event "File integrity monitoring real-time Whodata engine started"')
