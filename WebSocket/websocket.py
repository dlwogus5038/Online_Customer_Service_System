# coding=utf8
# !/usr/bin/python

import struct, socket, sys
import hashlib
import threading, random
import time
import os
import requests
import shutil
from base64 import b64encode, b64decode
from app.models import *
from OnlineCustomerService.settings import SERVER_HOST, chatbot
from chatterbot import ChatBot
from app.chatbot import *
from email.mime.text import MIMEText
from django.utils import timezone
from django.db.models import Q

connectionlist = {}


# python3k 版本recv返回字节数组
def parse_recv_data(msg):
    en_bytes = b''
    cn_bytes = []
    if len(msg) < 6:
        return ''
    v = msg[1] & 0x7f
    if v == 0x7e:
        p = 4
    elif v == 0x7f:
        p = 10
    else:
        p = 2
    mask = msg[p:p + 4]
    data = msg[p + 4:]
    for k, v in enumerate(data):
        nv = chr(v ^ mask[k % 4])
        nv_bytes = nv.encode()
        nv_len = len(nv_bytes)
        if nv_len == 1:
            en_bytes += nv_bytes
        else:
            en_bytes += b'%s'
            cn_bytes.append(ord(nv_bytes.decode()))
    if len(cn_bytes) > 2:
        # 字节数组转汉字
        cn_str = ''
        clen = len(cn_bytes)
        count = int(clen / 3)
        for x in range(0, count):
            i = x * 3
            b = bytes([cn_bytes[i], cn_bytes[i + 1], cn_bytes[i + 2]])
            cn_str += b.decode()
        new = en_bytes.replace(b'%s%s%s', b'%s')
        new = new.decode()
        res = (new % tuple(list(cn_str)))
    else:
        res = en_bytes.decode()
    return res


def encode(data):
    data = str.encode(data)
    head = b'\x81'

    if len(data) < 126:
        head += struct.pack('B', len(data))
    elif len(data) <= 0xFFFF:
        head += struct.pack('!BH', 126, len(data))
    else:
        head += struct.pack('!BQ', 127, len(data))
    return head + data


def send_message(remote, message, company_code='00000'):
    conn_lists = ChatConnection.objects.filter(user_ip=str(remote[0]), user_port=str(remote[1]))
    if len(conn_lists) != 0:
        for conn_list in conn_lists:
            try:
                conn = connectionlist['connection' + conn_list.staff_ip + conn_list.staff_port]
            except:
                break
            chat_data = ChatData.objects.create(staff=MyUser.objects.get(staff_ip=conn_list.staff_ip, staff_port=conn_list.staff_port),
                                                is_send=False,user_ip=str(remote[0]), user_port=str(remote[1]), Data=message)
            chat_data.save()
            msg = '{' + str(conn_list.index) + '}' + message
            conn.send(encode(msg))
            return
    elif len(ChatConnection.objects.filter(staff_ip=str(remote[0]), staff_port=str(remote[1]))) != 0:
        num_str = ""
        check_flag = 0

        if str(remote[0]) in message and 'Logout' in message:
            conn_lists = ChatConnection.objects.filter(staff_ip=str(remote[0]), staff_port=str(remote[1]))
            for conn_list in conn_lists:
                try:
                    conn = connectionlist['connection' + conn_list.user_ip + conn_list.user_port]
                    chat_data = ChatData.objects.create(
                        staff=MyUser.objects.get(staff_ip=str(remote[0]), staff_port=str(remote[1]))
                        , user_ip=conn_list.user_ip, user_port=conn_list.user_port, Data=message)
                    chat_data.save()
                    msg = '{' + str(conn_list.index) + '}' + message
                    conn.send(encode(msg))
                except:
                    return
            return

        for i in range(len(message)):
            if message[check_flag] != '{':
                conn_lists = ChatConnection.objects.filter(staff_ip=str(remote[0]), staff_port=str(remote[1]))
                break
            elif message[i] == '{':
                num_str = ""
            elif message[i] == '}':
                conn_lists = ChatConnection.objects.filter(staff_ip=str(remote[0]), staff_port=str(remote[1])
                                                           , index=int(num_str))
                break
            else:
                num_str += message[i]

        for conn_list in conn_lists:
            try:
                conn = connectionlist['connection' + conn_list.user_ip + conn_list.user_port]
                chat_data = ChatData.objects.create(
                    staff=MyUser.objects.get(staff_ip=str(remote[0]), staff_port=str(remote[1]))
                    , user_ip=conn_list.user_ip, user_port=conn_list.user_port, Data=message)
                chat_data.save()
                msg = '{' + str(conn_list.index) + '}' + message
                conn.send(encode(msg))
            except:
                return
        return
    else:
        if len(MyUser.objects.filter(staff_ip=str(remote[0]), staff_port=str(remote[1]))) != 0:
            return

        conn = connectionlist['connection' + str(remote[0]) + str(remote[1])]

        if message == 'asdasdasdasvmvjvjnjvsd':
            if len(MyUser.objects.filter(staff_ip=str(remote[0]), staff_port=str(remote[1]))) != 0:
                return
            conn.send(encode(str('您好！很高兴为您服务~')))
            responses = chatterbot_order(chatbot[company_code], company_code)
            if len(responses) > 0:
                html = '<p>你是否想了解以下热门问题</p>'
                for title, text in responses:
                    html += '<p><a onclick="send_question(' + "'" + text + "'" + ')">' + str(title) + '</a></p>'
                conn.send(encode(html))
            return

        new_message = ""
        check_flag = 0
        if message[check_flag] == '{':
            while message[check_flag] != '}':
                check_flag += 1
            check_flag += 1

        while True:
            if check_flag == len(message):
                break
            else:
                new_message += message[check_flag]
            check_flag += 1

        message = new_message
        tt = chatterbot_get_response(chatbot[company_code], message)
        conn.send(encode(str(tt)))
        return


