import logging

from django.db import connection

logger = logging.getLogger(__name__)


def db_health_check():
    try:
        connection.cursor()
        logger.info("db_health_check OK")
        return True
    except Exception as e:
        logger.error("db_health_check failed: %s", e)
        return False
