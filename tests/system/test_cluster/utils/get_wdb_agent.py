# Copyright (C) 2015-2021, KhulnaSoft Ltd.
# Created by Cyware, Inc. <info@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import sys
sys.path.append('/cyware-qa/deps/cyware_testing')
from cyware_testing import cyware_db

result = cyware_db.query_wdb(sys.argv[1])
if result:
  print(result)
