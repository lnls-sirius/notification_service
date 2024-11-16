#!./venv/bin/python
"""Useful functions."""

from epics import PV, cainfo
from classes import NotificationInfoByPV
import symbols, json, re
from time import sleep
from copy import deepcopy
from datetime import datetime, timedelta
from json import loads
from db_app import *
from iofunctions import current_path as cpath, write, fromcfg
from modem_usb import Modem
from multiprocessing import Process
from psutil import process_iter
from datetime import datetime as dt
# from pywhatkit import sendwhatmsg_instantly as send_wapp_


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d


def makepvlist(fullpvlist, app_notifications):
    """Returns a lisf of string PV names, without duplicates."""
    try:
        pvlist = []
        notifications_raw = app_notifications.get()
        for item in notifications_raw:
            item = row2dict(item)
            i = 0
            n = json.loads(json.dumps(item))
            notification = json.loads(n[symbols.notification])
            for key in notification[symbols.notificationCores]:
                nC = symbols.notificationCore + str(i)
                comp_regex = re.compile(symbols.BGNCHAR + key[nC][symbols.pv + str(i)] + symbols.ENDCHAR)
                filterlist = list(filter(comp_regex.match, fullpvlist))
                for pv in filterlist:
                    if pv not in pvlist:
                        pvlist.append(pv)
                i += 1
    except Exception as e:
        print('Error on making PV list: ', e)
    return pvlist


def makepvpool(fullpvlist, app_notifications):
    """Returns a lisf of NotoficationInfoByPV classes."""
    pvpool = []
    notifications_db = app_notifications #App_db(symbols.Notifications)
    notifications_raw = symbols.notifications_raw
    j = 0
    for item in notifications_raw:
        i = 0
        n = str(item.get(symbols.notification))
        notification = json.loads(n)
        for core in notification[symbols.notificationCores]:
            nC = symbols.notificationCore + str(i)
            comp_regex = re.compile(symbols.BGNCHAR + core[nC][symbols.pv + str(i)] + symbols.ENDCHAR)
            filterlist = list(filter(comp_regex.match, fullpvlist))
            lim = symbols.limit + str(i)
            for element in filterlist:
                pvinfo = NotificationInfoByPV()
                pvinfo.notification_id = item[symbols.id]
                for nc in core.keys():
                    pvinfo.notificationCore = int(nc[-1])
                pvinfo.user_id = item[symbols.user_id]
                pvinfo.pv = element
                if core[nC].get(lim) is not None:
                    pvinfo.limit = core[nC][symbols.limit + str(i)]
                else:
                    pvinfo.limitLL = core[nC][symbols.limitLL + str(i)]
                    pvinfo.limitLU = core[nC][symbols.limitLU + str(i)]
                pvinfo.rule = core[nC][symbols.rule + str(i)]
                pvinfo.subrule = core[nC][symbols.subrule + str(i)]
                pvpool.append(pvinfo)
            i += 1
        j += 1
    return pvpool


def connect_pvs(allpvs, pvs_dict):
    # build up pv dictionary
    for pvname in allpvs:
        # if pv not in dictionary
        if pvname not in pvs_dict:
            # add to dictionary
            pvs_dict[pvname] = PV(pvname)
            if not PV(pvname).connected:
                PV(pvname).connect()
    # clean up unused PV objects
    # because dict can't be changed during iteration, turned it to list
    for key in list(pvs_dict):
        # if dictionary key name not in list
        if key not in allpvs:
            # delete dictionary key
            del pvs_dict[key]


def get_enum_list(pv):
    ans3 = ''
    try:
        ans = cainfo(str(pv), print_out=True)
        if ans != '' and ans != None and 'enum strings:' in ans:
            ans2 = (ans.split('enum strings:')[-1])
            ans3 = ans2.split('\n')[1:-2]
        else:
            return
    except Exception as e:
        # print('e', e)
        return 'PV data not available'
    aux = []
    if ans3 != '' and ans3 is not None:
        for element in ans3:
            aux3 = element.strip()
            aux4 = aux3.replace(' ', '')
            aux5 = aux4.replace('\n', '')
            aux6 = aux5.replace('\t', '')
            aux7 = aux6.replace('\r', '')
            aux8 = aux7.replace('=', ' = ')
            aux.append(aux8)
        aux = '\n'.join(aux)
        if type(aux) == str:
            return aux
        else:
            return None
    else:
        return None


