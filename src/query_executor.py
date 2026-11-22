import threading


def execute_with_timeout(con, sql, timeout_seconds=5):
    timer = threading.Timer(timeout_seconds, con.interrupt)
    timer.start()

    try:
        return con.execute(sql).fetchdf()
    finally:
        timer.cancel()