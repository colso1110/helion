<!--

 (c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP

 Licensed under the Apache License, Version 2.0 (the "License"); you may
 not use this file except in compliance with the License. You may obtain
 a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.

-->

This repo contains the playbooks for installing and configuring Horizon as well
as any additional dashboards.

# Adding your own dashboard, panel group, or panels

Adding your dashboard, panel groups, or panels requires having your code made
available to Horizon and adding some configuration to enable that code.

## STEP 1 - Package your dashboard code within the horizon virtual environment

To do this, you will need to modify
[ansible/roles/venv/defaults/main.yml](https://git.fc.usa.hp.com/
cgit/hp/hlm-dev-tools/tree/ansible/roles/venv/defaults/main.yml)
within the [hp/hlm-dev-tools](https://git.fc.usa.hp.com/cgit/hp/hlm-dev-tools)
repository.  This will involve (a) adding your source code to the list of HLM
virtual environment sources and (b) specifying its inclusion in the Horizon
virtual environment tarball.

### (a) Adding your source

You will need to add your dashboard repo to the list of repos declared under the
**_venv_hlm_sources** section.  For example, suppose you have a new dashboard
called "a_new_dashboard" in a repo called "hp/a_new_dashboard" and that this
dashboard makes use of a python library api called "a_new_pythonclient" in a
named "hp/a_new_pythonclient".  Then you'd add the following lines to the
**_venv_hlm_sources** section:

    # List of sources for HLM
    _venv_hlm_sources:

      a_new_pythonclient:
        dest: "{{ _venv_source_dir }}/a_new_pythonclient"
        branch: "{{ _venv_service_branch_default }}"
        url: "{{ dev_env_default_git_server }}/hp/a_new_pythonclient"

      a_new_dashboard:
        dest: "{{ _venv_source_dir }}/a_new_dashboard"
        branch: "{{ _venv_service_branch_default }}"
        url: "{{ dev_env_default_git_server }}/hp/a_new_dashboard"

This will ensure that your repositories are cloned in a temporary directory
along with all the other repositories to be used in the process of building
each virtual environment's tarball.  Also, note that the list of sources is
alphabetized by the name.  Please maintain this convention.

### (b) Including your source in the Horizon virtual environment tarball

Next, under the services default section, you will need to reference your repo
in the list of repositories to include when building the horizon virtual
environment, under **_services_default --> horizon --> sources**

Using the "a_new_dashboard" example again.  You will want to add the following
to the section that specifies which sources are to be installed into the horizon
virtual environment.  Here's what that section looks like when adding the
dashboard and client code to the existing list of horizon dependencies:

      horizon:
        sources:
          - keystoneclient
          - ceilometerclient
          - cinderclient
          - glanceclient
          - neutronclient
          - novaclient
          - swiftclient
          - heatclient
          - horizon
          - monasca_ui
          - a_new_dashboard
          - a_new_pythonclient
        pips:
          - python-memcached
        version: "{{ package_version }}"

The changes to **hp/hlm-dev-tools** will need to be merged *before* you can
merge changes to the **horizon-ansible** repository (described below)

To get your changes to the **hp/hlm-dev-tools** repository reviewed and merged,
you will want to ping someone from Horizon team (just mention HLM and that you
are merging a new dashboard).  This can be done in the "Horizon" hipchat room.

## STEP 2 - Add a role to the hp/horizon-ansible repository

The next step is to **(a)** create a new role within the **horizon-ansible**
repository and **(b)** enable your dashboard:

### (a) Add a directory for your role

In a clone of the **horizon-ansible** repo, under the **roles/** directory,
create a new directory (using the name of your role).

### (b) Create configure.yml script to enable your dashbaord

In the directory of your role, create a **tasks/** subdirectory and, in the
**tasks** directory, create a **configure.yml** ansible script.  You will need
to use this script to add your dashboard configuration file(s) to the
**{{ horizon_enabled_dashboard_dir }}** directory, which will translate to
**lib/python2.7/site-packages/openstack_dashboard/local/enabled/** within the
Horizon virtual environment directory.

Instructions on how to configure your dashboard can be found in the
[horizon docs](http://docs.openstack.org/developer/horizon/topics/settings.html
#pluggable-settings-label).
Here, we can go over how to install your dashboard, panel group, and/or panel
configuration file(s) so that Horizon loads it:


#### (i) Copying
If the configuration options of your dashboard do not depend on any other
variables that need to be translated during installation, you can have a copy of
the configuration file in a "files/" subdirectory  of your new role's directory
and use the ansible copy command to copy the file to the
**{{ horizon_dashboard_enabled_dir }}**.

#### (ii) Templating
If, however, your dashboard configuration file does contain jinja2 placeholders
that need to be translated, you'll want to put a copy of your template in a new
**templates/** subdirectory of your role's directory and use the ansible
"template" command to copy and translate your dashboard configuration file.

#### (iii) Symlinking
If the default dashboard configuration file is defined in the source of your
dashboard project and is available within it's directory in the virtual
environment, you can use the ansible "file" command to sym link it from
**{{ horizon_dashboard_enabled_dir }}**



## STEP 3 - Modify horizon-deploy.yml to reference your configure task.

In the future, we will be modifying horizon-deploy.yml to automatically load
each role's configure.yml file, but, for now, you will need to modify, in the
**hp/horizon-ansible** repository, horizon-deploy.yml to do this so that your
role's configure.yml is run after HZN-WEB/configure.yml is run.



##OTHER NOTES: 


If you are incrementally testing changes to the process for building the Horizon
virtual environment tarball, you will find some useful notes here:

https://git.fc.usa.hp.com/cgit/hp/hlm-dev-tools/plain/build-vagrant/README.md

Rebuilding virtual environments takes a very long time.  If you are just making
changes to one virtual environment tarball, this link will explain how to test
your changes incrementally.

We believe these instructions should cover everything needed to install a new
dashboard.  However, if the installation/configuration of your particular
dashboard requires additional steps not documented here, please contact us (on
the horizon team) to figure out the best, most maintainable/flexible way to
proceed.

