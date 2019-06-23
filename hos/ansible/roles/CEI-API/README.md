README
======

### Enable or Disable Auditing
  * Auditing feature can be disabled or enabled by following steps.
    * Edit the file  ~/helion/my_cloud/definition/cloudConfig.yml
    * All audit related configuration is defined under `audit-settings` section.
        * Please note that valid yaml syntax need to be followed when specifying values.
    * Service name defined under `enabled-services` or `disabled-services` override
      the default setting (i.e. `default: enabled` or `default: disabled`)
    * To enable auditing, make sure that `ceilometer` service name is within
      `enabled-services` list of `audit-settings` section or is **not** present in
      `disabled-services` list when `default: enabled`.
    * To disable auditing for ceilometer service specifically, make sure that `ceilometer`
      service name is within `disabled-services` list of `audit-settings`
      section or is **not** present in `enabled-services` list when
      `default: disabled`.
    * It is incorrect to specify service name in both list. If its specified, then
      `enabled-services` value takes precedence.
    * Commit the change in git repository.
    * *cd ~/helion/hos/ansible/*
    * *ansible-playbook -i hosts/localhost config-processor-run.yml*
    * *ansible-playbook -i hosts/localhost ready-deployment.yml*
    * *cd ~/scratch/ansible/next/hos/ansible*
  * *ansible-playbook -i hosts/verb_hosts ceilometer-reconfigure.yml*
