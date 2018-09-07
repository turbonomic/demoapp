import logging
import datetime
import threading
import operator
import time

import sys
from os import path
sys.path.append(path.join(path.dirname( path.dirname( path.abspath(__file__))), 'cass_driver'))
import cass_driver as db_driver
import cass_queries as dbqueries
import conf

TWITTER_KEYSPACE = conf.TWITTER_KEYSPACE
TWEET_TABLE = conf.TWITTER_TWEET_TABLE_NAME
NEWS_FEED_COUNT = conf.TWITTER_NEWS_FEED_COUNT
TIMELINE_COUNT = conf.TWITTER_TIMELINE_COUNT
TOTAL_TIMELINE_COUNT = conf.TWITTER_TOTAL_TIMELINE_COUNT


def profile(func):
    def wrap(*args, **kwargs):
        start_time = time.time()
        ret = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logging.info('[%s] elapsed_time: %f (seconds)' % (func.__name__, elapsed_time))
        return ret
    return wrap


class TweetService:
    def __init__(self, db_driver, lock):
        self.db_driver = db_driver
        self.count = 0 # TODO: read from somewhere (e.g., db)
        self.lock = lock

    def tweet(self, user_id, content):
        logging.info("%d tweets %s" % (user_id, content))
        self.lock.acquire()
        self.count += 1
        tweet_id = self.count
        self.lock.release()

        self._tweet_to_db(user_id, tweet_id, content)
        return tweet_id

    def timeline(self, user_id, followees):
        logging.debug("User %d follows %d people" % (user_id, len(followees)))
        timeline = self._select_tweets_async(followees, TIMELINE_COUNT)

        logging.info("%d tweets retrieved for timeline of user %d" % (len(timeline), user_id))

        # Sort to have the latest ones first
        timeline.sort(key=operator.itemgetter('created_at'), reverse=True)
        return timeline[:TOTAL_TIMELINE_COUNT]

    def news_feed(self, user_id):
        tweets = self._select_tweets(user_id, NEWS_FEED_COUNT)
        logging.info("%d tweets retrieved from user %d" % (len(tweets), user_id))
        logging.debug("tweets: %s", tweets)
        return tweets

    def _tweet_to_db(self, user_id, tweet_id, content):
        params = {
            'table_name': TWEET_TABLE,
            'user_id': user_id,
            'tweet_id': tweet_id,
            'created_at': int(float(datetime.datetime.now().strftime("%s.%f"))) * 1000,
            'content': content,
        }

        self.db_driver.execute(dbqueries.q_insert_tweet_temp, params, is_async=True)

    @profile
    def _select_tweets(self, user_id, count):
        params = {
            'table_name': TWEET_TABLE,
            'user_id': user_id,
            'count': count,
        }

        rows = self.db_driver.execute(dbqueries.q_select_tweet_latest_tweets_temp, params)

        return [{
                    'created_at': str(row.created_at),
                    'user_id': str(row.user_id),
                    'content': row.content.encode('utf-8'), # content type is unicode
                } for row in rows]

    @profile
    def _select_tweets_async(self, user_ids, count_per_user):
        future_dict = {}
        for user_id in user_ids:
            params = {
                'table_name': TWEET_TABLE,
                'user_id': user_id,
                'count': count_per_user,
            }

            future = self.db_driver.execute(dbqueries.q_select_tweet_latest_tweets_temp, params, is_async=True)
            future_dict[user_id] = future
            logging.debug("Select tweets asyncly from user %s", str(user_id))

        rows = []
        for user_id in user_ids:
            try:
                res = future_dict[user_id].result()
                rows += res
                logging.info("Received tweets asyncly from user %s", str(user_id))
            except Exception:
                logging.exception("Select tweets from user %s failed", str(user_id))

        return [{
                    'created_at': str(row.created_at),
                    'user_id': str(row.user_id),
                    'content': row.content.encode('utf-8'),
                } for row in rows]


driver = db_driver.get_db_driver(TWITTER_KEYSPACE, TWEET_TABLE)

tweet_svc = TweetService(driver, threading.Lock())
