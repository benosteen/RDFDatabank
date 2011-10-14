#!/bin/bash
su databankadmin --command "exec /usr/local/bin/supervisord -c /opt/workers/supervisord.conf"