def delete_connection(remote):
    global connectionlist
    del connectionlist['connection' + str(remote[0]) + str(remote[1])]


class WebSocket(threading.Thread):
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, conn, index, name, remote, code='00000', path="/"):
        threading.Thread.__init__(self)
        self.conn = conn
        self.index = index
        self.name = name
        self.remote = remote
        self.path = path
        self.buffer = ""
        self.company_code = code

    def run(self):
        print('Socket%s Start!' % self.index)
        headers = {}
        self.handshaken = False

        while True:
            if self.handshaken == False:
                print('Socket%s Start Handshaken with %s!' % (self.index, self.remote))
                self.buffer += bytes.decode(self.conn.recv(1024))

                if self.buffer.find('\r\n\r\n') != -1:
                    header, data = self.buffer.split('\r\n\r\n', 1)
                    for line in header.split("\r\n")[1:]:
                        key, value = line.split(": ", 1)
                        headers[key] = value

                    headers["Location"] = ("ws://%s%s" % (headers["Host"], self.path))
                    key = headers['Sec-WebSocket-Key']
                    token = b64encode(hashlib.sha1(str.encode(str(key + self.GUID))).digest())

                    handshake = "HTTP/1.1 101 Switching Protocols\r\n" \
                                "Upgrade: websocket\r\n" \
                                "Connection: Upgrade\r\n" \
                                "Sec-WebSocket-Accept: " + bytes.decode(token) + "\r\n" \
                                                                                 "WebSocket-Origin: " + str(
                        headers["Origin"]) + "\r\n" \
                                             "WebSocket-Location: " + str(headers["Location"]) + "\r\n\r\n"

                    self.conn.send(str.encode(str(handshake)))
                    self.handshaken = True
                    print('Socket%s Handshaken with %s success!' % (self.index, self.remote))
                    send_message(self.remote, 'asdasdasdasvmvjvjnjvsd', self.company_code)

            else:
                msg = parse_recv_data(self.conn.recv(1024))
                if msg == 'quit':
                    print('Socket%s Logout!' % (self.index))
                    send_message(self.remote, '*' + self.name + ' Logout*', self.company_code)
                    delete_connection(self.remote)
                    delete_chat_connection(str(self.remote[0]), str(self.remote[1]))
                    self.conn.close()
                    break
                elif 'quit/score=' in msg:
                    print('Socket%s Logout!' % (self.index))
                    send_message(self.remote, '*' + self.name + ' Logout*', self.company_code)
                    delete_connection(self.remote)

                    score = ""
                    for i in range(len(msg)):
                        if msg[i] == '=':
                            score = ""
                        else:
                            score += msg[i]

                    delete_chat_connection(str(self.remote[0]), str(self.remote[1]), score=score)
                    self.conn.close()
                    break
                elif '*defriend*' in msg:
                    index_num = ""
                    for i in range(len(msg)):
                        if msg[i] == '*':
                            index_num = ""
                        else:
                            index_num += msg[i]

                    if len(ChatConnection.objects.filter(staff_ip=str(self.remote[0]), staff_port=str(self.remote[1]), index=index_num)) == 0:
                        defriend_conn = connectionlist['connection' + str(self.remote[0]) + str(self.remote[1])]
                        defriend_conn.send(encode('{' + index_num + '}' + '*当前没有聊天连接*'))
                        continue

                    send_message(self.remote, '{' + index_num + '}*对方已断开此聊天连接，请您尝试重新做连接*', self.company_code)
                    delete_chat_connection(str(self.remote[0]), str(self.remote[1]), score=0, index=int(index_num))
                    defriend_conn = connectionlist['connection' + str(self.remote[0]) + str(self.remote[1])]
                    defriend_conn.send(encode('{' + index_num + '}' + '*成功断开聊天连接*'))
                elif '*change_staff*' in msg:
                    index_num = ""
                    for i in range(len(msg)):
                        if msg[i] == '*':
                            index_num = ""
                        else:
                            index_num += msg[i]

                    if len(ChatConnection.objects.filter(staff_ip=str(self.remote[0]), staff_port=str(self.remote[1]), index=index_num)) == 0:
                        defriend_conn = connectionlist['connection' + str(self.remote[0]) + str(self.remote[1])]
                        defriend_conn.send(encode('{' + index_num + '}' + '*当前没有聊天连接*'))
                        continue

                    new_staff = arrange_staff(self.company_code, str(self.remote[0]), str(self.remote[1]))
                    if new_staff != None:
                        for n in range(new_staff.process_num + 1):
                            if n == 0:
                                continue
                            else:

                                if len(ChatConnection.objects.filter(staff=new_staff, index=n, staff_ip=new_staff.staff_ip
                                        , staff_port=new_staff.staff_port)) == 0:
                                    delete_conn = ChatConnection.objects.get(staff_ip=str(self.remote[0])
                                                                             , staff_port=str(self.remote[1])
                                                                             , index=int(index_num))
                                    us_IP = delete_conn.user_ip
                                    us_Port = delete_conn.user_port
                                    us_index = delete_conn.index
                                    delete_chat_connection(str(self.remote[0]), str(self.remote[1]), -1, n)

                                    newConnection = ChatConnection(staff=new_staff, user_ip=str(us_IP)
                                                                   , user_port=str(us_Port),
                                                                   staff_name=new_staff.username, staff_ip=new_staff.staff_ip
                                                                   , staff_port=new_staff.staff_port, index=n)
                                    newConnection.save()

                                    msg = "连接成功/IP=" + str(new_staff.staff_ip) + '/Nickname=' + str(
                                        new_staff.nickname) + '/image=' + new_staff.get_image_url()
                                    conn = connectionlist['connection' + str(us_IP) + str(us_Port)]
                                    conn.send(encode(msg))

                                    msg2 = '{' + str(newConnection.index) + '}' + "连接成功/IP=" + str(us_IP)
                                    conn2 = connectionlist[
                                        'connection' + str(newConnection.staff_ip) + str(newConnection.staff_port)]
                                    conn2.send(encode(msg2))

                                    msg3 = '{' + str(us_index) + '}' + "*转接成功！*"
                                    conn3 = connectionlist[
                                        'connection' + str(self.remote[0]) + str(self.remote[1])]
                                    conn3.send(encode(msg3))
                                    break
                    else:
                        msg = '*没有其他正在等待的客服人员*'
                        conn = connectionlist['connection' + str(self.remote[0]) + str(self.remote[1])]
                        conn.send(encode(msg))
                        delete_conn = ChatConnection.objects.get(staff_ip=str(self.remote[0])
                                                                 , staff_port=str(self.remote[1])
                                                                 , index=int(index_num))
                        conn = connectionlist['connection' + str(delete_conn.user_ip) + str(delete_conn.user_port)]
                        conn.send(encode(msg))

                elif '*create image data*' in msg:
                    check_index = ''

                    if len(ImageData.objects.filter(user_IP=str(self.remote[0]))) != 0:
                        delete_image_data = ImageData.objects.filter(user_IP=str(self.remote[0]))
                        for data in delete_image_data:
                            data.delete()

                    if msg[0] == '{':
                        for i in range(len(msg)):
                            if msg[i] == '}':
                                break
                            elif msg[i] == '{':
                                check_index = ''
                            else:
                                check_index += msg[i]
                        new_image_data = ImageData.objects.create(user_IP=str(self.remote[0]), user_port=str(self.remote[1])
                                                              , chat_index=int(check_index))
                        new_image_data.save()
                    else:
                        new_image_data = ImageData.objects.create(user_IP=str(self.remote[0]),
                                                                  user_port=str(self.remote[1]))
                        new_image_data.save()
                elif msg == '*connect_staff*':

                    if len(ChatConnection.objects.filter(user_ip=str(self.remote[0]),user_port=str(self.remote[1]))) != 0:
                        msg = '您已经在跟客服人员对话中'
                        conn = connectionlist['connection' + str(self.remote[0]) + str(self.remote[1])]
                        conn.send(encode(msg))
                        continue

                    staff = arrange_staff(self.company_code)
                    if staff != None:
                        for n in range(staff.process_num + 1):
                            if n == 0:
                                continue
                            else:
                                if len(ChatConnection.objects.filter(staff=staff, index=n, staff_ip=staff.staff_ip
                                        , staff_port=staff.staff_port)) == 0:
                                    newConnection = ChatConnection(staff=staff, user_ip=str(self.remote[0])
                                                                   , user_port=str(self.remote[1]),
                                                                   staff_name=staff.username, staff_ip=staff.staff_ip
                                                                   , staff_port=staff.staff_port, index=n)
                                    newConnection.save()

                                    msg = "连接成功/IP=" + str(staff.staff_ip) + '/Nickname=' + str(
                                        staff.nickname) + '/image=' + staff.get_image_url()
                                    conn = connectionlist['connection' + str(self.remote[0]) + str(self.remote[1])]
                                    conn.send(encode(msg))

                                    msg2 = '{' + str(newConnection.index) + '}' + "连接成功/IP=" + str(self.remote[0])
                                    conn2 = connectionlist[
                                        'connection' + str(newConnection.staff_ip) + str(newConnection.staff_port)]
                                    conn2.send(encode(msg2))
                                    break
                    else:
                        msg = '目前没有等待的客服人员，请您稍后再试！'
                        conn = connectionlist['connection' + str(self.remote[0]) + str(self.remote[1])]
                        conn.send(encode(msg))

                elif msg != '':
                    print('Socket%s Got msg:%s from %s!' % (self.index, msg, self.remote))
                    send_message(self.remote, msg, self.company_code)

            self.buffer = ""


