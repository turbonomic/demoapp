import logging
from functools import wraps

from user_service import user_svc
from tweet_service import tweet_svc
from friend_service import friend_svc

from flask import Flask, jsonify, abort, make_response, render_template, flash, redirect, url_for, request

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8699

SESSION_KEY = 'session_key'
USER_ID = 'user_id'

app = Flask(__name__)
app.secret_key = "super very so secret key"


def check_session(cookies):
    if SESSION_KEY in cookies and USER_ID in cookies:
        user_id = cookies.get(USER_ID)
        session_key = cookies.get(SESSION_KEY)
        logging.info("=userid, session: %s, %s", user_id, session_key)
        if user_svc.check_session(int(user_id), session_key):
            return True

    logging.info("check session false: %s", cookies)
    return False


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        logging.info("cookie: %s", request.cookies)
        logging.info("logged_in: %s", request.cookies.get('logged_in'))
        if check_session(request.cookies):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrap


@app.route('/')
@login_required
def index():
    user_id = request.cookies.get(USER_ID)
    logging.info("user %s has cookie: %s", user_id, request.cookies)
    return redirect(url_for('newsfeed'))


@app.route('/setcookie', methods=['POST', 'GET'])
def setcookie():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']

    resp = make_response(redirect(url_for('index')))

    ok, session_key = user_svc.check_password(int(user), pw)

    logging.info("check password: %s, %s", str(ok), session_key)

    if ok:
        resp.set_cookie(SESSION_KEY, session_key)
        resp.set_cookie(USER_ID, user)

        logging.info("cookie: %s", request.cookies)
        flash('You were successfully logged in')
    else:
        flash('Logged in failed! Invalid user ID or password.')

    return resp


@app.route('/login', methods=['GET', 'POST'])
def login():
    if check_session(request.cookies):
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session_key = request.cookies.get(SESSION_KEY)
    user_svc.remove_session(session_key)

    resp = make_response(redirect(url_for('index')))
    resp.set_cookie(SESSION_KEY, '', expires=0)
    logging.info("cookie: %s", request.cookies)

    flash('You were successfully logged out')

    return resp


@app.route('/timeline', methods=['GET'])
@login_required
def timeline():
    user_id = request.cookies.get(USER_ID)
    user_id = int(user_id)
    logging.info('User %d requests timeline', user_id)
    followees = friend_svc.followees(user_id)
    logging.info('User %d is followed by %d users', user_id, len(followees))
    tweets = tweet_svc.timeline(user_id, followees)
    for t in tweets:
        t['user_name'] = user_svc.name(int(t['user_id']))

    return render_template('twitter.html', title='MaxTurboTwitter', user_name=user_svc.name(user_id), tweets=tweets)


@app.route('/newsfeed', methods=['GET'])
@login_required
def newsfeed():
    user_id = request.cookies.get(USER_ID)
    user_id = int(user_id)
    logging.info('User %d requests news feed', user_id)
    tweets = tweet_svc.news_feed(user_id)
    for t in tweets:
        t['user_name'] = user_svc.name(user_id)

    return render_template('twitter.html', title='MaxTurboTwitter', user_name=user_svc.name(user_id), tweets=tweets)


@app.route('/tweet', methods=['POST'])
@login_required
def tweet():
    user_id = request.cookies.get(USER_ID)
    user_id = int(user_id)
    content = request.form['content']
    logging.info('User %d said %s', user_id, str(content))
    tweet_id = tweet_svc.tweet(user_id, content)
    logging.info('User %d said with tweet id %d', user_id, tweet_id)
    return redirect(url_for('newsfeed'))


@app.route('/follows', methods=['POST'])
@login_required
def follows():
    from_id = request.cookies.get(USER_ID)
    from_id = int(from_id)
    to_id = int(request.form['id_to_follow'])
    logging.info('User %d requests following user %d', from_id, to_id)
    if from_id == to_id:
        return make_response("Invalid followee id {}".format(to_id), 400)

    done = friend_svc.follows(from_id, to_id)

    if done:
        flash('You followed {}'.format(user_svc.name(to_id)))
        return redirect(url_for('index'))
    else:
        # TODO: correct the http status code
        return make_response("User {} alread reached max follows".format(user_svc.name(from_id)), 200)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel('INFO')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)

    logging.info("Strating HTTP server...")

    app.run(host=SERVER_HOST,
            port=SERVER_PORT,
            threaded=True,
            debug=False)
