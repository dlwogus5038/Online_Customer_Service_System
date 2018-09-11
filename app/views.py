from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponse
from .models import *
from WebSocket import websocket
from OnlineCustomerService import settings
from .chatbot import *
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from .permission_check import *
import requests
from .error import *
import os


def index(request):
    users = MyUser.objects.filter(is_company=True, is_active=True, is_verified=True)
    companies = []
    for user in users:
        company = (user.company_name, user.company_code)
        companies.append(company)
    return render(request, 'index.html', {'companies': companies})


def preview(request):
    url = request.GET.get('url')
    return render(request, 'preview.html', {'url': url})


def image_send(request):
    return render(request, 'image_send.html')


def send_image(request):
    if request.method == 'POST':
        new_file = request.FILES.get("new_file", None)
        if not new_file:
            return HttpResponse('No file for upload!')

        allow_suffix = ['jpg', 'png', 'jpeg', 'gif', 'bmp']
        file_suffix = new_file.name.split(".")[-1]
        if file_suffix not in allow_suffix:
            return HttpResponse( '文件格式错误！')
        elif new_file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            return HttpResponse('超出文件系统大小限制！（10MB）')

        if ImageData.objects.filter(user_IP=str(request.META['REMOTE_ADDR']), image_name='').order_by('id'):
            image_data = ImageData.objects.filter(user_IP=str(request.META['REMOTE_ADDR']), image_name='').order_by('id').first()
            image_data.image_name = new_file.name
            image_data.save()

            if len(MyUser.objects.filter(staff_ip=image_data.user_IP, staff_port=image_data.user_port)) != 0:
                if not os.path.exists('app/static/staff_image/' + request.META['REMOTE_ADDR']):
                    os.makedirs('app/static/staff_image/' + request.META['REMOTE_ADDR'])
                destination = open(os.path.join('app/static/staff_image/' + request.META['REMOTE_ADDR'], new_file.name),
                                   'wb+')
                for chunk in new_file.chunks():
                    destination.write(chunk)
                destination.close()
            else:
                if not os.path.exists('app/static/user_image/' + request.META['REMOTE_ADDR']):
                    os.makedirs('app/static/user_image/' + request.META['REMOTE_ADDR'])
                destination = open(os.path.join('app/static/user_image/' + request.META['REMOTE_ADDR'], new_file.name),
                                   'wb+')
                for chunk in new_file.chunks():
                    destination.write(chunk)
                destination.close()

            if len(ChatConnection.objects.filter(user_ip=image_data.user_IP, user_port=image_data.user_port)) != 0:
                con = ChatConnection.objects.get(user_ip=image_data.user_IP, user_port=image_data.user_port)
                remote = [con.user_ip, con.user_port]
                websocket.send_message(remote, '*log*' + str(con.user_ip) + '/' + str(image_data.image_name))
            elif len(ChatConnection.objects.filter(staff_ip=image_data.user_IP, staff_port=image_data.user_port)) != 0:
                con = ChatConnection.objects.get(staff_ip=image_data.user_IP, staff_port=image_data.user_port
                                                 , index= image_data.chat_index)
                remote = [con.staff_ip, con.staff_port]
                websocket.send_message(remote, '{' + str(con.index) + '}' + '*log*' + str(con.staff_ip) + '/' + str(image_data.image_name))

            websocket.connectionlist['connection' + image_data.user_IP + image_data.user_port].send(
                websocket.encode('*self*' + str(image_data.user_IP) + '/' + str(image_data.image_name)))
            image_data.delete()

            delete_data = ImageData.objects.filter(user_IP=str(request.META['REMOTE_ADDR']), image_name='')
            for datum in delete_data:
                datum.delete()
        return HttpResponse("upload over!")


