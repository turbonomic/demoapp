import argparse
from concurrent import futures
import grpc
import logging

DB_QUERY_RETRY_COUNT = 5
DB_QUERY_TIMEOUT_SEC = 5
MAX_WORKER = 10

# Command line options
parser = argparse.ArgumentParser()
parser.add_argument(
    "--log",
    default="info",
    help=(
        "specify logging level "
        "[default='info']"
    ),
)
parser.add_argument(
    "--grpc-max-connection-age-ms",
    type=int,
    help=(
        "specify maximum time that the server channel may exist in milliseconds "
        "[default=None]"
    ),
)
parser.add_argument(
    "--db-query-timeout-sec",
    default=DB_QUERY_TIMEOUT_SEC,
    type=int,
    help=(
            "specify database query timeout in seconds "
            "[default=" + str(DB_QUERY_TIMEOUT_SEC) + "]"
    ),
)
parser.add_argument(
    "--db-query-retry-count",
    default=DB_QUERY_RETRY_COUNT,
    type=int,
    help=(
            "specify data query retry count "
            "[default=" + str(DB_QUERY_RETRY_COUNT) + "]"
    ),
)
options = parser.parse_args()
levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}
level = levels.get(options.log.lower())
if level is None:
    raise ValueError(
        f"log level given: {options.log}"
        f" -- must be one of: {' | '.join(levels.keys())}"
    )
if options.grpc_max_connection_age_ms is not None and options.grpc_max_connection_age_ms <= 0:
    raise ValueError(
        f"grpc-max-connection-age-ms given: {options.grpc_max_connection_age_ms}"
        f" -- must be a positive integer"
    )

# Set up logging
logging.basicConfig(level=level)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(module)s] [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(handler)
logging.info('Logging level %d' % level)
logging.info('Server grpc.max_connection_age_ms %s' % options.grpc_max_connection_age_ms)
logging.info('DB query timeout sec %d' % options.db_query_timeout_sec)
logging.info('DB query retry count %d' % options.db_query_retry_count)


def create_grpc_server(port):
    if options.grpc_max_connection_age_ms is None:
        logging.info("Creating GRPC server with %d workers" % MAX_WORKER)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKER))
    else:
        logging.info("Creating GRPC server with %d workers and grpc.max_connection_age_ms %d" %
                     (MAX_WORKER, options.grpc_max_connection_age_ms))
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=MAX_WORKER),
            options=(('grpc.max_connection_age_ms', options.grpc_max_connection_age_ms),)
        )
    server.add_insecure_port('[::]:' + str(port))
    return server