def post_test_notification(n, pvs_dict):
    """test if notification rules evaluates to true."""
    fullpvlist = list(pvs_dict.keys())
    notification = n[symbols.notification]
    notification_json = json.loads(notification)
    nc = notification_json[symbols.notificationCores]
    test_results = {"send_sms":False, "sizetrue": 0, "faulty":None, "pvs":{}}
    L, LL, LU = None, None, None
    complete_rule = []
    faulty = []
    pv = None
    try:
        for core in nc:
            rule_array = []
            true_pvs = {}
            true_pvs_array = []
            partial_rule = ""
            core_number = list(core.keys())[0].split("notificationCore", 1)[1]
            core_inner = core[symbols.notificationCore + core_number]
            pv_in_notification = (core_inner[symbols.pv + core_number]).strip()
            comp_regex = re.compile("^" + pv_in_notification + "$")
            pvnames = list(filter(comp_regex.match, fullpvlist))
            rule = core_inner[symbols.rule + core_number]
            subrule = core_inner[symbols.subrule + core_number]
            if (symbols.limit + core_number) in core_inner.keys():
                L = float(core_inner[symbols.limit + core_number])
            if (symbols.limitLL + core_number) in core_inner.keys():
                LL = float(core_inner[symbols.limitLL + core_number])
            if (symbols.limitLU + core_number) in core_inner.keys():
                LU = float(core_inner[symbols.limitLU + core_number])
            i = 0
            for pvname in pvnames:
                try:
                    if pvs_dict[pvname].connected:
                        pv = pvs_dict[pvname].value
                        try:
                            float(str(pv))
                        except Exception as e1:
                            rule_array.append(str(False))
                            faulty.append(pvname)
                            continue
                        eval_partial = eval(rule)
                        if eval_partial:
                            true_pvs.update({"pv" : pvname})
                            true_pvs.update({"value" : pv})
                            true_pvs.update({"rule" : rule})
                            true_pvs.update({"limit" : L})
                            true_pvs.update({"limitLL" : LL})
                            true_pvs.update({"limitLU" : LU})
                            true_pvs.update({"subrule" : subrule})
                            aux = deepcopy(true_pvs)
                            true_pvs_array.append(aux)
                            test_results["sizetrue"] += 1
                        rule_array.append(str(eval_partial))
                    else:
                        faulty.append(pvname)
                        rule_array.append(str(False))
                except Exception as e2:
                    print("Error on PV test: ", e2)
                    faulty.append(pvname)
                    rule_array.append(str(False))

            partial_rule = " or ".join(rule_array)
            partial_rule = eval(partial_rule)

            complete_rule.append(str(partial_rule))
            complete_rule.append(subrule.lower()) if subrule != '' else None
            test_results["pvs"].update({
                (pv_in_notification + "(" + core_number + ")") : true_pvs_array})
            if subrule != '':
                test_results.update({(symbols.subrule + core_number) : subrule})
            L, LL, LU = None, None, None
        if eval(" ".join(complete_rule)):
            test_results.update({"send_sms" : True})

        test_results.update({"faulty" : faulty})
    except Exception as e:
        print("Error on utils.py, post_test_notification function: ", e)

    return test_results


