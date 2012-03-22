#!/usr/bin/env python

test_cases = []

# All possible options
test_cases.append({
    'totalnodes': 4,
    'version': 'Enterprise',
    'analyticsnodes': 2,
    'searchnodes': 1,
    'cfsreplicationfactor': 2,
    'clustername': "All Enterprise T$e%^st",
    'installopscenter': 'True',
    'instance_type': 'm1.large',
    'release': '2.0-1'
})

test_name = 'All Community Options'
test_cases.append({
    'totalnodes': 4,
    'version': 'Community',
    'clustername': test_name,
    'installopscenter': 'True',
    'instance_type': 'm1.large'
})

test_name = 'All Enterprise with No OpsCenter'
test_cases.append({
    'totalnodes': 4,
    'version': 'Enterprise',
    'analyticsnodes': 2,
    'searchnodes': 1,
    'cfsreplicationfactor': 2,
    'clustername': test_name,
    'installopscenter': 'False',
    'instance_type': 'm1.large'
})

test_name = 'Old Enterprise 1.0'
test_cases.append({
    'totalnodes': 4,
    'version': 'Enterprise',
    'analyticsnodes': 2,
    'searchnodes': 0,
    'cfsreplicationfactor': 2,
    'clustername': test_name,
    'instance_type': 'm1.large',
    'release': '1.0.2-1'
})

test_name = 'CFS of 2'
test_cases.append({
    'totalnodes': 4,
    'version': 'Enterprise',
    'analyticsnodes': 2,
    'searchnodes': 1,
    'cfsreplicationfactor': 2,
    'clustername': test_name,
    'instance_type': 'm1.large'
})

test_name = 'Single C*'
test_cases.append({
    'totalnodes': 1,
    'version': 'Enterprise',
    'analyticsnodes': 0,
    'searchnodes': 0,
    'clustername': test_name,
    'installopscenter': 'True',
    'instance_type': 'm1.large',
    'release': '2.0-1'
})

test_name = 'Single Analytics'
test_cases.append({
    'totalnodes': 1,
    'version': 'Enterprise',
    'analyticsnodes': 1,
    'searchnodes': 0,
    'cfsreplicationfactor': 1,
    'clustername': test_name,
    'installopscenter': 'True',
    'instance_type': 'm1.large',
    'release': '2.0-1'
})

test_name = 'DSE-2.0 - Single Search'
test_cases.append({
    'totalnodes': 1,
    'version': 'Enterprise',
    'analyticsnodes': 0,
    'searchnodes': 1,
    'clustername': test_name,
    'installopscenter': 'True',
    'instance_type': 'm1.large',
    'release': '2.0-1'
})

test_name = 'DSE-2.0 - All C*'
test_cases.append({
    'totalnodes': 2,
    'version': 'Enterprise',
    'analyticsnodes': 0,
    'searchnodes': 0,
    'cfsreplicationfactor': 1,
    'clustername': test_name,
    'installopscenter': 'True',
    'instance_type': 'm1.large',
    'release': '2.0-1'
})

test_name = 'DSE-2.0 - All Analytics'
test_cases.append({
    'totalnodes': 2,
    'version': 'Enterprise',
    'analyticsnodes': 2,
    'searchnodes': 0,
    'cfsreplicationfactor': 1,
    'clustername': test_name,
    'installopscenter': 'True',
    'instance_type': 'm1.large',
    'release': '2.0-1'
})

test_name = 'DSE-2.0 - All Search'
test_cases.append({
    'totalnodes': 2,
    'version': 'Enterprise',
    'analyticsnodes': 0,
    'searchnodes': 2,
    'cfsreplicationfactor': 1,
    'clustername': test_name,
    'installopscenter': 'True',
    'instance_type': 'm1.large',
    'release': '2.0-1'
})

for case in test_cases:
    print 'cassandralauncher/cassandralauncher.py ',
    switches = case.keys()
    switches.sort()
    for switch in switches:
        if switch == 'clustername':
            print '--{0} "{1}"'.format(switch, case[switch]),
        else:
            print '--{0} {1}'.format(switch, case[switch]),
    print
    print

print 'Manually test just --version, --clustername, --totalnodes'
print
