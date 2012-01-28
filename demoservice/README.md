# Cassandra Launcher Demo Service

Allows for a service to run over ./running.log from the instantiation directory to ensure that clusters running too long are terminated.

For use in conjuncture with demo=True in clusterlauncher.conf under [Cassandra].

We do _not_ guarantee any successful operations with this program and should not be held liable for over-running clusters. This is merely an experimental tool which works well in our enviornment. Nothing more.

## Setup

Run:

    nohup ./demoservice.py &
