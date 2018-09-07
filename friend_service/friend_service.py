import datetime
import logging

import sys
from os import path
sys.path.append(path.join(path.dirname( path.dirname( path.abspath(__file__))), 'cass_driver'))
import cass_driver as db_driver
import cass_queries as dbqueries
import conf


MAX_NUM_FOLLOWEES = conf.TWITTER_MAX_FOLLOWS

TWITTER_KEYSPACE = conf.TWITTER_KEYSPACE
FRIEND_TABLE = conf.TWITTER_FRIEND_TABLE_NAME


def params(user_id, followee_id=None, created_at=None):
    param_dict = {
        'table_name': FRIEND_TABLE,
        'user_id': user_id,
    }

    if followee_id is not None:
        param_dict['followee_id'] = followee_id

    if created_at is not None:
        param_dict['created_at'] = created_at

    return param_dict


class FriendService:
    def __init__(self, db_driver):
        self.db_driver = db_driver

    def followees(self, user_id):
        rows = self.db_driver.execute(dbqueries.q_select_follows_temp, params(user_id))
        followees = [row.followee_id for row in rows]
        logging.debug("User %d follows %d users", user_id, len(followees))
        return followees

    def followers(self, user_id):
        rows = self.db_driver.execute(dbqueries.q_select_followers_temp, params(user_id))
        followers = [row.user_id for row in rows]
        logging.debug("User %d has %d followers", user_id, len(followers))
        return followers

    def follows(self, from_id, to_id):
        num_follows = self.count_follows(from_id)
        logging.debug("User %d has %d follows", from_id, num_follows)
        if num_follows >= MAX_NUM_FOLLOWEES:
            logging.warning("User %d already reached max (%d) follows", from_id, MAX_NUM_FOLLOWEES)
            # TODO: raise error
            return False

        self.db_driver.execute(dbqueries.q_insert_follows_temp,
                                   params(
                                       from_id,
                                       followee_id=to_id,
                                       created_at=int(float(datetime.datetime.now().strftime("%s.%f"))) * 1000,
                                   )
                               )

        return True

    def count_follows(self, user_id):
        rows = self.db_driver.execute(dbqueries.q_count_follows_temp, params(user_id))
        count = [row.system_count_followee_id for row in rows][0]
        logging.debug("User %d has followed %d people", user_id, count)
        return count


db_driver = db_driver.get_db_driver(TWITTER_KEYSPACE, FRIEND_TABLE)

friend_svc = FriendService(db_driver)
