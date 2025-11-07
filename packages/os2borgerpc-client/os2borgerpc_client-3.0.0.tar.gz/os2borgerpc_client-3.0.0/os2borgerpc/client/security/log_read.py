"""log_read module."""

from datetime import datetime


def read(last_security_check, log_name):
    """Search a (system) log for events that occurred between "last_security_check" and now."""
    log_event_tuples = []
    now = datetime.now()

    with open(log_name) as f:
        for line in f.readlines():
            line = line.replace("\0", "").strip("\n")
            try:
                log_event_timestamp = line[:15]
                log_event = line
                # convert from log event timestamp to security event log timestamp.
                log_event_datetime = datetime.strptime(
                    str(now.year) + " " + log_event_timestamp, "%Y %b  %d %H:%M:%S"
                )
            except ValueError:
                log_event_timestamp = line[:19]
                log_event = line
                # convert from log event timestamp to security event log timestamp.
                log_event_datetime = datetime.strptime(
                    log_event_timestamp, "%Y-%m-%dT%H:%M:%S"
                )
            security_event_log_timestamp = datetime.strftime(
                log_event_datetime, "%Y%m%d%H%M%S"
            )
            # Detect lines from within the last x seconds to now.
            if last_security_check <= log_event_datetime <= now:
                log_event_tuples.append((security_event_log_timestamp, log_event))

    return log_event_tuples
