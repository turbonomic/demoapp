import cassandra
import logging
import datetime
import operator
import time
import queue
import sys
from os import path
sys.path.append(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'cass_driver'))
sys.path.append(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'common_service'))
from common_service import options # noqa: E402
import cass_driver  # noqa: E402
from cass_queries import q_insert_tweet_temp, q_select_tweet_latest_tweets_temp  # noqa: E402
from cass_conf import TWITTER_KEYSPACE, TWITTER_TWEET_TABLE_NAME, TWITTER_NEWS_FEED_COUNT, \
    TWITTER_TIMELINE_COUNT, TWITTER_TOTAL_TIMELINE_COUNT  # noqa: E402


def profile(func):
    def wrap(*args, **kwargs):
        start_time = time.time()
        ret = func(*args, **kwargs)
        elapsed_time_ms = (time.time() - start_time) * 1000
        if elapsed_time_ms > 500:
            logging.info('[%s] elapsed_time: %f (ms)' % (func.__name__, elapsed_time_ms))
        else:
            logging.debug('[%s] elapsed_time: %f (ms)' % (func.__name__, elapsed_time_ms))
        return ret

    return wrap


class TweetService:
    def __init__(self, lock):
        self.db_driver = cass_driver.get_db_driver(TWITTER_KEYSPACE, TWITTER_TWEET_TABLE_NAME)
        self.count = 0  # TODO: read from somewhere (e.g., db)
        self.lock = lock

    @profile
    def tweet(self, user_id, content):
        logging.info("User %d tweet" % user_id)
        logging.debug("%d tweets %s" % (user_id, content))
        self.lock.acquire()
        self.count += 1
        tweet_id = self.count
        self.lock.release()

        self._tweet_to_db(user_id, tweet_id, content)
        return tweet_id

    @profile
    def timeline(self, user_id, followees):
        logging.info("User %d timeline" % user_id)
        logging.debug("User %d follows %d people" % (user_id, len(followees)))
        if len(followees) == 0:
            return []
        timeline_map = self._select_tweets_async(followees, TWITTER_TIMELINE_COUNT)
        timeline = []
        tweets_per_user = int(max(TWITTER_TOTAL_TIMELINE_COUNT / len(followees), 2))
        for user in timeline_map:
            timeline += timeline_map[user][:tweets_per_user]

        logging.debug("%d tweets retrieved for timeline of user %d" % (len(timeline), user_id))

        # Sort to have the latest ones first
        timeline.sort(key=operator.itemgetter('created_at'), reverse=True)
        return timeline[:TWITTER_TOTAL_TIMELINE_COUNT]

    @profile
    def news_feed(self, user_id):
        logging.info("User %d news_feed" % user_id)
        tweets = self._select_tweets(user_id, TWITTER_NEWS_FEED_COUNT)
        logging.debug("%d tweets retrieved from user %d" % (len(tweets), user_id))
        logging.debug("tweets: %s", tweets)
        return tweets

    @profile
    def _tweet_to_db(self, user_id, tweet_id, content):
        params = {
            'table_name': TWITTER_TWEET_TABLE_NAME,
            'user_id': user_id,
            'tweet_id': tweet_id,
            'created_at': int(float(datetime.datetime.now().strftime("%s.%f"))) * 1000,
            'content': content,
        }

        self.db_driver.execute(q_insert_tweet_temp, params, is_async=True)

    @profile
    def _select_tweets(self, user_id, count):
        params = {
            'table_name': TWITTER_TWEET_TABLE_NAME,
            'user_id': user_id,
            'count': count,
        }

        retry_count = options.db_query_retry_count
        timeout = options.db_query_timeout_sec
        while True:
            try:
                rows = self.db_driver.execute(q_select_tweet_latest_tweets_temp, params, timeout=timeout)
                return [{
                            'created_at': str(row.created_at),
                            'user_id': str(row.user_id),
                            'content': row.content.encode('utf-8'), # content type is unicode
                        } for row in rows]
            except cassandra.OperationTimedOut as e:
                logging.error("[DB_OperationTimedOut] Select tweets from user %s failed: retry [%d]", str(user_id),
                              retry_count)
                if retry_count > 0:
                    retry_count -= 1
                else:
                    raise e

    @profile
    def _select_tweets_async(self, user_ids, count_per_user):
        retry_count = options.db_query_retry_count
        timeout = options.db_query_timeout_sec
        q = queue.Queue(maxsize=len(user_ids))
        for user_id in user_ids:
            params = {
                'table_name': TWITTER_TWEET_TABLE_NAME,
                'user_id': user_id,
                'count': count_per_user,
            }

            future = self.db_driver.execute(q_select_tweet_latest_tweets_temp, params, is_async=True,
                                            timeout=timeout)
            q.put((user_id, retry_count, future, params))
            logging.debug("Selecting tweets asyncly from user %s", str(user_id))

        rows = {}
        while not q.empty():
            try:
                (user_id, retry_count, future, params) = q.get()
                res = future.result()
                rows[user_id] = [{
                                    'created_at': str(row.created_at),
                                    'user_id': str(row.user_id),
                                    'content': row.content.encode('utf-8'),
                                } for row in res]
                logging.debug("Received tweets asyncly from user %s", str(user_id))
            except cassandra.OperationTimedOut:
                logging.error("[DB_OperationTimedOut] Select tweets from user %s failed: retry [%d]", str(user_id),
                              retry_count)
                if retry_count > 0:
                    future = self.db_driver.execute(q_select_tweet_latest_tweets_temp, params, is_async=True,
                                                    timeout=timeout)
                    q.put((user_id, retry_count - 1, future, params))
            except Exception as e:
                logging.exception("Selecting tweets from user %s failed: %s", str(user_id), e)

        return rows
