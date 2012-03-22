#!/bin/bash

test=$1
install_type=$2

if [ -z "$test" ] || [ -z $install_type ]; then
  echo "Usage:  $0 <dsc | hadoop | search | hive | pig> <tar | pkg>"
  exit
fi

ts=$(date +%m%d%y_%H%M%S)
output=/tmp/${0}-$(date +%m%d%y_%H%M%S).output
CWD=`pwd`


if [ $install_type == 'pkg' ]; then
    SUDO="sudo"

    DSE_CMD="$SUDO dse "
    DSETOOL_CMD="$SUDO dsetool "
    NODETOOL_CMD="$SUDO nodetool "
    CQLSH_CMD="$SUDO cqlsh "
    CASS_CLI_COMMAND="$SUDO cassandra-cli -h `hostname`"


    if [ $test == "dsc" ]; then
        DEMO_DIR=/usr/share/dsc-demos
        PRICER_CMD="$SUDO $DEMO_DIR/portfolio_manager/bin/pricer "
    else
        DEMO_DIR=/usr/share/dse-demos
        PRICER_CMD="$SUDO $DEMO_DIR/portfolio_manager/bin/pricer "
        HADOOP_EXAMPLES="/usr/share/dse/hadoop/lib/hadoop-examples-*.jar"
    fi

elif [ $install_type == 'tar' ]; then
    SUDO=""

    DSE_HOME=$HOME/dse
    DSE_CMD="$SUDO $DSE_HOME/bin/dse "
    DSETOOL_CMD="$SUDO $DSE_HOME/bin/dsetool "
    NODETOOL_CMD="$SUDO $DSE_HOME/bin/nodetool "
    CQLSH_CMD="$SUDO $DSE_HOME/bin/cqlsh "
    CASS_CLI_COMMAND="$SUDO $DSE_HOME/bin/cassandra-cli -h localhost"

    DEMO_DIR=$DSE_HOME/demos
    PRICER_CMD="$SUDO $DEMO_DIR/portfolio_manager/bin/pricer "
    HADOOP_EXAMPLES="$DSE_HOME/resources/hadoop/hadoop-examples-*.jar"

fi


function run_cmd () {
  run_cmd=$1
  echo
  echo "--------------- Running Command: $run_cmd ---------------"
  echo
  ! $run_cmd  | $SUDO tee $output  
  
  echo
  echo
  echo "*** Return Code of Command: $? ***"
  echo "*** Checking Output for failures ***"
  egrep "ERROR | WARNING | WARN | FAIL | FATAL| Exception" $output

  $SUDO rm $output

  echo
  echo
  echo
  sleep 1
}

