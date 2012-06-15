Changes
=======

* 1.15-0: Regions besides us-east-1 now supported.
* 1.16-0: DSE 2.0 support. QA folder with test generation
and smoke testing scripts.
* 1.17-0: Notify users when `ssh-keyscan` fails and workaround
OpsCenter 2.1.0 bug with installing agents.
* 1.18-0: Added datastax_pssh and s3 store/restore functionality.
See [New Features](https://github.com/joaquincasares/cassandralauncher/tree/master/docs/new_features.md) for details.
* 1.18-1: Added needed files to the manifest.

Automated Features
==================

The list of automated features include:

* DataStax username and password memory
* AWS API key memory
* Instance size memory
* Input validation
* Automated RSA fingerprint checking
* Automatic separate known_hosts file
* Pre-built SSH strings
* Automatic OpsCenter agent installation
* Passwordless SSH around the cluster
* datastax_ssh tool
  * Allows for SSH commands to easily be run across an entire cluster
* nodelist file
  * An uploaded file onto the cluster for later, possible, use
* Modified hosts file
  * Allows for easy jumping between machines, e.g. c0, c1, a0, a1, s0, ...
