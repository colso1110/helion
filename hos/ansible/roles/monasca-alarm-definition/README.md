# monasca-alarm-definition

This role provides an Ansible module for creation of Monasca alarm definitions and notifications.
More details on alarm definitions can be found at the [Monasca API documentation](https://github.com/stackforge/monasca-api/blob/master/docs/monasca-api-spec.md#alarm-definitions-and-alarms)

##Requirements
It is assumed the service endpoint for Monasca is properly registered in keystone.

##Role Variables

These variables must be defined.

- keystone_url
- monasca_keystone_user
- monasca_keystone_password

## Monasca Modules Usage
There are two modules available in the library subdirectory, one for Monasca notifications and the other for alarm definitions. For example:

    - name: Setup default email notification method
      monasca_notification_method:
        name: "Default Email"
        type: 'EMAIL'
        address: "root@localhost"
        keystone_url: "{{ keystone_url }}"
        keystone_user: "{{ monasca_keystone_user }}"
        keystone_password: "{{ monasca_keystone_password }}"
        keystone_project: "{{ monasca_keystone_project }}"
      register: default_notification_result
    - name: Host Alive Alarm
      monasca_alarm_definition:
        name: "Host Alive Alarm"
        description: "Trigger when a host alive check fails"
        expression: "host_alive_status > 0"
        monasca_keystone_token: "{{ default_notification_result.keystone_token }}"
        monasca_api_url: "{{ default_notification_result.monasca_api_url }}"
        severity: "HIGH"
        alarm_actions:
          - "{{ default_notification_result.notification_method_id }}"
        ok_actions:
          - "{{ default_notification_result.notification_method_id }}"
        undetermined_actions:
          - "{{ default_notification_result.notification_method_id }}"

Refer to the documentation within the module for full detail

##License
Apache

##Author Information
Tim Kuhlman
Monasca Team email monasca@lists.launchpad.net
