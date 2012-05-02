#!/usr/bin/env python

import getpass
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import urllib2

import ec2
import common


# Globals
private_ips = []
public_ips = []

config, KEY_PAIR, PEM_HOME, HOST_FILE, PEM_FILE = common.header()
cli_options = {}


#################################
# Execution and SSH commands

def exe(command, wait=True):
    """Execute a subprocess command"""

    # Open a subprocess to run your command
    process = subprocess.Popen(shlex.split(str(command)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if wait:
        read = process.communicate()
        return read
    else:
        return process

def create_ssh_cmd(sshuser, host):
    """SSH function that returns SSH string"""

    connstring = "%s -i %s -o UserKnownHostsFile=%s %s@%s " % (
                        config.get('System', 'ssh'),
                        PEM_FILE,
                        HOST_FILE,
                        sshuser, host
                    )
    return connstring

def exe_ssh_cmd(connstring, command, wait=True):
    """SSH function that executes SSH string + command"""

    return exe('{0} "{1}"'.format(connstring, command), wait)

def scp_send(sshuser, host, sendfile, tolocation=''):
    """SCP send a file"""

    return exe("%s -i %s -o UserKnownHostsFile=%s %s %s@%s:%s" % (
                config.get('System', 'scp'),
                PEM_FILE,
                HOST_FILE,
                sendfile, sshuser, host, tolocation
            ))

#################################

#################################
# Keyless SSH Creation

def confirm_authentication(username, password):
    repo_url = "http://debian.datastax.com/enterprise"

    # Configure HTTP authentication
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, repo_url, username, password)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)

    # Try reading from the authenticated connection
    try:
        opener.open(repo_url)
    except Exception as inst:
        if "401" in str(inst):
            # Authentication failed
            return False
        raise
    return True

#################################

#################################
# Install small tools

def install_datastax_ssh(user):
    # Find the datastax_ssh original file
    datastax_ssh = os.path.join(os.path.dirname(__file__), 'datastax_ssh')
    if not os.path.exists(datastax_ssh):
        datastax_ssh = os.path.join('/etc', 'cassandralauncher', 'datastax_ssh')

    # Write the public IPs to the nodelist file
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write('\n'.join(public_ips))
        tmp_file.flush()

        # Send files to the cluster
        for ip in public_ips:
            scp_send(user, ip, tmp_file.name, 'nodelist')
            scp_send(user, ip, datastax_ssh)
            exe_ssh_cmd(create_ssh_cmd(user, ip), 'chmod +x datastax_ssh; sudo mv datastax_ssh /usr/bin/datastax_ssh; sudo mkdir /etc/cassandralauncher; sudo mv nodelist /etc/cassandralauncher/nodelist')

def upload_smoke_tests(user):
    # Find the datastax_ssh original file
    qa_file = os.path.join(os.path.dirname(__file__), '../', 'qa', 'run_packaging_smoke.sh')
    if not os.path.exists(qa_file):
        return

    # Send files to the cluster
    for ip in public_ips:
        scp_send(user, ip, qa_file, 'run_packaging_smoke.sh')
        exe_ssh_cmd(create_ssh_cmd(user, ip), 'chmod +x run_packaging_smoke.sh')
        # exe_ssh_cmd(create_ssh_cmd(user, ip), 'sudo ./run_packaging_smoke.sh hadoop pkg')
        # exe_ssh_cmd(create_ssh_cmd(user, ip), 'sudo ./run_packaging_smoke.sh search pkg')

def install_hosts_appending(user):
    # Write the public IPs to a hosts file
    with tempfile.NamedTemporaryFile() as tmp_file:
        hosts_file = ''
        for i, ip in enumerate(private_ips):
            for node_type in node_types:
                if i in node_types[node_type]:
                    i = node_types[node_type].index(i)
                    break
            hosts_file += '{0:15} {1}\n'.format(ip, '{0}{1}'.format(node_type, i))
        tmp_file.write(hosts_file)
        tmp_file.flush()

        # Send files to the cluster
        for ip in public_ips:
            scp_send(user, ip, tmp_file.name, 'hosts_file')
            exe_ssh_cmd(create_ssh_cmd(user, ip), "sudo su -c 'cat hosts_file >> /etc/hosts'")
            exe_ssh_cmd(create_ssh_cmd(user, ip), 'rm hosts_file')