function dse_utilities {
  cmdlist[0]="$DSETOOL_CMD ring"
  cmdlist[1]="$DSETOOL_CMD jobtracker"
  cmdlist[2]="$DSE_CMD hive --service help"
  
  for ((i=0; i<${#cmdlist[@]} ;i++)); 
  do
    cmd=${cmdlist[$i]}
    run_cmd "$cmd"
  done
}

function nodetool_test {
  cmd="$NODETOOL_CMD -h `hostname` ring"
  run_cmd "$cmd"
  sleep 2
}


function run_portfolio_demo {
    cmdlist[0]="$PRICER_CMD -o INSERT_PRICES"
    cmdlist[1]="$PRICER_CMD -o UPDATE_PORTFOLIOS"
    cmdlist[2]="$PRICER_CMD -o INSERT_HISTORICAL_PRICES -n 100"
    cmdlist[3]="$DSE_CMD hive -f 10_day_loss.q"
  
    for ((i=0; i<${#cmdlist[@]} ;i++)); 
    do
        cd ${DEMO_DIR}/portfolio_manager

        cmd=${cmdlist[$i]}
        run_cmd "$cmd"
    done
}

function run_terasort {

  cmdlist[0]="$DSE_CMD hadoop jar $HADOOP_EXAMPLES teragen 30 /tmp/terasort-input-${ts}"
  cmdlist[1]="$DSE_CMD hadoop jar $HADOOP_EXAMPLES terasort /tmp/terasort-input-${ts} /tmp/terasort-output-${ts}"
  cmdlist[2]="$DSE_CMD hadoop jar $HADOOP_EXAMPLES teravalidate /tmp/terasort-output-${ts} /tmp/terasort-validate-${ts}"
  cmdlist[3]="$DSE_CMD hadoop fs -lsr cfs:///"
  
  for ((i=0; i<${#cmdlist[@]} ;i++));
  do
    cmd=${cmdlist[$i]}
    run_cmd "$cmd"
  done
}

function run_cql_queries {
  echo
  echo "--------------- Running test: cqlsh ---------------"
  echo

  $CQLSH_CMD localhost <<HERE
  
  DROP KEYSPACE ks1;
  
  CREATE KEYSPACE ks1 with strategy_class =  'org.apache.cassandra.locator.SimpleStrategy' 
  and strategy_options:replication_factor=1;
    
  use ks1;
  
  CREATE COLUMNFAMILY users (
    KEY varchar PRIMARY KEY, password varchar, gender varchar,
    session_token varchar, state varchar, birth_year bigint);
  
  CREATE INDEX gender_key ON users (gender);
  CREATE INDEX state_key ON users (state);
  CREATE INDEX birth_year_key ON users (birth_year);
  
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user1', 'ch@ngem3a', 'f', 'TX', '1968');    
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user2', 'ch@ngem3b', 'm', 'CA', '1971');    
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user3', 'ch@ngem3c', 'f', 'FL', '1978');    
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user4', 'ch@ngem3d', 'm', 'TX', '1974');    
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user5', 'ch@ngem3e', 'f', 'UT', '1968');    
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user6', 'ch@ngem3f', 'f', 'CA', '1971');    
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user7', 'ch@ngem3g', 'f', 'TX', '1982');    
  INSERT INTO users (KEY, password, gender, state, birth_year) VALUES ('user8', 'ch@ngem3h', 'm', 'TX', '1979');    
  
  SELECT * FROM users;
  
  quit;
HERE

  echo
  echo
  echo
}

function run_pig_smoke {
  echo
  echo "--------------- Running test: pig smoke ---------------"
  echo

  # cqlsh data above
  $DSE_CMD pig <<HERE
  usersCF = LOAD 'cassandra://ks1/users' USING CassandraStorage() AS (RowKey, columns: bag {T: tuple(row_key, column_name, value)});
  dump usersCF;
  quit;
HERE
  
  echo
  echo
  echo
}


function run_pig_demo {
  echo
  echo "--------------- Running setup: pig-demo  ---------------"
  echo
  
  $CASS_CLI_COMMAND <<HERE
        drop keyspace PigDemo;
        create keyspace PigDemo with placement_strategy = 'org.apache.cassandra.locator.SimpleStrategy' and strategy_options = [{replication_factor:1}];
        use PigDemo;
        create column family Scores with comparator = 'LongType';
        quit;
HERE
  
  echo
  echo "--------------- Running test: pig-demo  ---------------"
  echo
  
  
  cmdlist[0]="$DSE_CMD hadoop fs -put files/example.txt /"
  cmdlist[1]="$DSE_CMD pig -f 001_sort-by-total-cfs.pig"
  cmdlist[2]="$DSE_CMD pig -f 002_push-data-to-cassandra.pig"
  cmdlist[3]="$DSE_CMD pig -f 003_sort-by-total-cs.pig"
  
  for ((i=0; i<${#cmdlist[@]} ;i++));
  do
    cd $DEMO_DIR/pig

    cmd=${cmdlist[$i]}
    run_cmd "$cmd"
  done
}


function run_wiki_demo {
echo
echo "--------------- Running test: wiki-demo  ---------------"
echo


cmdlist[0]="$SUDO ./1-add-schema.sh"
cmdlist[1]="$SUDO ./2-index.sh --wikifile wikipedia-sample.bz2 --limit 10000"

for ((i=0; i<${#cmdlist[@]} ;i++));
do
    cd $DEMO_DIR/wikipedia
    cmd=${cmdlist[$i]}
    run_cmd "$cmd"
done

cd $CWD

}

function run_logsearch_demo {
echo
echo "--------------- Running test: log-search-demo  ---------------"
echo

cmdlist[0]="$DSETOOL_CMD ring"
cmdlist[1]="$SUDO ./1-*.sh"
cmdlist[2]="$SUDO ./2-*.sh"

for ((i=0; i<${#cmdlist[@]} ;i++));
do
    cd $DEMO_DIR/log_search
    cmd=${cmdlist[$i]}
    run_cmd "$cmd"
    sleep 1
done

cd $CWD

}

function run_solr_stress {
echo
echo "--------------- Running test: solr stress  ---------------"
echo

cmdlist[0]="$DSETOOL_CMD ring"
cmdlist[1]="$SUDO ./1-add-schema.sh"
cmdlist[2]="$SUDO ./2-run-benchmark.sh --clients=2 --loops=2 --type=both"

for ((i=0; i<${#cmdlist[@]} ;i++));
do
cd $DEMO_DIR/solr_stress
cmd=${cmdlist[$i]}
run_cmd "$cmd"
sleep 1
done

cd $CWD

}



## ------- TEST INVOCATION -------

if [ $test == "dsc" ]; then
  nodetool_test
  run_cql_queries
  run_portfolio_demo
elif [ $test = "search" ]; then
  dse_utilities
  run_wiki_demo
  run_logsearch_demo
  run_solr_stress
elif [ $test = "pig" ]; then
  dse_utilities
  run_cql_queries
  run_pig_smoke
  run_pig_demo
elif [ $test = "hive" ]; then
  dse_utilities
  run_portfolio_demo
elif [ $test == "hadoop" ]; then
  dse_utilities
  nodetool_test
  run_portfolio_demo
  run_terasort
  run_cql_queries
  run_pig_smoke
  run_pig_demo
  dse_utilities
fi

