# Changelog

## [2.0]
### Major Changes
- Complete code refactor.
- Script now runs in three distinct phases:
  1. Executes a lightweight Ansible task to gather facts and detect package managers.
  2. Builds and runs playbooks dynamically for each detected package manager (filtered by allowed values). Runs in parallel to avoid bottlenecks (e.g., no need to wait for all YUM tasks to finish before starting APT).
  3. Gathers and sends results to Zabbix.
- Fully dynamic YAML playbook generation using PyYAML. Unused tasks are removed (e.g., APT tasks if only YUM is detected), allowing easier customization. Removed static `linux_security_compliance.yaml`.
- Reworked command-line arguments for more intuitive and flexible usage. Configuration can now be overridden via CLI (e.g., Zabbix server, inventory path, allowed package managers).
- Added flexibility to choose and mix package managers and define packages to lock/unlock.
- Introduced verbose and silent output modes.
- Reworked log sending to Zabbix.
- Optional inventory generation from Zabbix API:
  - Requires a valid API token.
  - Selects the first available interface (IP or DNS).
  - **Important:** Hosts with no interfaces or only `127.0.0.1` will be skipped.
  - Hostnames and group names with spaces will be converted to use underscores (`_`).

### Minor Changes
- Changes on Python script:
- Renamed `ZABBIX_DEF_HOSTNAME` to `ZABBIX_HOST`.
- Removed `ZABBIX_PORT`. `ZABBIX_SERVER` now accepts an array for HA/clustered nodes (e.g., `['zabbix1:10051', 'zabbix2', 'zabbix3:10055']`).
- Added lock mechanism: script won't run if a `.lock` file is found in the temp path.
- Temporary files are now deleted upon successful execution.
- User login can now be set via variable or CLI argument.
- Script renamed to `zbx_linux_security_compliance.py`. Still executable directly if marked as such.
- Changes on Zabbix templates:
	- Added SELinux item and trigger.
	- Updated JSONPath expressions to the items:
	  - Linux distribution: `..distro.first()` → `..distribution.first()`
	  - Linux version: `..distro_ver.first()` → `..distribution_version.first()`
	- Added new item: "Locked updates list".
	- Renamed item key updates.raw to report.raw.
	- Added macro {$ANSIBLE_HOST} to override any interface address when using Zabbix API.

## [1.1]
### Changes
- Added new params to lock/hold and unlock/unhold packages.
  - Yum already filters those that are locked, but changed the apt when listing updates to remove those holded.
  - The list of apt packages are without the repository (ex: "packagename/repository 1.1.1 amd64").
  - Removed the javascript function in the zabbix preprocessor to remove the repository, and added to diplay the error when trying to list updates into the 'updates.pending.list' item.
- Improved errors handling Ansible/Python.
- Added an option to escalate privileges using Ansible (become).
- Case insensitive for param --sshcheck (True/true - False/false)

### Notes
- When locking/unlocking a package fails, it would not proceed to update/upgrade. As a failsafe in case you do not want to upgrade a package.
- For Ansible yum-versionlock module, now requires to install the collection. Added it into README.

## [1.0]
### First release
- Update repositories and the ability to do upgrade of packages.