#################################

#################################
# Keyless SSH Creation

def sshprompt(prompt, choices):
    """Helper for prompting that ensures user answer is included in choices.
    'prompt' text is displayed after initial blank prompt, in the event that the answer is not included in the choices.
    """

    # Repeat question until the input is a valid int
    while True:
        response = raw_input().lower()
        if response in choices:
            break
        print prompt,
    return response

def prompt_rsa_fingerprints(ip, fingerprint):
    """Prompts the user to accept RSA fingerprints."""

    # Generate and prompt
    securityText = [
        "The authenticity of host '{0} ({0})' can't be established.",
        "RSA key fingerprint is {1}.",
        "Are you sure you want to continue connecting (yes/no/all)?"
    ]
    print "\n".join(securityText).format(ip, fingerprint),
    accept_rsa_fingerprints = sshprompt("Please type 'yes' or 'no' or 'all': ", ['yes', 'no', 'all'])

    # Allow one more chance if answered 'no'
    if accept_rsa_fingerprints == 'no':
        while True:
            confirmation = raw_input("Do you really want to cancel OpsCenter Agent Installation (y/n)? ").lower()
            if confirmation in ['y', 'n']:
                break
        if confirmation == 'y':
            sys.exit(1)
        else:
            print "\n".join(securityText),
            accept_rsa_fingerprints = sshprompt("Please type 'yes' or 'no' or 'all': ", ['yes', 'no', 'all'])
    if accept_rsa_fingerprints == 'no':
        sys.exit(1)

    return accept_rsa_fingerprints

def create_keyless_ssh_ring(public_ips, user):
    """Create keyless SSH ring from primed servers"""

    print "Creating a keyless SSH ring..."

    # Send files to EC2 once
    kicker_conn = create_ssh_cmd(user, public_ips[0])
    scp_send(user, public_ips[0], PEM_FILE)
    scp_send(user, public_ips[0], HOST_FILE)
    exe_ssh_cmd(kicker_conn, "mv %s .ssh/id_rsa; chmod 400 .ssh/id_rsa" % (KEY_PAIR + '.pem'))
    exe_ssh_cmd(kicker_conn, "mv %s .ssh/known_hosts; chmod 600 .ssh/known_hosts" % 'ds_known_hosts')

    # Transfer files from kicker node to all other nodes
    for node in public_ips[1:]:
        exe_ssh_cmd(kicker_conn, "scp .ssh/id_rsa %s:.ssh/id_rsa" % node)
        exe_ssh_cmd(kicker_conn, "scp .ssh/known_hosts %s:.ssh/known_hosts" % node)

def prime_connections(public_ips, user):
    """Ask acceptance of RSA keys."""

    print "Priming connections..."

    # Clear previous file, if not running parallel tests
    if not cli_options['CLI_qa']:
        with open(HOST_FILE, 'w') as f:
            f.write('')

    accept_rsa_fingerprints = config.get('Cassandra', 'accept_rsa_fingerprints')

    # Prompt for RSA fingerprint authentication for each IP
    for ip in public_ips:

        while True:
            # Get public RSA key
            rsa_key = exe('ssh-keyscan -t rsa {0}'.format(ip))[0]
            with tempfile.NamedTemporaryFile() as tmp_file:
                tmp_file.write(rsa_key)
                tmp_file.flush()

                # Generate fingerprint
                fingerprint = exe('ssh-keygen -l -f {0}'.format(tmp_file.name))[0].split()[1]

            # Ensure that stderr didn't return the error message '* is not a public key file.'
            if fingerprint != 'is':
                break

        # If performing individual authentication, prompt
        if accept_rsa_fingerprints != 'all':
            accept_rsa_fingerprints = prompt_rsa_fingerprints(ip, fingerprint)

        # Append all public RSA keys into HOST_FILE
        with open(HOST_FILE, 'a') as f:
            f.write(rsa_key)

        # Clear authentication if not marked 'all'
        if accept_rsa_fingerprints != 'all':
            accept_rsa_fingerprints = ''

    create_keyless_ssh_ring(public_ips, user)

#################################

