#!/usr/bin/env python

import os
import shutil
import sys

from optparse import OptionParser

def header():
    """Setup an array of information before starting the program."""

    # Read authentication file
    import ConfigParser
    config = ConfigParser.RawConfigParser()

    # If $CLUSTERLAUNCHER_CONF is set, we will assume success or total failure
    if os.getenv('CLUSTERLAUNCHER_CONF'):
        configfile = os.getenv('CLUSTERLAUNCHER_CONF')
        if not os.path.exists(configfile):
            sys.stderr.write("ERROR: environ['CLUSTERLAUNCHER_CONF'] is set incorrectly to a file that does not exists.\n")
            sys.stderr.write("Please remove the enviornment variable or set it correctly.\n")
            sys.exit(1)
    else:
        # Look for the configuration file in the same directory as the launcher
        configfile = os.path.join(os.path.dirname(__file__), 'clusterlauncher.conf')
        if not os.path.exists(configfile):
            # Look for the configuration file in the user's home directory
            configfile = os.path.join(os.path.expanduser('~'), '.clusterlauncher.conf')
        if not os.path.exists(configfile):
            # Look for the configuration file in /etc/clusterlauncher
            defaultfile = os.path.join('/etc', 'cassandralauncher', 'clusterlauncher.conf')
            configfile = os.path.join(os.path.expanduser('~'), '.clusterlauncher.conf')
            shutil.copyfile(defaultfile, configfile)

            # Exit the program to alert the user that the conf file must be properly set with authentications
            # before continuing
            sys.stderr.write("A copy of the default configuration file located at:\n")
            sys.stderr.write('    %s\n' % defaultfile)
            sys.stderr.write("was now copied to:\n")
            sys.stderr.write('    %s\n' % configfile)
            sys.stderr.write("Please ensure that all default settings are correct and filled in before continuing.\n")
            sys.exit(1)

        if not os.path.exists(configfile):
            # Exit since we still have not found the configuration file
            sys.stderr.write("Please setup your authentication configurations. Order of importance:\n")
            sys.stderr.write("    The location as set by $CLUSTERLAUNCHER_CONF.\n")
            sys.stderr.write("    {0}\n".format(os.path.join(os.path.dirname(__file__), 'clusterlauncher.conf')))
            sys.stderr.write("    {0}\n".format(os.path.join(os.path.expanduser('~'), '.clusterlauncher.conf')))
            sys.stderr.write("    {0}\n".format(os.path.join('/etc', 'cassandralauncher', 'clusterlauncher.conf')))
            sys.exit(1)
    
    # Read configuration file
    config.read(configfile)
    config.add_section('Internal')
    config.set('Internal', 'last_location', configfile)

    # Constantly referenced filenames
    KEY_PAIR = config.get('EC2', 'key_pair') if config.has_option('EC2', 'key_pair') else 'DataStaxLauncher'
    KEY_PAIR = KEY_PAIR.replace('.pem', '')

    PEM_HOME = os.path.expanduser(config.get('EC2', 'pem_home'))
    HOST_FILE = os.path.join(PEM_HOME, 'ds_known_hosts')
    PEM_FILE = os.path.join(PEM_HOME, KEY_PAIR) + '.pem'

    # Ensure filesystem access
    if not os.path.exists(PEM_HOME):
        try:
            os.makedirs(PEM_HOME)
        except:
            sys.stderr.write("Failed to create %s. Please ensure the parent directory has write permissions.\n" % PEM_HOME)
            sys.exit(1)
    if not os.access(PEM_HOME, os.W_OK):
        sys.stderr.write("Please ensure %s is writeable. Nothing was launched.\n" % PEM_HOME)
        sys.exit(1)

    return [config, KEY_PAIR, PEM_HOME, HOST_FILE, PEM_FILE]

def printConnections(user, private_ips, public_ips):
    """Helper method for printing ssh commands."""

    # Print SSH commands
    for publicIP in public_ips:
        print '{0} {1}@{2}'.format(config.get('System', 'ssh'), user, publicIP)
    print

    # Print IPs (CSV)
    print "Private IPs:"
    print ", ".join(private_ips)
    print "Public IPs:"
    print ", ".join(public_ips)
    print

def typed_input(type_check, question=''):
    """Like raw_input, but reprompts to ensure strict type checking."""

    toReturn = ""

    # Repeat question until the input is an int
    while not isinstance(toReturn, type_check):
        try:
            toReturn = type_check(raw_input(question))
        except ValueError:
            toReturn = ""
        
    # Return the int
    return toReturn

def choose(question, choices, noneOption=False, sort=True):
    """Like raw_input, but prompts options and reprompts until answer is valid."""

    print question

    # Sort dictionary keys
    if sort:
        choices.sort()

    # Add an option for adding None to the list as 0
    if noneOption:
        choices = ['None'] + choices

    if len(choices) == 0:
        print "No choices available."
        print
        sys.exit()

    # List the options
    for i, choice in enumerate(choices):
        print "  [{0}] {1}".format(i, choice)

    if len(choices) == 1:
        index = 0
        print '%s automatically chosen.' % choices[0]
    else:
        # Repeat question until the input is a valid int
        index = ""
        while not isinstance(index, int) or index >= len(choices):
            try:
                index = int(raw_input())
            except ValueError:
                index = ""
        
    # Clear a line and return the choice
    print
    return choices[index]

def parse_cli_options(options_tree):
    """Allows for a simplified way to parse complex argument types.
    In particular, when coming from different sources."""

    parser = OptionParser()

    # Keys in options_tree dictionary are the arguments
    options = options_tree.keys()
    options.sort()

    for option in options:
        # All options are created from said dictionary
        section = options_tree[option]['Section']
        help = options_tree[option]['Help']
        action = options_tree[option]['Action'] if 'Action' in options_tree[option] else 'store'
        parser.add_option('--{0}'.format(option), action=action,
                          dest='{0}_{1}'.format(section, option),
                          help=help)

    (options, args) = parser.parse_args()
    return vars(options)
