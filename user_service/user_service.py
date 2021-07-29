import logging
import time
import hashlib
import datetime
import sys
from os import path

sys.path.append(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'cass_driver'))
import cass_driver  # noqa: E402
from cass_queries import q_select_session_temp, q_insert_session_temp  # noqa: E402
from cass_conf import TWITTER_KEYSPACE, TWITTER_SESSION_TABLE_NAME  # noqa: E402

# https://github.com/treyhunner/names/tree/f99542dc21f48aa82da4406f8ce408e92639430d/names
NAME_LIST_FILENAME = 'files/dist.all.last.txt'


def mock_password(user_id):
    return str(user_id)


def params(session_id, login=True, user_id=-1):
    param_dict = {
        'table_name': TWITTER_SESSION_TABLE_NAME,
        'session_id': session_id,
        'created_at': int(float(datetime.datetime.now().strftime("%s.%f"))) * 1000,
        'login': login,
        'user_id': user_id,
    }

    return param_dict


class UserService:
    def __init__(self):
        self.db_driver = cass_driver.get_db_driver(TWITTER_KEYSPACE, TWITTER_SESSION_TABLE_NAME)
        self._names = {}
        dir_path = path.dirname(path.realpath(__file__))
        filename = dir_path + "/" + NAME_LIST_FILENAME
        self._load_name_dict(filename)
        self.name_count = len(self._names)
        logging.info("Loaded %d names from %s", self.name_count, filename)

    def _load_name_dict(self, filename):
        time.sleep(3)  # TODO: Remove it!
        i = 0
        with open(filename) as name_file:
            for line in name_file:
                i += 1
                name = line.strip().split(" ")[0]
                self._names[i] = name

    def get_name(self, user_id):
        username = self._names.get((user_id % self.name_count) + 1, "NONAME")
        idx = user_id // self.name_count
        if idx > 0:
            username += "-" + str(idx)
        return username

    def get_names(self, user_ids):
        return list(map(self.get_name, user_ids))

    def check_session(self, user_id, session_id):
        (uid, login) = self._select_session(session_id)
        return uid == user_id and login

    def remove_session(self, session_id):
        return self._insert_session(session_id, login=False)

    def check_password(self, user_id, password):
        ok = password == mock_password(user_id)
        session_id = ''

        if ok:
            key = str(user_id) + password
            session_id = hashlib.sha256(key.encode('utf-8')).hexdigest()
            self._insert_session(session_id, user_id)

        return ok, session_id

    def _select_session(self, session_id):
        rows = self.db_driver.execute(q_select_session_temp, params(session_id))
        users = [(row.user_id, row.login) for row in rows]
        (user_id, login) = users[0] if len(users) else (None, None)
        logging.debug("Selected session id %s for user %s with login=%s", str(session_id), str(user_id), str(login))
        return user_id, login

    def _insert_session(self, session_id, user_id=-1, login=True):
        self.db_driver.execute(q_insert_session_temp, params(session_id, login, user_id))
        logging.info("Inserted session id %s for user %s", str(session_id), str(user_id))