class WebSocketServer(threading.Thread):
    def __init__(self, code='00000'):
        threading.Thread.__init__(self)
        self.socket = None
        self.company_code = code

        if code not in chatbot:
            chatbot[code] = ChatBot(
                'chatbot',
                database=self.company_code,
                read_only=True,
                logic_adapters=[
                    "chatterbot.logic.BestMatch"
                ]
            )

    def run(self):
        print('WebSocketServer Start!')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((SERVER_HOST, int(self.company_code)))
        self.socket.listen(3000)

        global connectionlist

        i = 0
        while True:
            connection, address = self.socket.accept()

            username = address[0]
            newSocket = WebSocket(connection, i, username, address, self.company_code)
            newSocket.start()
            connectionlist['connection' + str(address[0]) + str(address[1])] = connection
            i = i + 1

            staffs = MyUser.objects.filter(~Q(status=0), is_admin=False, is_company=False, staff_ip=str(address[0])
                                           , staff_port='0')
            if len(staffs) != 0:
                for staff in staffs:
                    if staff.staff_port == '0':
                        staff.staff_port = address[1]
                        staff.save()
                continue


def arrange_staff(company_code, IP="0.0.0.0", PORT="0"):
    #connect user with staff
    if IP == "0.0.0.0":
        staffs = MyUser.objects.filter(is_admin=False, is_company=False, company_code=company_code).order_by(
            'chatting_score')
    else:
        staffs = MyUser.objects.filter(~Q(staff_ip=IP, staff_port=PORT) ,is_admin=False, is_company=False, company_code=company_code).order_by(
            'chatting_score')
    for my_staff in staffs:
        if my_staff.status == 1 or my_staff.status == 2:
            # choose this one
            my_staff.cur_process += 1
            my_staff.chatting_num += 1
            if my_staff.cur_process > 0 and my_staff.cur_process < my_staff.process_num:
                my_staff.status = 2
            elif my_staff.cur_process == my_staff.process_num:
                my_staff.status = 3
            my_staff.save()
            return my_staff
    return None