@login_required
@only_company
def manage_staff(request):
    after_range_num = 5
    before_range_num = 4
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except:
        page = 1

    company_code = request.user.company_code
    staffs = MyUser.objects.filter(company_code=company_code, is_company=False).order_by('id')
    paginator = Paginator(staffs, 10)
    try:
        staff_list = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        staff_list = paginator.page(1)
    if page >= after_range_num:
        page_range = paginator.page_range[page - after_range_num:page + before_range_num]
    else:
        page_range = paginator.page_range[0:int(page) + before_range_num]

    staffs = []
    _index = 1
    for staff in staff_list.object_list:
        _data = (staff, (staff_list.number - 1) * 10 + _index)
        staffs.append(_data)
        _index += 1

    return render(request, 'manage_staff.html', locals())


@login_required
@only_company
def manage_robot(request):
    after_range_num = 5
    before_range_num = 4
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except:
        page = 1
    responses = chatterbot_filter_by(request)['response']
    paginator = Paginator(responses, 10)
    try:
        response_list = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        response_list = paginator.page(1)
    if page >= after_range_num:
        page_range = paginator.page_range[page - after_range_num:page + before_range_num]
    else:
        page_range = paginator.page_range[0:int(page) + before_range_num]

    responses = []
    _index = 1
    for response in response_list.object_list:
        _data = (response, (response_list.number - 1) * 10 + _index)
        responses.append(_data)
        _index += 1
    robot_name = request.user.chatterbot_nickname
    return render(request, 'manage_robot.html', locals())


@login_required
@only_company
def manage_answer(request):
    after_range_num = 5
    before_range_num = 4
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except:
        page = 1
    answers = AnswerList.objects.filter(company_code=request.user.company_code).order_by('created_at')
    paginator = Paginator(answers, 10)
    try:
        answer_list = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        answer_list = paginator.page(1)
    if page >= after_range_num:
        page_range = paginator.page_range[page - after_range_num:page + before_range_num]
    else:
        page_range = paginator.page_range[0:int(page) + before_range_num]
    data = []
    _index = 1
    for answer in answer_list.object_list:
        _data = (answer, (answer_list.number - 1) * 10 + _index)
        data.append(_data)
        _index += 1
    return render(request, 'manage_answer.html', locals())


def chat(request, company_code):
    if str(company_code) not in settings.checkTime:
        settings.checkTime[str(company_code)] = 1
        wm = websocket.WebSocketServer(str(company_code))
        wm.setDaemon(True)
        wm.start()
    company_user = MyUser.objects.filter(company_code=company_code, is_company=True).first()
    return render(request, 'chat.html', {'company_code': company_code, 'company_user': company_user})


def m_chat(request, company_code):
    if str(company_code) not in settings.checkTime:
        settings.checkTime[str(company_code)] = 1
        wm = websocket.WebSocketServer(str(company_code))
        wm.setDaemon(True)
        wm.start()
    return render(request, 'm_chat.html', {'company_code': company_code})


@login_required
@only_staff
def staff_base(request):
    return render(request, 'staff_base.html', {'company_code': '00000'})


@login_required
@only_staff
def staff_chat(request):
    websocket.delete_chat_connection(request.user.staff_ip, request.user.staff_port)
    user = request.user
    user.staff_port = 0
    user.cur_process = 0
    if user.status != 4:
        user.status = 1
    user.save()
    company_code = user.company_code
    if str(company_code) not in settings.checkTime:
        settings.checkTime[str(company_code)] = 1
        wm = websocket.WebSocketServer(str(company_code))
        wm.setDaemon(True)
        wm.start()
    answer_list = AnswerList.objects.filter(company_code=request.user.company_code).order_by('created_at')
    return render(request, 'staff_chat.html', {'processNum': user.process_num, 'company_code': company_code, 'answer_list': answer_list})


@login_required
@only_company
def add_answer(request):
    answer = request.POST.get('answer_text')
    try:
        answer_list = AnswerList.objects.create(company_code=request.user.company_code, answer=answer)
        messages.success(request, '添加成功')
    except:
        messages.error(request, '添加失败，请重试！')
    return redirect('manage_answer')


@login_required
@only_company
def delete_answer(request, answer_id):
    try:
        answer = AnswerList.objects.get(id=answer_id)
        answer.delete()
        messages.success(request, '删除成功')
    except:
        messages.error(request, '删除失败，请重试！')
    return redirect('manage_answer')