#################################
# Installing OpsCenter Agents

def start_priming(user):
    """Prime connections to all nodes"""

    # Give AWS some time to warm up
    wait = 10
    print "Waiting %s seconds for EC2 instances to warm up..." % wait
    time.sleep(wait)

    # Authenticate and ring cluster with keyless SSH
    prime_connections(public_ips, user)
    print

def install_opsc_agents(user):
    """Wait for OpsCenter agent tarball to be created. Then install the agent on all other nodes."""

    if check_cascading_options('installopscenter', optional=True) != 'False':
        # Connection to the OpsCenter machine to be used later
        opsc_conn = create_ssh_cmd(user, public_ips[0])

        print "Waiting for the agent tarball to be created (This can take up to 4 minutes)..."
        print "    If taking longer, ctrl-C and login to AMI to see error logs."
        while exe_ssh_cmd(opsc_conn, "ls /usr/share/opscenter/agent/opscenter-agent.tar.gz")[1]:
            # The agent tarball has yet to be created
            time.sleep(5)

        # Ensures the tarball is fully written before transferring
        while True:
            old_md5 = exe_ssh_cmd(opsc_conn, "md5sum /usr/share/opscenter/agent/opscenter-agent.tar.gz")[0]
            time.sleep(2)
            new_md5 = exe_ssh_cmd(opsc_conn, "md5sum /usr/share/opscenter/agent/opscenter-agent.tar.gz")[0]

            if old_md5 == new_md5:
                break

        print "Installing OpsCenter Agents..."
        for i, node in enumerate(public_ips):
            node_conn = create_ssh_cmd(user, node)

            # Copying OpsCenter Agent tarball
            exe_ssh_cmd(opsc_conn, "scp /usr/share/opscenter/agent/opscenter-agent.tar.gz %s:opscenter-agent.tar.gz" % node)

            # Untarring tarball
            exe_ssh_cmd(node_conn, "sudo mv -f opscenter-agent.tar.gz /usr/share; cd /usr/share; sudo tar --overwrite -xzf opscenter-agent.tar.gz; sudo rm -f opscenter-agent.tar.gz")

            # Starting installation of OpsCenter Agent
            exe_ssh_cmd(node_conn, "cd /usr/share/opscenter-agent/; sudo nohup bin/install_agent.sh opscenter-agent.deb %s %s" % (private_ips[0], private_ips[i]), wait=False)
    print

#################################

#################################
# Log code for private stats

def running_log(reservation, demotime):
    """Logs usage data for personal stats."""

    loginfo = [
        'Running' if config.get('Cassandra', 'demo') == 'True' else 'Ignore',
        config.get('Shared', 'handle'),
        str(demotime),
        str(time.time()),
        str(reservation.id)
    ]
    logline = ",".join(loginfo) + '\n'

    with open('running.log', 'a') as f:
        f.write(logline)

#################################

#################################
# Argument parsing

# This holds the information for all options
# and their metadata to allow easier command
# line argument, configuration reading, and
# raw_input prompting.