def sms_formatter(sms_text, ndata=None):
    """format SMS message text to sent to modem."""
    if sms_text:
        return sms_text + "\r\n"
    else:
        msg = "WARNING!\r\n"
        # print(ndata)
        if ndata["sizetrue"] <= 2:
            i = 0
            for key in ndata["pvs"]:
                aux = ndata["pvs"][key]
                if aux:
                    pvname = ndata["pvs"][key][0]["pv"]
                    pvvalue = ndata["pvs"][key][0]["value"]
                    rule = ndata["pvs"][key][0]["rule"]
                    subrule = ndata["pvs"][key][0]["subrule"]
                    msg += pvname + " = " + str(pvvalue) + "\r\n"
                    msg +="Rule: " + rule + "\r\n"
                    if ndata["pvs"][key][0]["limit"]:
                        msg += "Limit: " + str(ndata["pvs"][key][0]["limit"]) + "\r\n"
                    else:
                        if i == 0:
                            msg += "LL: " + str(ndata["pvs"][key][0]["limitLL"]) + "\r\n"
                            msg += "LU: " + str(ndata["pvs"][key][0]["limitLL"]) + "\r\n"
                    if subrule:
                        msg += "Subrule: " + subrule + "\r\n"
                i += 1
            return msg
        else:
            msg += "Multiple PVs reached their limits!\r\n"
            for key in ndata["pvs"]:
                pvname = ndata["pvs"][key][0]["pv"]
                pvvalue = ndata["pvs"][key][0]["value"]
                rule = ndata["pvs"][key][0]["rule"]
                break
            msg += "First PV: " + pvname + "\r\n"
            msg += "Value: " + str(pvvalue) + "\r\n"
            msg += "Rule: " + rule + "\r\n"
            return msg


def show_running(loop_index):
    """show running status on prompt."""
    run = ["|", "/", "-", "\\", "|", "/", "-", "\\"]
    idx = loop_index % 8
    print(run[idx], end='\r')


def pre_test_notification(n, now):
    """test if notification can be sent."""
    can_send = False
    interval_can_send = False
    persistence_can_send = False
    expiration_can_send = False
    last_sent = n["last_sent"]
    n_lastsent = last_sent
    # if n_lastsent != None:
    #     pass
    # else:
    #     n_lastsent = None
    n_notification = loads(n["notification"])
    n_interval = timedelta(minutes=int(n_notification["interval"]))
    n_persistence = n_notification["persistence"]
    n_expiration = datetime.strptime(n_notification["expiration"], '%Y-%m-%d %H:%M')
    # test interval:
    if n_lastsent != None:
        if now >= (n_lastsent + n_interval):
            interval_can_send = True
    else:
        interval_can_send = True
    # test persistence:
    if n_persistence == 'NO':
        if n_lastsent == None:
            persistence_can_send = True
    else:
        persistence_can_send = True
    # test expiration
    if now <= n_expiration:
        expiration_can_send = True

    # if all conditions outside notification
    if interval_can_send == True and \
        persistence_can_send == True and \
        expiration_can_send == True:
        can_send = True
    return can_send


def byebye(ans, n, now, app_notifications, users_db, update_db=True, update_log=True, no_text=False, send_sms=True, send_wapp=True, print_msg=True, queue=None):
    try:
        user_id = n["user_id"]
        n_id = n["id"]
        user = users_db.get(field="id", value=user_id)
        # get sms text from notification
        sms_text = n["sms_text"]
        # if no text option enabled
        if no_text:
            # set sms text to empty
            sms_text = ""
        # format sms text
        text2send = sms_formatter(sms_text, ndata=ans)
        # set cellphone number
        number = user.phone
        username = user.username
        email = user.email

        # update notification last_sent key
        if update_db:
            update_db_ans = app_notifications.update(n_id, "last_sent", now)

        # create variable to store data passed to new process
        basket = [number, text2send, n_id, update_db_ans, update_log, username, email, send_sms, send_wapp, now, print_msg]
        # append data to queue
        queue.append(basket)
    except Exception as e:
        print("Error on utils.py, byebye function: ", e)


def prepare_evaluate(f, test_mode=False):
    if test_mode:
        try:
            f.update()
            fullpvlist = f.getlist()
            print("Full PV List created")
        except Exception as e:
            print("Error on prepare_evaluate function: ", e)
            exit()
    else:
        try:
            f.update()
            fullpvlist = f.getlist()
            print("Full PV List created")
            # modem = Modem(debug=False)
            # print("Modem object created")
            # modem.initialize()
            # print("USB Modem initialized")
            # modem.closeconnection()
        except Exception as e:
            print("Error on prepare_evaluate function: ", e)
            exit()
    return fullpvlist#, modem


