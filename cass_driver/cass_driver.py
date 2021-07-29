import logging
import os
import threading
import time

from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

import cass_conf
import cass_queries as cstr

CASSANDRA_HOSTS = [os.getenv('CASSANDRA_HOST_ADDRESS', 'localhost')]
CASSANDRA_PORT = os.getenv('CASSANDRA_PORT', 9042)
SESSION_POOL_SIZE = int(os.getenv('SESSION_POOL_SIZE', 1))
DC = 'DC1'


table_create_query_dict = {
    cass_conf.TWITTER_TWEET_TABLE_NAME: cstr.q_create_tweet_table_temp.substitute(
        table_name=cass_conf.TWITTER_TWEET_TABLE_NAME),
    cass_conf.TWITTER_FRIEND_TABLE_NAME: cstr.q_create_tweet_friend_table_temp.substitute(
        table_name=cass_conf.TWITTER_FRIEND_TABLE_NAME),
    cass_conf.TWITTER_SESSION_TABLE_NAME: cstr.q_create_session_table_temp.substitute(
        table_name=cass_conf.TWITTER_SESSION_TABLE_NAME),
}


class DBDriverConnectionException(Exception):
    pass


class CassandraDriver:
    def __init__(self, keyspace, table_name=None, hosts=('localhost',)):
        self.cluster = None
        self.session = None
        self.session_pool = []
        self.hosts = list(hosts)
        self.keyspace = keyspace
        self.table_name = table_name
        self.session_idx = 0

        logging.info("Creating driver to Cassandra cluster %s with keyspace %s and table %s",
                      self.hosts, self.keyspace, self.table_name)

        try:
            self._create_session()
        except Exception as e:
            raise DBDriverConnectionException(e)
        self._create_table()

    def __del__(self):
        if self.cluster is not None:
            self.cluster.shutdown()

    def _get_session(self):
        self.session_idx = (self.session_idx + 1) % len(self.session_pool)
        logging.debug("session_idx=%d", self.session_idx)
        return self.session_pool[self.session_idx]

    def _create_session(self):
        self.cluster = Cluster(
            self.hosts,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=DC),
            port=CASSANDRA_PORT)

        # create the keyspace if not exist
        self._create_keyspace()
        self.session = self.cluster.connect(self.keyspace)
        self.session_pool.append(self.cluster.connect(self.keyspace))

        # create multiple sessions
        for i in range(SESSION_POOL_SIZE - 1):
            cluster = Cluster(
                self.hosts,
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=DC),
                port=CASSANDRA_PORT)
            self.session_pool.append(cluster.connect(self.keyspace))

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

    def execute(self, query_template, params, is_async=False, timeout=None):
        q = query_template.substitute(params)

        logging.debug("q=%s", q)

        session = self._get_session()
        f = session.execute_async if is_async else session.execute
        return f(q, timeout=timeout) if timeout else f(q)


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
