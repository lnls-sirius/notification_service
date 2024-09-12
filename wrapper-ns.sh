#!/bin/bash

# Start the first process
./gunicorn -k gevent -b 10.20.31.144:5000 'notificationservice:app' &

# Start the second process
./python monitor.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?