def call_modem(number, text2send, n_id, update_db_ans, update_log, username, email, send_sms, now, print_msg, busy_modem, writer_queue, system_errors):
    # initially, busy variable is True, because modem will be in use
    m_now = dt.now()
    if send_sms:
        msg = deepcopy(text2send[:-2])
        modem = Modem()
        modem.initialize()
        modem_ans = modem.sendsms(number=number, msg=msg, force=True)
        modem.closeconnection()
    else:
        modem_ans = 1, m_now
    # if modem answer ok, proceed to write log
    modem_ok = modem_ans[0]
    if modem_ok:
        if send_sms:
            if update_db_ans and update_log:
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                m_now_str = m_now.strftime("%Y-%m-%d %H:%M:%S")
                logmsg = f"{now_str} - id {n_id} - SMS to {username} at {m_now_str} with message: \r\n{text2send}\r\n"
                writer_queue.append(logmsg)
                # w_log = write("log.txt", logmsg)
                if print_msg:
                    print(logmsg)
        else:
            if update_db_ans and update_log:
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                m_now_str = m_now.strftime("%Y-%m-%d %H:%M:%S")
                logmsg = f"{now_str} - id {n_id} - SMS not sent due script configuration."
                writer_queue.append(logmsg)
                # w_log = write("log.txt", logmsg)
                if print_msg:
                    print(logmsg)
    else:
        error = dict()
        error["username"] = username
        error["number"] = number
        error["email"] = email
        error["message"] = text2send
        error["timestamp"] = m_now
        error["cause"] = "modem error"
        system_errors.append(error)
        if update_log:
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            m_now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            logmsg = f"{now_str} - id {n_id} - SMS to {username} was not sent due modem error, at {m_now_str}\n\r"
            writer_queue.append(logmsg)
            if print_msg:
                print(logmsg)

    # set busy variable to False, freeing the modem for next use
    sleep(1)
    busy_modem.value = False
    return 1


def call_wapp(number, text2send, n_id, update_db_ans, update_log, username, email, send_wapp, now, print_msg, busy_wapp, writer_queue, system_errors):
    m_now = dt.now()
    if send_wapp:
        try:
            wait_time = 20
            tab_close = True
            # send_wapp_(number, text2send, wait_time, tab_close)
            sleep(10)
            busy_wapp.value = False
            wapp_ans = 1
        except Exception as e:
            print("Error on sending WhatsApp message:", e)
            wapp_ans = 0
    else:
        wapp_ans = 1

    if wapp_ans:
        if update_db_ans and update_log:
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            m_now_str = m_now.strftime("%Y-%m-%d %H:%M:%S")
            logmsg = f"{now_str} - id {n_id} - WhatsApp to {username} at {m_now_str} with message: \r\n{text2send}\r\n"
            writer_queue.append(logmsg)
            if print_msg:
                print(logmsg)
    else:
        error = dict()
        error["username"] = username
        error["number"] = number
        error["email"] = email
        error["message"] = text2send
        error["timestamp"] = m_now
        error["cause"] = "pywhatkit error"
        system_errors.append(error)
        if update_log:
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            m_now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            logmsg = f"{now_str} - id {n_id} - WhatsApp to {username} was not sent due error on pywhatkit, at {m_now_str}\n\r"
            writer_queue.append(logmsg)
            if print_msg:
                print(logmsg)
    sleep(1)
    busy_wapp.value = False
    return 1


def writer(writer_queue, exit):
    while True:
        if len(writer_queue) > 0:
            try:
                my_log = writer_queue[0]
                w_log = write("log.txt", my_log + "\n\r")
                if w_log:
                    writer_queue.pop(0)
            except Exception as e:
                print("Error on writing log file: ", e)
        if exit.value == True:
            break
        else:
            sleep(1)


