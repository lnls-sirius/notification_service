import serial, time, re, psutil
import random, string
from copy import deepcopy
from symbols import *
from datetime import datetime as dt
from datetime import timedelta as td

##############################################################
# We need to change permission for the usb file of the modem #
# To make a udev file adding a specific rule for this modem, #
# two parameter are necessary: idVendor and idProduct, found #
# with command: <lsusb -vvv> (look for ZTE modem in the list)#
# Udev file goes to: /etc/udev/rules.d/<50-filename.rules> ###
# Add the bellow line to the file: ###########################
# SUBSYSTEMS=="usb", ATTRS{idVendor}=="<idVendor_for_modem>", ATTRS{idProduct}=="<idProduct_for_modem>", GROUP="users", MODE="0666"
# In optiplex-7070-sc-2, idVendor=19d2 and idProduct=1589 ####
# Reload udev with command: <sudo udevadm control --reload> ##
# Insert (or take out and reinsert) modem in the usb slot ####
# Verify modem file permission with the bellow command: ######
# <stat /dev/ttyUSB0> ########################################
# Access must be with description (0666/crw-rw-rw) ###########
# Also, kill ModemManagement proccess with commands: #########
# <sudo lsof -t /dev/ttyUSB0> then <sudo kill proccess_id> ###
# Sometimes it's necessary kill, start, than kill again the ##
# ModemManager proccess. Use the following commands: #########
# <sudo service ModemManager status> (look for Main PID) #####
# <sudo kill process_ID> #####################################
# <sudo service ModemManager start> ##########################
# Keep ModemManager proccess killed! #########################
# Wait until the modem is ready, sometimes 60 seconds ########
##############################################################


