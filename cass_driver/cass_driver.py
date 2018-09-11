import time
import os
import logging
from cassandra.cluster import Cluster, NoHostAvailable
from cassandra.policies import DCAwareRoundRobinPolicy
import cass_queries as cstr
import conf
import threading

CASSANDRA_HOSTS = [os.getenv('CASSANDRA_HOST_ADDRESS', 'localhost')]
CASSANDRA_PORT = os.getenv('CASSANDRA_PORT', 9042)
DC = 'DC1'


table_create_query_dict = {
    conf.TWITTER_TWEET_TABLE_NAME: cstr.q_create_tweet_table_temp.substitute(
        table_name=conf.TWITTER_TWEET_TABLE_NAME),
    conf.TWITTER_FRIEND_TABLE_NAME: cstr.q_create_tweet_friend_table_temp.substitute(
        table_name=conf.TWITTER_FRIEND_TABLE_NAME),
}


class DBDriverConnectionException(Exception):
    pass


class CassandraDriver:
    def __init__(self, keyspace, table_name=None, hosts=('localhost',)):
        self.cluster = None
        self.session = None
        self.hosts = list(hosts)
        self.keyspace = keyspace
        self.table_name = table_name

        logging.info("Creating driver to Cassandra cluster %s with keyspace %s and table %s",
                      self.hosts, self.keyspace, self.table_name)

        try:
            self._create_session()
        except NoHostAvailable as e:
            raise DBDriverConnectionException(e)
        self._create_table()

    def __del__(self):
        self.cluster.shutdown()

    def _create_session(self):
        self.cluster = Cluster(
            self.hosts,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=DC),
            port=CASSANDRA_PORT)

        # create the keyspace if not exist
        self._create_keyspace()
        self.session = self.cluster.connect(self.keyspace)

    def _create_keyspace(self):
        keyspace = self.keyspace
        session = self.cluster.connect()

        rows = session.execute(cstr.Q_SELECT_KEYSPACES)
        keyspace_list = [row[0] for row in rows]
        logging.info("Keyspaces: %s", keyspace_list)
        if keyspace in keyspace_list:
            logging.info("Keyspace %s exists...", keyspace)
            return
        else:
            spec = cstr.q_create_keyspace_temp.substitute(keyspace=keyspace)
            logging.info("Creating keyspace of spec %s...", spec)
            session.execute(spec)

    def _create_table(self):
        logging.info("Creating table %s (if not exist)", self.table_name)
        if self.table_name in table_create_query_dict:
            self.session.execute(table_create_query_dict[self.table_name])
        else:
            logging.error("Creating table %s is not supported", self.table_name)

    def execute(self, query_template, params, is_async=False):
        q = query_template.substitute(params)

        logging.debug("q=%s", q)

        if is_async:
            return self.session.execute_async(q)

        return self.session.execute(q)


# Driver cache
cass_drivers = {}
cass_lock = threading.Lock()


def _get_db_driver(keyspace, table_name):
    cass_lock.acquire()
    try:
        key = (keyspace, table_name)
        if key in cass_drivers:
            cass_driver = cass_drivers[key]
            logging.debug("cass driver exists!")
        else:
            time.sleep(5)  # TODO: Remove!
            cass_driver = CassandraDriver(keyspace, table_name=table_name, hosts=CASSANDRA_HOSTS)
            cass_drivers[key] = cass_driver
            logging.info("Created new cass driver with keyspace %s and table %s!", keyspace, table_name)
    finally:
        cass_lock.release()
    return cass_driver


def get_db_driver(keyspace, table_name):
    """Get the db driver with infinite retrying if catching connection exception."""
    while True:
        try:
            return _get_db_driver(keyspace, table_name)
        except DBDriverConnectionException as e:
            logging.error("Retry in 10 seconds to connect to DB due to connection error: %s", e)
            time.sleep(10)
