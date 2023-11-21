Ansible Role: Filebeat for Elastic Stack
------------------------------------

An Ansible Role that installs [Filebeat-oss](https://www.elastic.co/products/beats/filebeat), this can be used in conjunction with [ansible-cyware-manager](https://github.com/cyware/cyware-ansible/ansible-cyware-server).

Requirements
------------

This role will work on:
 * Red Hat
 * CentOS
 * Fedora
 * Debian
 * Ubuntu

Role Variables
--------------

Available variables are listed below, along with default values (see `defaults/main.yml`):

```
  filebeat_output_indexer_hosts:
    - "localhost:9200"

```

License and copyright
---------------------

CYWARE Copyright (C) 2016, KhulnaSoft Ltd. (License GPLv3)

### Based on previous work from geerlingguy

 - https://github.com/geerlingguy/ansible-role-filebeat

### Modified by Cyware

The playbooks have been modified by Cyware, including some specific requirements, templates and configuration to improve integration with Cyware ecosystem.
