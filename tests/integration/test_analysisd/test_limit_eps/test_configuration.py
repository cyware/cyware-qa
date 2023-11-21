import os
import pytest

from cyware_testing.tools.configuration import load_configuration_template, get_test_cases_data
from cyware_testing.modules.analysisd import event_monitor as evm
from cyware_testing.tools.services import control_service
from cyware_testing.processes import check_if_daemons_are_running
from cyware_testing.tools import file
from cyware_testing import CYWARE_CONF_PATH

# Reference paths
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
CONFIGURATIONS_PATH = os.path.join(TEST_DATA_PATH, 'configuration_template', 'configuration_test_module')
TEST_CASES_PATH = os.path.join(TEST_DATA_PATH, 'test_cases', 'configuration_test_module')
local_internal_options = {'cyware_modules.debug': '2', 'monitord.rotate_log': '0'}

# ------------------------------------------------ TEST_ACCEPTED_VALUES ------------------------------------------------
# Configuration and cases data
t1_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'configuration_accepted_values.yaml')
t1_cases_path = os.path.join(TEST_CASES_PATH, 'cases_accepted_values.yaml')

# Accepted values test configurations (t1)
t1_configuration_parameters, t1_configuration_metadata, t1_case_ids = get_test_cases_data(t1_cases_path)
t1_configurations = load_configuration_template(t1_configurations_path, t1_configuration_parameters,
                                                t1_configuration_metadata)

# ------------------------------------------------- TEST_INVALID_VALUES ------------------------------------------------
# Configuration and cases data
t2_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'configuration_invalid_values.yaml')
t2_cases_path = os.path.join(TEST_CASES_PATH, 'cases_invalid_values.yaml')

# Invalid values test configurations (t2)
t2_configuration_parameters, t2_configuration_metadata, t2_case_ids = get_test_cases_data(t2_cases_path)
t2_configurations = load_configuration_template(t2_configurations_path, t2_configuration_parameters,
                                                t2_configuration_metadata)

# --------------------------------------------- TEST_MISSING_CONFIGURATION ---------------------------------------------
# Configuration and cases data
t3_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'configuration_missing_configuration.yaml')
t3_cases_path = os.path.join(TEST_CASES_PATH, 'cases_missing_configuration.yaml')

