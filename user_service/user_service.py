import logging
import time
import os
import hashlib


# https://github.com/treyhunner/names/tree/f99542dc21f48aa82da4406f8ce408e92639430d/names
NAME_LIST_FILENAME = 'files/dist.all.last.txt'

session_cache = {}


def mock_password(user_id):
    return 'pw' + str(user_id)


class UserService:
    def __init__(self):
        self.names = {}
        dirpath = os.path.dirname(os.path.realpath(__file__))
        filename = dirpath + "/" + NAME_LIST_FILENAME
        self._load_name_dict(filename)
        self.name_count = len(self.names)
        logging.info("Loaded %d names from %s", self.name_count, filename)

    def _load_name_dict(self, filename):
        time.sleep(3) # TODO: Remove it!
        i = 0
        with open(filename) as name_file:
            for line in name_file:
                i += 1
                name = line.strip().split(" ")[0]
                self.names[i] = name

    def name(self, user_id):
        username = self.names.get((user_id % self.name_count) + 1, "NONAME")
        idx = user_id // self.name_count
        if idx > 0:
            username += "-" + str(idx)
        return username

    def check_session(self, user_id, key):
        return session_cache.get(key) == user_id

    def remove_session(self, key):
        if key in session_cache:
            del session_cache[key]
            return True

        return False

    def check_password(self, user_id, password):
        ok = password == mock_password(user_id)
        session_key = ''

        if ok:
            hash_object = hashlib.sha256(str(user_id) + password)
            session_key = hash_object.hexdigest()
            session_cache[session_key] = user_id

        return ok, session_key

user_svc = UserService()
