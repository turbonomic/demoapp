from string import Template

Q_SELECT_KEYSPACES = "SELECT keyspace_name FROM system_schema.keyspaces"

q_create_keyspace_temp = Template("""
                    CREATE KEYSPACE $keyspace
                    WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '1' }
                    """)

q_create_tweet_table_temp = Template("""
                CREATE TABLE IF NOT EXISTS $table_name (user_id int,
                                                        tweet_id int,
                                                        created_at timestamp,
                                                        content varchar,
                                                        primary key (user_id, created_at, tweet_id));
                 """)

q_insert_tweet_temp = Template("""
                INSERT INTO $table_name (user_id, tweet_id, created_at, content)
                VALUES ($user_id, $tweet_id, $created_at, '$content')
                """)

q_select_tweet_latest_tweets_temp = Template("""
                SELECT * FROM $table_name WHERE user_id=$user_id ORDER BY created_at DESC LIMIT $count;
                """)

q_create_tweet_friend_table_temp = Template("""
                CREATE TABLE IF NOT EXISTS $table_name (user_id int,
                                                        followee_id int,
                                                        created_at timestamp,
                                                        primary key (user_id, followee_id));
                 """)

q_insert_follows_temp = Template("""
                INSERT INTO $table_name (user_id, followee_id, created_at)
                VALUES ($user_id, $followee_id, $created_at)
                """)

q_select_follows_temp = Template("""
                SELECT followee_id FROM $table_name WHERE user_id=$user_id;
                """)

q_count_follows_temp = Template("""
                SELECT count(followee_id) FROM $table_name WHERE user_id=$user_id;
                """)

# cassandra.InvalidRequest: Error from server: code=2200 [Invalid query] message="Cannot execute this query as it
# might involve data filtering and thus may have unpredictable performance. If you want to execute this query despite
# the performance unpredictability, use ALLOW FILTERING"
q_select_followers_temp = Template("""
                SELECT user_id FROM $table_name WHERE followee_id=$user_id ALLOW FILTERING;
                """)
# CREATE TABLE IF NOT EXISTS testtable (session_id varchar, login boolean, user_id int, created_at timestamp, primary key (session_id, created_at));

q_create_session_table_temp = Template("""
                CREATE TABLE IF NOT EXISTS $table_name (session_id varchar,
                                                        login boolean,
                                                        user_id int,
                                                        created_at timestamp,
                                                        primary key (session_id, created_at));
                 """)

q_insert_session_temp = Template("""
                INSERT INTO $table_name (session_id, login, user_id, created_at)
                VALUES ('$session_id', $login, $user_id, $created_at)
                """)

q_select_session_temp = Template("""
                SELECT * FROM $table_name WHERE session_id='$session_id' ORDER BY created_at DESC LIMIT 1;
                """)