def delete_chat_connection(IP, PORT, score=-1, index=-1):
    st_ip = None
    st_port = None
    delete_num = 0

    conns = ChatConnection.objects.filter(user_ip=IP, user_port=PORT)
    if len(conns) != 0:
        for conn in conns:
            st_ip = conn.staff_ip
            st_port = conn.staff_port
            delete_num += 1
            # 计算并保存聊天时间
            conn.end_time = timezone.now()
            staff = MyUser.objects.get(staff_ip=conn.staff_ip, staff_port=conn.staff_port)
            conn_start_time = conn.start_time
            conn_end_time = conn.end_time
            staff.chatting_time += int((conn_end_time - conn_start_time).seconds)  # 服务器异常结束时会有出现BUG
            staff.save()
            data = ChatRecord.objects.create(staff=staff, user_IP=conn.user_ip, user_Port=conn.user_port, start_time= conn_start_time, end_time= conn_end_time)
            if not score == -1:
                data.score = score
            data.chatting_time = str(int((data.end_time - data.start_time).seconds / 60)) + "' " + str(
                (data.end_time - data.start_time).seconds % 60) + "''"
            user_add = ''
            address = check_ip(data.user_IP)
            for add in address:
                if add not in user_add:
                    if len(user_add) > 0:
                        user_add += ' '
                    user_add += add
            if len(user_add) > 0:
                data.address = user_add
            data.save()
            break
        conns.delete()
    elif len(ChatConnection.objects.filter(staff_ip=IP, staff_port=PORT)) != 0:
        conns = ChatConnection.objects.filter(staff_ip=IP, staff_port=PORT)
        for conn in conns:
            if not index == -1 and not conn.index == index:
                continue
            st_ip = conn.staff_ip
            st_port = conn.staff_port
            delete_num += 1
            # 计算并保存聊天时间
            conn.end_time = timezone.now()
            staff = MyUser.objects.get(staff_ip=conn.staff_ip, staff_port=conn.staff_port)
            conn_start_time = conn.start_time
            conn_end_time = conn.end_time
            staff.chatting_time += int((conn_end_time - conn_start_time).seconds)  # 服务器异常结束时会有出现BUG
            staff.save()
            data = ChatRecord.objects.create(staff=staff, user_IP=conn.user_ip, user_Port=conn.user_port,
                                             start_time=conn_start_time, end_time=conn_end_time)
            if not score == -1:
                data.score = score
            data.chatting_time = str(int((data.end_time - data.start_time).seconds / 60)) + "' " + str(
                (data.end_time - data.start_time).seconds % 60) + "''"
            user_add = ''
            address = check_ip(data.user_IP)
            for add in address:
                if add not in user_add:
                    if len(user_add) > 0:
                        user_add += ' '
                    user_add += add
            if len(user_add) > 0:
                data.address = user_add
            data.save()
            conn.delete()
    else:
        if len(MyUser.objects.filter(is_admin=False, is_company=False, staff_ip=IP, staff_port=PORT)) != 0:
            staff = MyUser.objects.filter(is_admin=False, is_company=False, staff_ip=IP, staff_port=PORT)
            for st in staff:
                st.cur_process = 0
                st.save()
        return

    staff = MyUser.objects.get(is_admin=False, is_company=False, staff_ip=st_ip, staff_port=st_port)
    staff.cur_process -= delete_num
    if staff.cur_process < 0:
        staff.cur_process = 0
    if staff.status == 0:
        staff.status = 0
        staff.cur_process = 0
    elif staff.cur_process == 0:
        staff.status = 1
    elif staff.cur_process > 0 and staff.cur_process < staff.process_num:
        staff.status = 2
    staff.save()
    # 计算平均对话时间并给客服人员分数
    staffs = MyUser.objects.filter(is_admin=False, is_company=False, company_code=staff.company_code)
    if len(staffs) == 0:
        return
    average_time = 0
    chatting_num = 0
    for my_staff in staffs:
        chatting_num += my_staff.chatting_num
        average_time += my_staff.chatting_time
    if chatting_num == 0:
        return
    average_time /= float(chatting_num)
    for my_staff in staffs:
        my_staff.chatting_score = float(my_staff.chatting_time)
        my_staff.chatting_score /= average_time
        my_staff.save()


def check_ip(user_IP):
    IP = {'ip': user_IP}
    URL = 'http://ip.taobao.com/service/getIpInfo.php'
    address = []
    try:
        r = requests.get(URL, params=IP, timeout=10)
    except requests.RequestException as e:
        return address
    else:
        json_data = r.json()
        if json_data[u'code'] == 0:
            if len(str(json_data[u'data'][u'country'])) > 0:
                address.append(str(json_data[u'data'][u'country']))
            if len(str(json_data[u'data'][u'area'])) > 0:
                address.append(str(json_data[u'data'][u'area']))
            if len(str(json_data[u'data'][u'region'])) > 0:
                address.append(str(json_data[u'data'][u'region']))
            if len(str(json_data[u'data'][u'city'])) > 0:
                address.append(str(json_data[u'data'][u'city']))
        return address