class Modem:
    def __init__(self, path=usbmodemport, debug=False):
        self.path = path
        self.debug = debug
        self.msgnumber = None
        self.msg = None
        try:
            if self.detect_modem_proc():
                self.serial_connection = serial.Serial(path, baudrate=115200, timeout=5)
                self.serial_connection.reset_input_buffer()
            else:
                print("Error on modem connection")
                exit()
        except OSError as e:
            if e.errno == 16:
                print(e)
                exit()

    def send_to_modem(self, msg, sleep=0.2):
        self.serial_connection.write(msg.encode())
        time.sleep(sleep)

    def get_answer(self, strt_sleep=0.1, sleep=0.1):
        time.sleep(strt_sleep)
        quantity = self.serial_connection.in_waiting
        ans = ''
        while True:
            if quantity > 0:
                ans += self.serial_connection.read(quantity).decode()
                time.sleep(sleep)
            else:
                pass
                time.sleep(sleep)
            quantity = self.serial_connection.in_waiting
            if quantity == 0:
                break
        if self.debug:
            print(ans)
        return ans

    def get_answer2(self):
        self.serial_connection.readline()
        while True:
            line = self.serial_connection.readline()
            if line == b'OK\r\n':
                return True
            if line == b'nOk\r\n':
                return False
            if line == b'NO CARRIER\r\n':
                return False

    def echo_mode(self, mode=1):
        if mode == 0:
            cmd = ATE0
        elif mode == 1:
            cmd = ATE1
        self.send_to_modem(cmd)
        ans = self.get_answer(sleep=0.2)
        return ans

    def send_command(self, cmd, sleep=2, endchar=CR):
        if endchar == 'ESC':
            endchar = chr(26)
        aux = cmd + endchar
        self.send_to_modem(aux)
        return self.get_answer(int(sleep))

    def reset(self):
        cmd = ATZ
        self.send_to_modem(cmd)
        ans = self.get_answer(sleep=2)
        return ans

    def verbose_on_error(self, turn=True):
        if turn:
            cmd = CMEE_1
            self.send_to_modem(cmd)
            ans = self.get_answer(sleep=0.2)
        elif turn == False:
            cmd = CMEE_0
            self.send_to_modem(cmd)
            ans = self.get_answer(sleep=0.2)
        return ans

    def set_mode(self, mode='text'):
        if mode == 'text':
            cmd = CMGF_1
            self.send_to_modem(cmd)
            ans = self.get_answer(sleep=0.5)
            return ans
        elif mode == 'PDU':
            return 'error on set_mode: PDU mode not implemented'
        else:
            return 'error on set_mode: option not supported'

    def write_to_storage(self, index, msg):
        cmd = CMGW + '"' + index + '"' + CR
        self.send_to_modem(cmd)
        ans = self.get_answer(sleep=0.2)
        if ans == '>':
            cmd = msg + SUB
            self.send_to_modem(cmd)
            ans = self.get_answer(sleep=0.2)
            if '+CMGW:' in ans:
                pattern = r'[\d]+' #raw string declaration
                if re.search(pattern, ans) is not None:
                    for catch in re.finditer(pattern, ans):
                        msgnumber = catch[0]
                    return msgnumber
        return ans

    def send_from_storage(self, index):
        cmd = CMSS + str(index) + CR
        self.send_to_modem(cmd)
        ans = self.get_answer(sleep=0.2)
        return ans

    def set_storage_area(self, area='ME'):
        if area == 'ME':
            area = '"' + area + '"'
            cmd = CPMS + area + ','+ area + CR
            self.send_to_modem(cmd)
            ans = self.get_answer(sleep=0.2)
            return ans

    #index = memory location of stored SMS, set storage area before using this.
    #flags:
    #0 = delete only selected message;
    #1 = ignore index (use any number), delete all received read;
    #2 = ignore index, delete all received read and stored sent;
    #3 = ignore index, delete all received read, stored unsent and stored sent;
    #4 = ignore index, delete all stored SMS messages;
    def clear_storage(self, index=1, flag=4):
        aux = str(index) + ',' + str(flag) + '\r'
        cmd = CMGD + aux
        self.send_to_modem(cmd)
        ans = self.get_answer(sleep=1)
        return ans

    def set_delivery_report(self, report=True):
        if report:
            cmd = CNMI + '2,1,0,1,0' # values to receive report
            ans = self.send_command(cmd)
            # ans = self.get_answer(sleep=0.2)
            if ('OK' in ans) and ('nOK' not in ans):
                cmd = CSMP + '49,167,0,0' # values to receive report
                ans = self.send_command(cmd)
                # ans = self.get_answer(sleep=0.2)
            else:
                return ans
        else:
            cmd = CNMI + '2,1,2,1,0' # original values
            ans = self.send_command(cmd)
            # ans = self.get_answer(sleep=0.2)
            if ('OK' in ans) and ('nOK' not in ans):
                cmd = CSMP + '0,173,0,0' # original values
                ans = self.send_command(cmd)
                # ans = self.get_answer(sleep=0.2)
            else:
                return ans

    def get_delivery_report(self, phonenumber, sent, delay=10, exclude_sms=True):
        time.sleep(delay)
        cmd = CMGL + ALL
        ans = self.send_command(cmd)
        if ('AT+CMGL="all"' and 'OK' and not "+CMGL: " in ans):
            return False
        else:
            ans = ans.split("+CMGL: ")
            ans.remove(ans[0])
            ans[-1] = ans[-1].split('OK')[0]
            for elem in ans:
                rec_number = elem.split('"",')[1].split('Torpedo SMS entregue p/ ')[1].split(' (')[0].strip()
                sms_id = (elem.split(',"REC ')[0])
                delivery_date = dt.strptime((elem.split('"","')[1]).split('-')[0], '%Y/%m/%d %H:%M:%S')
                if (rec_number.strip()) in (phonenumber.strip()):
                    validate_delivery = True if ((abs(delivery_date - sent).seconds) <= delay) else False
                    if (validate_delivery):
                        if exclude_sms:
                            cmd = CMGD + str(sms_id)
                            ans = self.send_command(cmd)
                            if ('OK' in ans) and ('nOK' not in ans):
                                return True
                            else:
                                return False
                        return True
            return False

    # Force delivery if Carrier denies it due Spam filter
    def force_delivery(self):
        is_delivered=False
        i = 0
        original_msg = deepcopy(self.msg)
        msgnumber = deepcopy(self.msgnumber)
        randomword = self.randomword(10)
        while is_delivered != True :
            if i == 0:
                if len(original_msg + '\r\n' + randomword) >= 160:
                    extra_len = len(original_msg + "\r\n" + randomword) - 160
                    msg = deepcopy(self.msg[:(len(original_msg) - extra_len)])
                    msg = original_msg + "\r\n" + randomword
                else:
                    msg = original_msg + "\r\n" + randomword
                sent = self.sendsms(number=msgnumber, msg=msg)
                if sent[0] == True:
                    is_delivered = self.get_delivery_report(msgnumber, sent[1], 10)
            else:
                if i >= 4:
                    break
                randomword += self.randomword(5)
                if len(original_msg + '\r\n' + randomword) >= 160:
                    extra_len = len(original_msg + "\r\n" + randomword) - 160
                    msg = deepcopy(original_msg[:(len(original_msg) - extra_len)])
                    msg = msg + '\r\n' + randomword
                else:
                    msg = original_msg + '\r\n' + randomword
                sent = self.sendsms(number=msgnumber, msg=msg)
                if sent[0] == True:
                    is_delivered = self.get_delivery_report(msgnumber, sent[1], 12)
            i += 1
        return is_delivered

    def detect_modem_proc(self):
        for proc in psutil.process_iter():
            if proc.name() == 'ModemManager':
                # proc.kill()
                if self.debug == True:
                    print('Error: modem in use by another proccess!')
                return False
            else:
                return True

    def initialize(self):
        self.reset()
        ans = self.reset()
        if self.debug == True:
            if ('OK' in ans) and ('nOK' not in ans):
                ans = self.verbose_on_error()
            else:
                return ans
        if ('OK' in ans) and ('nOK' not in ans):
            ans = self.set_mode(mode='text')
        else:
            return ans
        if ('OK' in ans) and ('nOK' not in ans):
            ans = self.set_storage_area(area='ME')
        else:
            return ans
        if ('OK' in ans) and ('nOK' not in ans):
            ans = self.clear_storage(index=1, flag=4)
        else:
            return ans
        if ('OK' in ans) and ('nOK' not in ans):
            ans = self.set_delivery_report()
        else:
            return ans
        return ans

    #Operations Group number
    def sendsms(self, mode='direct', number='+5519997397443', msg='SMS message test.', clearmemo=True, force=False):
        self.msg = deepcopy(msg[:160])
        self.msgnumber = number
        if mode == 'direct':
            cmd = CMGS + '"' + number + '"' + CR
            self.send_to_modem(cmd)
            ans = self.get_answer(sleep=0.2)
            if '>' in ans:
                cmd1 = self.msg
                self.send_to_modem(cmd1)
                cmd2 = chr(26)
                self.send_to_modem(cmd2)
                time.sleep(5)
                ans = self.get_answer()
            if msg and 'OK' in ans:
                if force:
                    if self.get_delivery_report(number, dt.now(), 12):
                        if self.force_delivery():
                            self.closeconnection()
                        return 1, dt.now()
                else:
                    return 1, dt.now()
            return 0, dt.now()

        elif mode == 'indirect':
            cmd = CMGW + '"' + number + '"' + CR
            self.send_to_modem(cmd)
            ans = self.get_answer(sleep=0.2)
            if '>' in ans:
                cmd = msg + EOMM
                self.send_to_modem(cmd)
                ans = self.get_answer(sleep=0.2)
                if '+CMGW:' in ans:
                    pattern = r'[\d]+' #raw string declaration
                    if re.search(pattern, ans) is not None:
                        for catch in re.finditer(pattern, ans):
                            msgnumber = catch[0]
                        if msgnumber.isnumeric():
                            cmd = CMSS + msgnumber + CR
                            self.send_to_modem(cmd)
                            ans = self.get_answer(sleep=4)
                            if ('OK' in ans) and ('nOK' not in ans):
                                if clearmemo:
                                    self.clear_storage(msgnumber)
                                if force:
                                    if not self.get_delivery_report(phonenumber=number,
                                        sent=dt.now(),
                                        delay=10):
                                        if self.force_delivery():
                                            self.closeconnection()
                                            return 1, dt.now()
                                else:
                                    return 1, dt.now()
                else:
                    return 1, dt.now()
            return 0, dt.now()

    def closeconnection(self):
        self.serial_connection.close()

    def randomword(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def sendsms_force(self, mode='direct', number='+5519997397443', msg='SMS test.', clearmemo=True):
        sent = self.sendsms(mode=mode, number=number, msg=msg, clearmemo=clearmemo)
        if not self.get_delivery_report(phonenumber=number, sent=sent[1], delay=10):
            if self.force_delivery():
                self.closeconnection()
                return 1
            else:
                return 0
        return 1

########## For testing purpose ############

# m = Modem(debug=True)
# m.initialize()
# number = '+5519997397443'
# msg = '1) SI-13C4:DI-DCCT:Current-Mon = 100.10985548\n\rLimit: L=420\n\r2) AS-Glob:AP-MachShift:Mode-Sts = 0\n\rLimit: L=69'
# msg = 'test'
# if m.sendsms_force(number=number, msg=msg):
#     print("SMS Delivered!")
# else:
#     print("SMS Failed to be delivered!")
