import time
import os
import logging
from cassandra.cluster import Cluster
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


class CassandraDriver:
    def __init__(self, keyspace, table_name=None, hosts=('localhost',), log=None):
        self.cluster = None
        self.session = None
        self.hosts = list(hosts)
        self.keyspace = keyspace
        self.table_name = table_name
        self.log = log

        self.log.info("Creating driver to Cassandra cluster %s with keyspace %s and table %s",
                      self.hosts, self.keyspace, self.table_name)

        self._create_session()
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
        self.log.info("Keyspaces: %s", keyspace_list)
        if keyspace in keyspace_list:
            self.log.info("Keyspace %s exists...", keyspace)
            return
        else:
            spec = cstr.q_create_keyspace_temp.substitute(keyspace=keyspace)
            self.log.info("Creating keyspace of spec %s...", spec)
            session.execute(spec)

    def _create_table(self):
        self.log.info("Creating table %s (if not exist)", self.table_name)
        if self.table_name in table_create_query_dict:
            self.session.execute(table_create_query_dict[self.table_name])
        else:
            self.log.error("Creating table %s is not supported", self.table_name)

    def execute(self, query_template, params, async=False):
        q = query_template.substitute(params)

        logging.info("q=%s", q)

        if async:
            return self.session.execute_async(q)

        return self.session.execute(q)


logger = logging.getLogger()
logger.setLevel('INFO')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(handler)


# Driver cache
cass_drivers = {}
cass_lock = threading.Lock()


def get_db_driver(keyspace, table_name):
    cass_lock.acquire()
    key = (keyspace, table_name)
    if key in cass_drivers:
        cass_driver = cass_drivers[key]
        logger.debug("cass driver exists!")
    else:
        time.sleep(5)  # TODO: Remove!
        cass_driver = CassandraDriver(keyspace, table_name=table_name, hosts=CASSANDRA_HOSTS, log=logger)
        cass_drivers[key] = cass_driver
        logger.info("Created new cass driver with keyspace %s and table %s!", keyspace, table_name)
    cass_lock.release()
    return cass_driver


# if __name__ == '__main__':
#     # CassandraDriver(KEYSPACE).drop_keyspace(KEYSPACE)
#     print("\n======== Started connecting to Cassandra cluster with keyspace %s ========\n" % conf.TWITTER_KEYSPACE)
#     driver = get_db_driver(conf.TWITTER_KEYSPACE, conf.TWITTER_TWEET_TABLE_NAME)
#
#     # print("\n======== Started %d write operations from keyspace %s ========\n" % (NUM_WRITE_REQUESTS, KEYSPACE))
#     #
#     # print("\n======== Started %d read operations from keyspace %s ========\n" % (NUM_READ_REQUESTS, KEYSPACE))
