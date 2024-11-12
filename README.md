Notification Service

====================

These are the files of the Notification Service system, meant to be operated at SIRIUS facility.

It is a system for notification delivery to the users, initially using a SMS modem, with WhatsApp and Microsoft Teams planned to be implemented in the future.

The system is composed of two parts: the web interface for the user to input desired notifications and a system of evaluation for those notifications.

The web interface was made using Flask's framework and a Python backend. For HTML style, we use Bootstrap, CSS, and some javascript. Our database is made in SQLite. Through the web interface, the user creates a notification, that is linked to his account. This notification is saved in a database, which is used in the evaluation system.

The evaluation system runs in a script called monitor.py. It is constantly evaluating each notification in the database in order to send the notification to the user when it meets all criteria.

Each of these parts run in a separated container. The commands to run each are commented in the dockerfiles Dockerfile.ns-flask (to run the web interface) and Dockerfile.ns-monitor (evaluation system)

For the flask part, it's needed just to create the image and run the docker.

For the monitor part, first you need to initialize the database, in order to have the required files in the correct folders. Make sure to create the folder /opt/notification_service/db. After that, uncomment the entrypoint in the dockerfile and create the image, running the docker afterwards.

For both, you need to have the SMS dongle installed and its service stopped in the computer.