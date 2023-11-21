/*
 * SQL Schema rbac tests
 * Copyright (C) 2015-2021, KhulnaSoft Ltd.
 * Created by Cyware, Inc. <info@khulnasoft.com>.
 * This program is a free software, you can redistribute it and/or modify it under the terms of GPLv2.
 */

-- PRAGMA foreign_keys=OFF;
-- BEGIN TRANSACTION;

/* Testing */
DELETE FROM users WHERE username = 'test_user';