@login_required
@only_company
def modify_answer(request, answer_id):
    answer_text = request.POST.get('answer_text')
    try:
        answer = AnswerList.objects.get(id=answer_id)
        answer.answer = answer_text
        answer.created_at = timezone.now()
        answer.save()
        messages.success(request, '修改成功')
    except:
        messages.error(request, '修改失败')
    return redirect('manage_answer')


@login_required
@only_company
def add_response(request):
    text = request.POST.get('text')
    statement_text = request.POST.get('statement_text')
    try:
        chatterbot_add(request, text=text, statement_text=statement_text)
        messages.success(request, '添加成功！')
    except DuplicationError:
        messages.error(request, '有重复，添加失败！')
    except:
        messages.error(request, '添加失败，请重试！')
    finally:
        return redirect('manage_robot')


@login_required
@only_company
def delete_response(request, res_id):
    try:
        chatterbot_delete(request, id=res_id)
        messages.success(request, '删除成功！')
    except:
        messages.success(request, '删除失败，请重试！')
    return redirect('manage_robot')


@login_required
@only_company
def modify_response(request, res_id):
    text = request.POST.get('text')
    statement_text = request.POST.get('statement_text')

    _query = chatterbot_filter_by(request, id=res_id)

    try:
        _query = chatterbot_filter_by(request, id=res_id)
        if _query:
            chatterbot_update(_query, {'text': text, 'statement_text': statement_text,
                                       'created_at': timezone.now()})
            messages.success(request, '修改成功')
        else:
            messages.error(request, '修改失败')
        return redirect('manage_robot')
    except:
        messages.error(request, '修改失败')
        return redirect('manage_robot')


@login_required
@only_company
def set_faq(request):
    show_responses = chatterbot_filter(request, ResponseTable.FAQ > 0)['response'].order_by(ResponseTable.FAQ)[:5]
    show_length = len(show_responses)
    hide_responses = chatterbot_filter(request, ResponseTable.FAQ == 0)['response'][:]
    hide_length = len(hide_responses)
    return render(request, 'manage_FAQ.html', locals())


@login_required
@only_company
def modify_faq_to_company(request):
    try:
        user = request.user
        user.is_set_faq = True
        user.save()
        messages.success(request, '修改成功')
    except:
        messages.error(request, '修改失败')
    return redirect('manage_robot')


@login_required
@only_company
def modify_faq_to_robot(request):
    try:
        user = request.user
        user.is_set_faq = False
        user.save()
        messages.success(request, '修改成功')
    except:
        messages.error(request, '修改失败')
    return redirect('manage_robot')


@login_required
@only_company
def up_question(request, count):
    count = int(count)
    _query = chatterbot_filter_by(request, FAQ=count)
    if count < 0 or count > 5:
        chatterbot_update(_query, {'FAQ': 0})
        return redirect('set_faq')
    elif count == 1:
        return redirect('set_faq')

    _query = _query
    to_change = chatterbot_filter_by(request, FAQ=count-1)
    chatterbot_change_FAQ(_query, to_change)
    return redirect('set_faq')


@login_required
@only_company
def down_question(request, count):
    count = int(count)
    _query = chatterbot_filter_by(request, FAQ=count)
    if count < 0 or count > 5:
        chatterbot_update(_query, {'FAQ': 0})
        return redirect('set_faq')
    elif count == 5:
        return redirect('set_faq')

    _query = _query
    to_change = chatterbot_filter_by(request, FAQ=count + 1)
    chatterbot_change_FAQ(_query, to_change)
    return redirect('set_faq')


@login_required
@only_company
def add_question(request, res_id):
    show_responses = chatterbot_filter(request, ResponseTable.FAQ > 0)['response'].order_by(ResponseTable.FAQ)[:5]
    show_length = len(show_responses)
    if show_length >= 5:
        return redirect('set_faq')

    res_id = int(res_id)
    _query = chatterbot_filter_by(request, id=res_id)
    chatterbot_update(_query, {'FAQ': show_length + 1})
    return redirect('set_faq')