options_tree = {
    'handle': {
        'Section': 'Shared',
        'Prompt': 'ShortName (Handle)',
        'Help': 'Your Personal Shortname'
    },
    'aws_access_key_id': {
        'Section': 'EC2',
        'Prompt': 'AWS Access Key ID',
        'Help': 'AWS Access Key ID'
    },
    'aws_secret_access_key': {
        'Section': 'EC2',
        'Prompt': 'AWS Secret Access Key',
        'Help': 'AWS Secret Access Key'
    },
    'clustername': {
        'Section': 'Cassandra',
        'Prompt': 'Cluster Name',
        'Help': 'Name of the Cluster'
    },
    'totalnodes': {
        'Section': 'Cassandra',
        'Prompt': 'Total Nodes',
        'Help': 'Number of Nodes in the Cluster'
    },
    'version': {
        'Section': 'Cassandra',
        'Prompt': 'Version:',
        'Help': 'Community | Enterprise'
    },
    'installopscenter': {
        'Section': 'Cassandra',
        'Prompt': 'Install Opscenter',
        'Help': 'True | False'
    },
    'release': {
        'Section': 'Cassandra',
        'Prompt': 'Specify Package Release',
        'Help': 'Package Release'
    },
    'username': {
        'Section': 'Cassandra',
        'Prompt': 'DataStax Username',
        'Help': 'DataStax Username'
    },
    'password': {
        'Section': 'Cassandra',
        'Prompt': 'Uses getpass()',
        'Help': 'DataStax Password'
    },
    'analyticsnodes': {
        'Section': 'Cassandra',
        'Prompt': 'Analytics Nodes',
        'Help': 'Number of Analytics Nodes'
    },
    'searchnodes': {
        'Section': 'Cassandra',
        'Prompt': 'Search Nodes',
        'Help': 'Number of Search Nodes'
    },
    'cfsreplicationfactor': {
        'Section': 'Cassandra',
        'Prompt': 'CFS Replication Factor',
        'Help': 'CFS Replication Factor'
    },
    'datastax_ami': {
        'Section': 'Cassandra',
        'Prompt': 'DataStax AMI ID',
        'Help': 'DataStax AMI ID'
    },
    'demotime': {
        'Section': 'Cassandra',
        'Prompt': 'Time (in hours) for the cluster to live',
        'Help': 'For use with DemoService'
    },
    'instance_type': {
        'Section': 'EC2',
        'Prompt': 'EC2 Instance Size:',
        'Help': 'm1.large | m1.xlarge | m2.xlarge | m2.2xlarge | m2.4xlarge'
    },
    'opscenterinterface': {
        'Section': 'OpsCenter',
        'Prompt': 'NoPrompts',
        'Help': 'Sets the OpsCenter interface port'
    },
    'noprompts':{
        'Section': 'CLI',
        'Prompt': 'NoPrompts',
        'Action': 'store_true',
        'Help': 'Ensures that no user prompts will occur.'
    },
    'qa':{
        'Section': 'CLI',
        'Prompt': 'QA',
        'Action': 'store_true',
        'Help': 'Upload QA scripts.'
    }
}

def type_checker(option, read_option, type_check, passive=False):
    """Ensures that the data read is of expected type."""

    if type_check:
        try:
            read_option = type_check(read_option)
        except:
            if passive:
                return None
            sys.stderr.write('"{0}" was expected to be of {1}\n'.format(option, type_check))
            sys.exit(1)
    return read_option

def basic_option_checker(read_option, option, type_check, choices):
    """Performs basic checks on configuration and command line argument data."""

    if read_option:
        read_option = type_checker(option, read_option, type_check)
        if choices:
            if any(read_option.lower() == choice.lower() for choice in choices):
                return read_option
        else:
            return read_option

def check_cascading_options(option, type_check=False, choices=False, password=False, optional=False, ignore_command_line=False):
    """Reads from the command line arguments, then configuration file, then prompts
    the user for program options."""
    section = options_tree[option]['Section']

    # Read from sys.argv
    if not ignore_command_line:
        read_option = cli_options['{0}_{1}'.format(section, option)]
        read_option = basic_option_checker(read_option, option, type_check, choices)
        if read_option != None:
            return read_option

    # Read from configfile
    if config.has_option(section, option):
        read_option = config.get(section, option)
        read_option = basic_option_checker(read_option, option, type_check, choices)
        if read_option != None:
            return read_option

    if optional:
        return False

    # Exit(1) if you asked for --noprompts and didn't fill in all variables
    if cli_options['CLI_noprompts']:
        sys.stderr.write('Prompt occurred after specifying --noprompts.\n')
        sys.stderr.write('Missing/Invalid configuration for "--{0}".\n'.format(option))
        sys.exit(1)

    # Prompt for password if special case
    if password:
        return getpass.getpass()

    # Prompt the user with raw_input or common.choose
    while True:
        prompt = options_tree[option]['Prompt']
        if choices:
            response = common.choose(prompt, choices)
        else:
            response = raw_input('{0}: '.format(prompt))
        response = type_checker(option, response, type_check, passive=True)
        if response != None:
            break

    # Set config to avoid double prompting later (doesn't actually write to disk)
    config.set(section, option, response)
    return response


#################################


