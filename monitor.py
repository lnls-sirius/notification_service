#!./venv/bin/python
from utils import makepvlist, connect_pvs, post_test_notification, pre_test_notification, show_running, byebye, prepare_evaluate, ns_queuer, writer
from time import sleep
from symbols import *
from datetime import datetime as dt
from db_app import FullPVList as fpvlist, App_db as app_db_
from multiprocessing import Process, Value, Manager
from ctypes import c_bool


def evaluate():
    # make full PV list and create modem object
    f = fpvlist()
    test_mode = False
    fullpvlist = prepare_evaluate(f, test_mode=test_mode)
    loop_index = 0
    # load notification db
    app_notifications = app_db_("notifications")
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

    first_iteration = True

    while True:
        try:
            if first_iteration:
                do_print = True
            # create pv list with all pvs used in db
            allpvs = makepvlist(fullpvlist, app_notifications)
            # create dictionary of PV objects
            if isinstance(allpvs, Exception):
                sleep(1)
                continue
            connect_pvs(allpvs, pvs_dict, do_print)
            if first_iteration:
                do_print = False
                first_iteration = False
                print("Running!")
            # get notifications from db
            notifications_raw = app_notifications.get()
            if isinstance(notifications_raw, Exception):
                sleep(1)
                continue
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
                        users_db = app_db_("users")
                        update_db= True # update notification database
                        update_log = True # write to log.txt
                        no_text = False # force notification text to none
                        # set to send or not through modem
                        send_sms = (False if test_mode else True)
                        send_wapp = False # set to send or not through WhatsApp
                        print_msg = True #print sent sms text to terminal
                        ans = byebye(ans, n, now, users_db, update_db=update_db, update_log=update_log, no_text=no_text, send_sms=send_sms, send_wapp=send_wapp, print_msg=print_msg, queue=n_queue)
                        if isinstance(ans, Exception):
                            sleep(1)
                            continue
            app_notifications.close()

            # print 'running' symbol each iteration
            show_running(loop_index) # printing running sign
            loop_index += 1

            sleep(1)

        except KeyboardInterrupt:
            break

    exit.value = True

evaluate()
