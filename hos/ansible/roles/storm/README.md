#Storm
Installs [Apache Storm](http://storm.incubator.apache.org/)

##Requirements
By default neither ui or logviewer will be enabled, set one or both of these variables to enable.
- storm_ui_enabled: true
- storm_logviewer_enabled: true

If `storm_ui_enabled` is set to True the UI is installed on the same box as nimbus. Typically there is a single nimbus server and multiple supervisors. Storm-logviewer is installed on the same box as the supervisors.

The variable are required for proper setup
- zookeeper_hosts - comma separated list of hosts, any specified port is ignored 2181 is used.

## Optional
- monasca_log_level - Log level to be used for storm logs. Defaults to WARN
- storm_wait_for_period - The time in seconds for how long to wait for the nimbus port and the ui port to be available after starting them. Default is 60 seconds.
- run_mode: One of Deploy, Stop, Install, Configure or Start. The default is Deploy which will do Install, Configure, then Start.

##License
Apache

##Author Information
Tim Kuhlman

Monasca Team email monasca@lists.launchpad.net
