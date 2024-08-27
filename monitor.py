#!./venv/bin/python
from utils import makepvlist, connect_pvs, post_test_notification, pre_test_notification, show_running, byebye, prepare_evaluate, ns_queuer, writer
from epics import PV
from time import sleep
from symbols import *
from datetime import datetime as dt
from db import * #App_db, FullPVList
import os
from psutil import Process as ps_proc
from multiprocessing import Process, Value, Manager
from ctypes import c_bool
from copy import deepcopy as dp
from utils import call_wapp as cw

def evaluate():
    # make full PV list and create modem object
    f = FullPVList()
    fullpvlist, modem = prepare_evaluate(f)
    loop_index = 0
    print("Running!")
    # load notification db
    app_notifications = App_db("notifications")
    pvs_dict = dict()
    n_queue = Manager().list()
    writer_queue = Manager().list()
    system_errors = Manager().list()
    busy_modem =  Value(c_bool, False)
    busy_wapp = Value(c_bool, False)
    busy_call_admin = Value(c_bool, False)
    exit = Value(c_bool, False)
    p1 = Process(target=ns_queuer, args=(n_queue, writer_queue, busy_modem, busy_wapp, exit, system_errors, busy_call_admin), name="ns_queuer")
    p1.start()
    p2 = Process(target=writer, args=(writer_queue, exit), name="ns_writer")
    p2.start()

    while True:
        try:
            # create pv list with all pvs used in db
            allpvs = makepvlist(fullpvlist, app_notifications)
            # create dictionary of PV objects
            connect_pvs(allpvs, pvs_dict)
            # get notifications from db
            notifications_raw = app_notifications.get()
            if isinstance(notifications_raw, Exception):
                print("Error on getting notifications DB: ", notifications_raw)
                break
            # for each notification
            for n in notifications_raw:
                now = dt.now()
                # test condition outside notification rules
                can_send = pre_test_notification(n, now)
                if can_send:
                    # test conditions inside notification rules
                    ans = post_test_notification(n, pvs_dict)
                    if ans["send_sms"]:
                        # send SMS to phone number and write to log.txt
                        users_db = App_db("users")
                        update_db= True # update notification database
                        update_log = True # write to log.txt
                        no_text = False # force notification text to none
                        send_sms = False # send through modem and whatsapp
                        send_wapp = True
                        print_msg=False #print sent sms text to terminal
                        byebye(ans, n, now, app_notifications, users_db, update_db=update_db, update_log=update_log, no_text=no_text, send_sms=send_sms, send_wapp=send_wapp, print_msg=print_msg, queue=n_queue)
            # print 'running' symbol each iteration
            show_running(loop_index) # printing running sign
            loop_index += 1

            sleep(0.15)

        except KeyboardInterrupt:
            break

    exit.value = True

evaluate()
