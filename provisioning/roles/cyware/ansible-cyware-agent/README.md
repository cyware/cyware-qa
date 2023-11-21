Ansible Playbook - Cyware agent
==============================

This role will install and configure a Cyware Agent.

OS Requirements
----------------

This role is compatible with:
 * Red Hat
 * CentOS
 * Fedora
 * Debian
 * Ubuntu


Role Variables
--------------

* `cyware_managers`: Collection of Cyware Managers' IP address, port, and protocol used by the agent
* `cyware_agent_authd`: Collection with the settings to register an agent using authd.

Playbook example
----------------

The following is an example of how this role can be used:

     - hosts: all:!cyware-manager
       roles:
         - ansible-cyware-agent
       vars:
         cyware_managers:
           - address: 127.0.0.1
             port: 1514
             protocol: tcp
             api_port: 55000
             api_proto: 'http'
             api_user: 'ansible'
         cyware_agent_authd:
           registration_address: 127.0.0.1
           enable: true
           port: 1515
           ssl_agent_ca: null
           ssl_auto_negotiate: 'no'


License and copyright
---------------------

CYWARE Copyright (C) 2016, KhulnaSoft Ltd. (License GPLv3)

### Based on previous work from dj-wasabi

  - https://github.com/dj-wasabi/ansible-ossec-server

### Modified by Cyware

The playbooks have been modified by Cyware, including some specific requirements, templates and configuration to improve integration with Cyware ecosystem.