def call_admin(system_errors, busy_modem, busy_call_admin, admin_number, admin_email):
    """Function to warn admin of system errors."""
    try:
        username = system_errors[0]["username"]
        m_now = system_errors[0]["timestamp"]
        error = system_errors[0]["cause"]
        m_now_str = m_now.strftime("%Y-%m-%d %H:%M:%S")
        message = f"Notification Failure\n\rUser: {username}\n\rTimestamp: {m_now_str}\n\rError: {error}"

        if not busy_modem.value:
            busy_modem.value = True
            modem = Modem()
            modem.initialize()
            modem_ans = modem.sendsms(number=admin_number, msg=message, force=True)
            modem.closeconnection()
            busy_modem.value = False
            system_errors.pop(0)

        busy_call_admin.value = False
        print("call_admin ended safely")
    except Exception as e:
        print("Error on call_admin: ", e)


def ns_queuer(n_queue, writer_queue, busy_modem, busy_wapp, exit, system_errors, busy_call_admin):
    while True:
        send_wapp = False
        if len(n_queue) > 0:
            basket = deepcopy(n_queue[0])
            n_queue.pop(0)
            number = basket[0]
            text2send = basket[1]
            n_id = basket[2]
            update_db_ans = basket[3]
            update_log = basket[4]
            username = basket[5]
            email = basket[6]
            send_sms = basket[7]
            send_wapp = basket[8]
            now = basket[9]
            print_msg = basket[10]
            if not busy_modem.value:
                call_modem_open = process_status("ns_call_modem")
                if not call_modem_open:
                    busy_modem.value = True
                    proc_modem = Process(target=call_modem, args=(number, text2send, n_id, update_db_ans, update_log, username, email, send_sms, now, print_msg, busy_modem, writer_queue, system_errors), name="ns_call_modem")
                    proc_modem.start()
                    # busy_wapp.value = True
                    # call_wapp(number, text2send, n_id, update_db_ans, update_log, username, email, send_wapp, now, print_msg, busy_wapp, writer_queue, system_errors)
        system_errors_len = len(system_errors)
        if system_errors_len > 0:
            m_now = dt.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            m_now_str = m_now.strftime("%Y-%m-%d %H:%M:%S")
            system_errors_str = str(system_errors)
            logmsg = f"{now_str} - id {n_id} - SMS to {username} at {m_now_str} with message: \r\n{text2send}\r\n got an error:\r\n{system_errors_str}"
            writer_queue.append(logmsg)
            system_errors.pop(0)
        # if system_errors_len > 0 and not busy_call_admin.value:
        #     call_admin_open = process_status("ns_call_admin")
        #     if not call_admin_open:
        #         # call modem ================================
        #         busy_call_admin.value = True
        #         app_notifications = App_db("users")
        #         admin = app_notifications.get(field='id', value=1)
        #         admin_number = admin.phone
        #         admin_email = admin.email
                # proc_system_errors = Process(target=call_admin, args=(system_errors, busy_modem, busy_call_admin, admin_number, admin_email), name="ns_call_admin")
        #         proc_system_errors.start()
        #         # call WhatsApp =============================
        #         username = system_errors["username"]
        #         m_now = system_errors["timestamp"]
        #         m_now_str = m_now.strftime("%Y-%m-%d %H:%M:%S")
        #         error = system_errors["cause"]
        #         message = f"Notification Failure\n\rUser: {username}\n\rTimestamp: {m_now_str}\n\rError: {error}"
        #         app_notifications = App_db("users")
        #         admin = app_notifications.get(field='id', value=1)
        #         admin_number = admin.phone
        #         admin_email = admin.email
        #         busy_wapp.value = True
        #         wait_time = 20
        #         tab_close = True
        #         if not busy_wapp.value:
        #             if send_wapp:
        #                 # send_wapp_(admin_number, message, wait_time, tab_close)
        #                 sleep(10)
        #                 busy_wapp.value = False
        sleep(1)
        if exit.value == True:
            break


def process_status(process_name):
    for process in process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            return True
    return False