def main():
    print "Using configuration file: %s" % config.get('Internal', 'last_location')
    print
    print "Welcome to DataStax' Cassandra Cluster Launcher!"
    print "    The easiest way to get Apache Cassandra up and running in Amazon's EC2"
    print "    in under 5 minutes!"
    print

    global cli_options
    cli_options = common.parse_cli_options(options_tree)

    # Required handle for log purposes and future shared EC2 purposes
    check_cascading_options('handle')

    # Prompt the user with any outstanding running clusters
    if (check_cascading_options('aws_access_key_id')[0] == '"' or check_cascading_options('aws_secret_access_key')[0] == '"' or
        check_cascading_options('aws_access_key_id')[0] == "'" or check_cascading_options('aws_secret_access_key')[0] == "'"):
        sys.stderr.write("None of the configurations should be wrapped in quotes.\n")
        sys.stderr.write("    EC2:aws_access_key_id or EC2:aws_secret_access_key appears to be.\n")
        sys.exit(1)

    if not cli_options['CLI_noprompts']:
        ec2.terminate_cluster(check_cascading_options('aws_access_key_id'), check_cascading_options('aws_secret_access_key'), config.get('EC2', 'placement'), check_cascading_options('handle'), prompt_continuation=True)

    start_time = time.time()

    # Get basic information for both Community and Enterprise clusters
    clustername = check_cascading_options('clustername')
    clustername = "'%s'" % clustername.replace("'", "")

    # Ensure totalnodes > 0
    ignore_command_line = False
    while True:
        totalnodes = check_cascading_options('totalnodes', int, ignore_command_line=ignore_command_line)
        if totalnodes > 0:
            break
        else:
            config.set('Cassandra', 'totalnodes')
            ignore_command_line = True

    version = check_cascading_options('version', choices=['Community', 'Enterprise']).title()
    user_data = '--clustername %s --totalnodes %s --version %s' % (clustername, totalnodes, version)

    if version == 'Enterprise':
        ignore_command_line = False
        while True:
            # Get additional information for Enterprise clusters
            username = check_cascading_options('username', ignore_command_line=ignore_command_line)
            password = check_cascading_options('password', password=True, ignore_command_line=ignore_command_line)

            print "Confirming credentials..."
            if confirm_authentication(username, password):
                break
            else:
                config.set('Cassandra', 'username')
                config.set('Cassandra', 'password')
                ignore_command_line = True
                print "Authentication to DataStax server failed. Please try again."

        # Check the number of Analytics Nodes that will launch
        ignore_command_line = False
        while True:
            analyticsnodes = check_cascading_options('analyticsnodes', int, ignore_command_line=ignore_command_line)
            if analyticsnodes <= totalnodes:
                break
            else:
                print "Overallocation of the chosen %d nodes" % (totalnodes)
                # Clear the previous cfsreplicationfactor
                config.set('Cassandra', 'analyticsnodes')
                ignore_command_line = True

        # Check the number of Search Nodes that will launch
        ignore_command_line = False
        while True:
            searchnodes = check_cascading_options('searchnodes', int, ignore_command_line=ignore_command_line)
            if analyticsnodes + searchnodes <= totalnodes:
                break
            else:
                print "Overallocation of the chosen %d nodes" % (totalnodes)
                # Clear the previous cfsreplicationfactor
                config.set('Cassandra', 'searchnodes')
                ignore_command_line = True

        user_data += ' --username %s --password %s --analyticsnodes %s --searchnodes %s' % (username, password, analyticsnodes, searchnodes)

        # If Hadoop enabled nodes are launching, check the CFS replication factor
        if analyticsnodes > 0:
            ignore_command_line = False
            while True:
                cfsreplicationfactor = check_cascading_options('cfsreplicationfactor', int, ignore_command_line=ignore_command_line)
                if 1 <= cfsreplicationfactor and cfsreplicationfactor <= analyticsnodes:
                    break
                else:
                    print "1 <= CFS Replication Factor <= Number of Analytics Nodes"
                    # Clear the previous cfsreplicationfactor
                    config.set('Cassandra', 'cfsreplicationfactor')
                    ignore_command_line = True

            user_data += ' --cfsreplicationfactor %s' % (cfsreplicationfactor)
        print

    # Included for the experimental DemoService that requires demoservice.py to always be running
    demotime = -1
    if config.get('Cassandra', 'demo') == 'True':
        print "Your configuration file is set to launch a demo cluster for a specified time."
        demotime = check_cascading_options('demotime', float)
        print "If the demo service is running, this cluster will live for %s hour(s)." % demotime
        print

    if check_cascading_options('installopscenter', optional=True) == 'False':
        user_data += ' --opscenter no'

    if check_cascading_options('release', optional=True):
        user_data += ' --release %s' % check_cascading_options('release')

    opscenterinterface = 8888
    if check_cascading_options('opscenterinterface', optional=True):
        opscenterinterface = check_cascading_options('opscenterinterface')
        user_data += ' --opscenterinterface %s' % opscenterinterface

    # DataStax AMI specific options and formatting
    image = check_cascading_options('datastax_ami', optional=True)
    if not image:
        image = 'ami-fd23ec94'

    tag = '{0} - DataStaxAMI Time: {1} Size: {2}'.format(check_cascading_options('handle'), time.strftime("%m-%d-%y %H:%M", time.localtime()), totalnodes)
    user = 'ubuntu'

    # Launch the cluster
    instance_type = check_cascading_options('instance_type', choices=['m1.large', 'm1.xlarge', 'm2.xlarge', 'm2.2xlarge', 'm2.4xlarge'])
    clusterinfo = ec2.create_cluster(check_cascading_options('aws_access_key_id'), check_cascading_options('aws_secret_access_key'),
                                    totalnodes, image, tag, KEY_PAIR,
                                    instance_type, config.get('EC2', 'placement'), PEM_HOME,
                                    user_data, cli_options['CLI_noprompts'], opscenterinterface)

    # Save IPs
    global private_ips
    global public_ips
    private_ips, public_ips, reservation = clusterinfo

    # Log clusterinfo
    running_log(reservation, demotime)

    if check_cascading_options('installopscenter', optional=True) != 'False':
        # Print OpsCenter url
        print "OpsCenter Address:"
        print "http://%s:%s" % (public_ips[0], opscenterinterface)
        print "Note: You must wait 60 seconds after Cassandra becomes active to access OpsCenter."
        print

    start_priming(user)

    if version == 'Enterprise':
        global seed_index
        realtimenodes = totalnodes - analyticsnodes - searchnodes
        seed_index = [0, realtimenodes, realtimenodes + analyticsnodes]
        seed_index.reverse()

    global node_types
    node_type = 'c'
    node_types = {'c': [], 'a':[], 's':[]}

    print 'Primed Connection Strings:'
    for i, node in enumerate(public_ips):
        if version == 'Enterprise' and i in seed_index:
            if seed_index.index(i) == 0:
                print 'Search (Solr) Nodes:'
                node_type = 's'
            if seed_index.index(i) == 1:
                print 'Analytics (Hadoop) Nodes:'
                node_type = 'a'
            if seed_index.index(i) == 2:
                print 'Realtime (Cassandra) Nodes:'
                node_type = 'c'

        node_types[node_type].append(i)
        print '    {0} -i {1} -o UserKnownHostsFile={2} {3}@{4}'.format(config.get('System', 'ssh'), PEM_FILE, HOST_FILE, user, node)
    print

    print 'Installing DataStax SSH on the cluster...'
    install_datastax_ssh(user)

    if cli_options['CLI_qa']:
        print 'Uploading smoke tests on the cluster...'
        upload_smoke_tests(user)

    print 'Setting up the hosts file for the cluster...'
    install_hosts_appending(user)

    install_opsc_agents(user)

    end_time = int(time.time() - start_time)
    print 'Total Elapsed Time: %s minutes %s seconds' % (end_time / 60, end_time % 60)
    print

    if not cli_options['CLI_noprompts']:
        ec2.terminate_cluster(check_cascading_options('aws_access_key_id'), check_cascading_options('aws_secret_access_key'), config.get('EC2', 'placement'), check_cascading_options('handle'))
    else:
        # Ensure the agents have time to start
        # installing before exiting the program
        time.sleep(10)

def run():
    try:
        main()
    except KeyboardInterrupt:
        print
        sys.stderr.write("Program Aborted.\n")
        print
        sys.exit(1)



if __name__ == "__main__":
    run()