# Invalid values test configurations (t2)
t3_configuration_parameters, t3_configuration_metadata, t3_case_ids = get_test_cases_data(t3_cases_path)
t3_configurations = load_configuration_template(t3_configurations_path, t3_configuration_parameters,
                                                t3_configuration_metadata)


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(t1_configurations, t1_configuration_metadata), ids=t1_case_ids)
def test_accepted_values(configuration, metadata, load_cyware_basic_configuration, set_cyware_configuration,
                         configure_local_internal_options_module, truncate_monitored_files,
                         restart_cyware_daemon_function):
    """
    description: Check that the EPS limitation is activated under accepted parameters.

    test_phases:
        - setup:
            - Load Cyware light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate cyware logs.
            - Restart cyware-manager service to apply configuration changes.
        - test:
            - Check in the log that the EPS limitation has been activated with the specified parameters.
            - Check that cyware-analysisd is running (it has not been crashed).
        - teardown:
            - Truncate cyware logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.

    cyware_min_version: 4.4.0

    parameters:
        - configuration:
            type: dict
            brief: Get configurations from the module.
        - metadata:
            type: dict
            brief: Get metadata from the module.
        - load_cyware_basic_configuration:
            type: fixture
            brief: Load basic cyware configuration.
        - set_cyware_configuration:
            type: fixture
            brief: Apply changes to the ossec.conf configuration.
        - configure_local_internal_options_function:
            type: fixture
            brief: Apply changes to the local_internal_options.conf configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate cyware logs.
        - restart_cyware_daemon_function:
            type: fixture
            brief: Restart the cyware service.

    assertions:
        - Check in the log that the EPS limitation has been activated with the specified parameters.
        - Check that cyware-analysisd daemon does not crash.

    input_description:
        - The `configuration_accepted_values` file provides the module configuration for this test.
        - The `cases_accepted_values` file provides the test cases.
    """
    evm.check_eps_enabled(metadata['maximum'], metadata['timeframe'])

    # Check that cyware-analysisd is running
    assert check_if_daemons_are_running(['cyware-analysisd'])[0], 'cyware-analysisd is not running. Maybe it has crashed'


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(t2_configurations, t2_configuration_metadata), ids=t2_case_ids)
def test_invalid_values(configuration, metadata, restart_cyware_daemon_after_finishing_function,
                        load_cyware_basic_configuration, set_cyware_configuration,
                        configure_local_internal_options_module, truncate_monitored_files):
    """
    description: Check for configuration error and cyware-analysisd if the EPS limiting configuration has unaccepted
        values. Done for the following cases:
            - Maximum value above the allowed value.
            - Timeframe value above the allowed value.
            - Timeframe = 0
            - Maximum, timeframe = 0

    test_phases:
        - setup:
            - Load Cyware light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate cyware logs.
        - test:
            - Restart cyware-manager service to apply configuration changes.
            - Check that a configuration error is raised when trying to start cyware-manager.
            - Check that cyware-analysisd is not running (due to configuration error).
        - teardown:
            - Truncate cyware logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
            - Restart the cyware-manager service to apply initial configuration and start cyware-analysisd daemon.

    cyware_min_version: 4.4.0

    parameters:
        - configuration:
            type: dict
            brief: Get configurations from the module.
        - metadata:
            type: dict
            brief: Get metadata from the module.
        - restart_cyware_daemon_after_finishing_function:
            type: fixture
            brief: Restart the cyware service in teardown stage.
        - load_cyware_basic_configuration:
            type: fixture
            brief: Load basic cyware configuration.
        - set_cyware_configuration:
            type: fixture
            brief: Apply changes to the ossec.conf configuration.
        - configure_local_internal_options_function:
            type: fixture
            brief: Apply changes to the local_internal_options.conf configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate cyware logs.

    assertions:
        - Check that a configuration error is raised when trying to start cyware-manager.
        - Check that cyware-analysisd is not running (due to configuration error).

    input_description:
        - The `configuration_invalid_values` file provides the module configuration for this test.
        - The `cases_invalid_values` file provides the test cases.
    """
    try:
        control_service('restart')
    except ValueError:
        pass
    finally:
        evm.check_configuration_error()
        # Check that cyware-analysisd is not running
        assert not check_if_daemons_are_running(['cyware-analysisd'])[0], 'cyware-analysisd is running and was not ' \
                                                                         'expected to'


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(t3_configurations, t3_configuration_metadata), ids=t3_case_ids)
def test_missing_configuration(configuration, metadata, restart_cyware_daemon_after_finishing_function,
                               load_cyware_basic_configuration, set_cyware_configuration, truncate_monitored_files):
    """
    description: Checks what happens if tags are missing in the event analysis limitation settings. Done for the
        following cases:
            - Missing <timeframe>.
            - Missing <maximum>.
            - Missing <timeframe> and <maximum>.

    test_phases:
        - setup:
            - Load Cyware light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate cyware logs.
        - test:
            - Remove the specified tag in ossec.conf
            - Restart cyware-manager service to apply configuration changes.
            - Check whether the EPS limitation is activated, deactivated or generates a configuration error due to a
              missing label.
            - Check if cyware-analysisd is running or not (according to the expected behavior).
        - teardown:
            - Truncate cyware logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
            - Restart the cyware-manager service to apply initial configuration and start cyware-analysisd daemon.

    cyware_min_version: 4.4.0

    parameters:
        - configuration:
            type: dict
            brief: Get configurations from the module.
        - metadata:
            type: dict
            brief: Get metadata from the module.
        - restart_cyware_daemon_after_finishing_function:
            type: fixture
            brief: Restart the cyware service in teardown stage.
        - load_cyware_basic_configuration:
            type: fixture
            brief: Load basic cyware configuration.
        - set_cyware_configuration:
            type: fixture
            brief: Apply changes to the ossec.conf configuration.
        - configure_local_internal_options_function:
            type: fixture
            brief: Apply changes to the local_internal_options.conf configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate cyware logs.

    assertions:
        - Check whether the EPS limitation is activated, deactivated or generates a configuration error due to a
            missing label.
        - Check if cyware-analysisd is running or not (according to the expected behavior).

    input_description:
        - The `configuration_missing_values` file provides the module configuration for this test.
        - The `cases_missing_values` file provides the test cases.
    """
    # Remove test case tags from ossec.conf
    file.replace_regex_in_file(metadata['remove_tags'], [''] * len(metadata['remove_tags']), CYWARE_CONF_PATH)

    if metadata['behavior'] == 'works':
        control_service('restart')
        evm.check_eps_enabled(metadata['maximum'], 10)  # 10 is the default timeframe
        assert check_if_daemons_are_running(['cyware-analysisd'])[0], 'cyware-analysisd is not running. Maybe it has ' \
                                                                     'crashed'
    elif metadata['behavior'] == 'missing_maximum':
        control_service('restart')
        evm.check_eps_missing_maximum()
        assert check_if_daemons_are_running(['cyware-analysisd'])[0], 'cyware-analysisd is not running. Maybe it has ' \
                                                                     'crashed'
    else:
        try:
            control_service('restart')
        except ValueError:
            pass
        finally:
            evm.check_configuration_error()
            # Check that cyware-analysisd is not running
            assert not check_if_daemons_are_running(['cyware-analysisd'])[0], 'cyware-analysisd is running and was not ' \
                                                                             'expected to'