@login_required
@only_company
def delete_question(request, count):
    _query = chatterbot_filter_by(request, FAQ=count)
    chatterbot_update(_query, {'FAQ': 0})

    filter_data = chatterbot_filter(request, ResponseTable.FAQ > count)
    session = filter_data['session']
    show_responses = filter_data['response'].order_by(ResponseTable.FAQ)
    for response in show_responses:
        response.FAQ -= 1
    session.commit()
    return redirect('set_faq')


def toolbar_chat(request, company_code):
    return render(request, 'toolbar_chat.html', {'company_code': company_code})


def check_ip(user_IP):
    IP = {'ip': user_IP}
    URL = 'http://ip.taobao.com/service/getIpInfo.php'
    address = []
    try:
        r = requests.get(URL, params=IP, timeout=10)
    except requests.RequestException as e:
        address.append('暂无信息')
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


@login_required
@only_company
def chatting_graph(request):
    data = []
    chat_record = ChatRecord.objects.filter(staff__company_code=request.user.company_code).order_by('start_time')
    if chat_record.first() is None:
        return render(request, 'chatting_graph.html')
    date = chat_record.first().start_time.date()
    num = 0
    for record in chat_record:
        if record.start_time.date() != date:
            _data = (str(date), num)
            data.append(_data)
            days = (record.start_time.date() - date).days
            for i in range(days - 1):
                date += timezone.timedelta(days=1)
                _data = (str(date), 0)
                data.append(_data)
            date = record.start_time.date()
            num = 0
        num += 1
    _data = (str(date), num)
    data.append(_data)
    days = (timezone.now().date() - date).days
    for i in range(days):
        date += timezone.timedelta(days=1)
        _data = (str(date), 0)
        data.append(_data)
    today_date = str(timezone.now().date())
    return render(request, 'chatting_graph.html', {'data': data, 'today_date': today_date})


@login_required
@only_company
def area_graph(request):
    today_date = str(timezone.now().date())
    data = []
    chat_record = ChatRecord.objects.filter(staff__company_code=request.user.company_code).order_by('start_time')
    for record in chat_record:
        _data = (str(record.start_time.date()), record.address)
        data.append(_data)
    return render(request, 'area_graph.html', {'data': data, 'today_date': today_date})


@login_required
@only_company
def todays_graph(request):
    today_date = str(timezone.now().date())
    data = []
    chat_record = ChatRecord.objects.filter(staff__company_code=request.user.company_code,
                                            start_time__date=timezone.now().date()).order_by('start_time')
    if chat_record.first() is None:
        for i in range(timezone.now().hour + 1):
            data.append((str(i), 0))
        return render(request, 'todays_graph.html', {'today_date': today_date})

    num = 0
    hours = chat_record.first().start_time.hour
    hour = hours
    for i in range(hours):
        _data = (str(i), 0)
        data.append(_data)

    for record in chat_record:
        if str(record.start_time.hour) != str(hour):
            _data = (str(hour), num)
            data.append(_data)
            hours = record.start_time.hour - hour
            for i in range(hours - 1):
                hour += 1
                _data = (str(hour), 0)
                data.append(_data)
            hour = record.start_time.hour
            num = 0
        num += 1
    _data = (str(hour), num)
    data.append(_data)
    return render(request, 'todays_graph.html', {'data': data, 'today_date': today_date})


def handle_uploaded_file(file):
    allow_suffix = ['jpg', 'png', 'jpeg', 'gif', 'bmp']
    file_suffix = file.name.split(".")[-1]
    if file_suffix not in allow_suffix:
        raise ExtensionError

    if file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
        raise SizeError
    path = settings.MEDIA_ROOT + '/'
    file_name = path + file.name
    destination = open(file_name, 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
    destination.close()
    return file.name


def example_company(request, company_code):
    try:
        company = MyUser.objects.get(is_company=True, is_active=True, is_verified=True,
                                           company_code=company_code)
    except:
        messages.error(request, '该公司不存在')
        return redirect('index')
    return render(request, 'example_company.html', {'company': company})
