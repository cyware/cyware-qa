# Copyright (C) 2015-2021, KhulnaSoft Ltd.
# Created by Cyware, Inc. <info@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import pytest

from cyware_testing.github import detect_github_start


@pytest.fixture(scope='module')
def wait_for_github_start(get_configuration, request):
    # Wait for module github starts
    file_monitor = getattr(request.module, 'cyware_log_monitor')
    detect_github_start(file_monitor)
