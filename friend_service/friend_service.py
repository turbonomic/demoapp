import datetime
import logging
import sys
from os import path
sys.path.append(path.join(path.dirname( path.dirname( path.abspath(__file__))), 'cass_driver'))
import cass_driver  # noqa: E402
from cass_queries import q_select_follows_temp, q_select_followers_temp, q_insert_follows_temp, q_count_follows_temp  # noqa: E402
from cass_conf import TWITTER_MAX_FOLLOWS, TWITTER_KEYSPACE, TWITTER_FRIEND_TABLE_NAME   # noqa: E402


def params(user_id, followee_id=None, created_at=None):
    param_dict = {
        'table_name': TWITTER_FRIEND_TABLE_NAME,
        'user_id': user_id,
    }

    if followee_id is not None:
        param_dict['followee_id'] = followee_id

    if created_at is not None:
        param_dict['created_at'] = created_at

    return param_dict


class FriendService:
    def __init__(self):
        self.db_driver = cass_driver.get_db_driver(TWITTER_KEYSPACE, TWITTER_FRIEND_TABLE_NAME)

    def followees(self, user_id):
        rows = self.db_driver.execute(q_select_follows_temp, params(user_id))
        followees = [row.followee_id for row in rows]
        logging.debug("User %d follows %d users", user_id, len(followees))
        return followees

    def followers(self, user_id):
        rows = self.db_driver.execute(q_select_followers_temp, params(user_id))
        followers = [row.user_id for row in rows]
        logging.debug("User %d has %d followers", user_id, len(followers))
        return followers

    def follows(self, from_id, to_id):
        num_follows = self.count_follows(from_id)
        logging.debug("User %d has %d follows", from_id, num_follows)
        if num_follows >= TWITTER_MAX_FOLLOWS:
            logging.warning("User %d already reached max (%d) follows", from_id, TWITTER_MAX_FOLLOWS)
            # TODO: raise error
            return False
        self.db_driver.execute(q_insert_follows_temp,
                               params(
                                       from_id,
                                       followee_id=to_id,
                                       created_at=int(float(datetime.datetime.now().strftime("%s.%f"))) * 1000,
                                   )
                               )
        return True

    def count_follows(self, user_id):
        rows = self.db_driver.execute(q_count_follows_temp, params(user_id))
        count = [row.system_count_followee_id for row in rows][0]
        logging.debug("User %d has followed %d people", user_id, count)
        return count

