# Copyright (C) 2015-2021, KhulnaSoft Ltd.
# Created by Cyware, Inc. <info@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import pytest

from cyware_testing.tools.services import control_service


@pytest.fixture(scope='package')
def restart_logcollector_required_daemons_package():
    control_service('restart', 'cyware-agentd')
    control_service('restart', 'cyware-logcollector')
    control_service('restart', 'cyware-modulesd')

    yield

    control_service('restart', 'cyware-agentd')
    control_service('restart', 'cyware-logcollector')
    control_service('restart', 'cyware-modulesd')
