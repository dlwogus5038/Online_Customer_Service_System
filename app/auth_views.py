from django.contrib import auth, messages
from django.shortcuts import render, redirect, get_object_or_404
import uuid
from django.http import HttpResponseRedirect
import re
from django.core.mail import EmailMultiAlternatives
from WebSocket.websocket import *
from .views import *
from .error import *


def login_company(request):
    return render(request, 'login_company.html')


def login_staff(request):
    return render(request, 'login_staff.html')


def authenticate_company(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    company_code = request.POST.get('company_code')
    try:
        company_code = int(company_code)
    except:
        messages.error(request, '登录失败')
        return redirect('login_company')

    user = auth.authenticate(username=username, password=password)
    if not user or not user.is_company or int(user.company_code) != int(company_code) or not user.is_verified:
        messages.error(request, '登录失败')
        return redirect('login_company')
    auth.login(request, user)
    return redirect('index')


def authenticate_staff(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    company_code = request.POST.get('company_code')
    try:
        company_code = int(company_code)
    except:
        messages.error(request, '登录失败')
        return redirect('login_company')

    user = auth.authenticate(username=username, password=password)
    if not user or user.is_company or int(user.company_code) != int(company_code):
        messages.error(request, '登录失败')
        return redirect('login_staff')
    user.status = 1
    try:
        ip = request.META['HTTP_X_FORWARDED_FOR']
    except:
        ip = request.META['REMOTE_ADDR']

    delete_chat_connection(user.staff_ip, user.staff_port)
    user.cur_process = 0
    user.staff_ip = ip
    user.staff_port = '0'
    user.save()
    auth.login(request, user)
    return redirect('staff_chat')


def signup(request):
    return render(request, 'signup.html')


def signup_submit(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    password2 = request.POST.get('password2')
    email = request.POST.get('email')
    company_name = request.POST.get('company_name')

    if password != password2:
        messages.error(request, '密码不一致')
        return redirect('signup')

    if re.match('^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$', email) == None:
        messages.error(request, '邮箱规格不正确')
        return redirect('signup')
    try:
        verification_code = str(uuid.uuid1())
        data = VerificationData.objects.create(username=username, verification_code=verification_code)
        url = settings.SERVER_URL + '/verification/' + verification_code
        user = MyUser.objects.create_company(username=username, company_name=company_name, email=email,
                                             password=password)
        send_verification_mail(email, url, company_name, user.company_code)
        create_database(user.company_code)
        messages.success(request, '注册成功')
        return redirect('login_company')
    except:
        messages.error(request, '注册失败')
        return redirect('signup')


@login_required
def logout(request):
    user = request.user
    user.status = 0
    user.cur_process = 0
    user.save()
    auth.logout(request)
    return redirect('index')


@login_required
@only_company
def add_staff(request):
    company_code = request.user.company_code
    company_name = request.user.company_name
    username = request.POST.get('username')
    name = request.POST.get('name')
    is_active = request.POST.get('is_active')
    password = request.POST.get('password')
    process_num = request.POST.get('ProcessNum')
    email = request.POST.get('email')

    try:
        user = MyUser.objects.create_staff(username=username, name=name, email=email, is_active=is_active,
                                           process_num=process_num, company_code=company_code, password=password)
        user.is_verified = True
        user.save()
        return redirect('manage_staff')
    except:
        messages.error(request, '无法新增客服')
        return redirect('manage_staff')


@login_required
@only_company
def delete_staff(request, user_id):
    try:
        user = get_object_or_404(MyUser, pk=user_id)
        if user:
            user.delete()
            return redirect('manage_staff')
    except:
        messages.error(request, '删除失败，请重试！')
        return redirect('manage_staff')


@login_required
@only_company
def modify_staff(request, user_id):
    name = request.POST.get('name')
    is_active = eval(request.POST.get('is_active'))
    password = request.POST.get('password')
    process_num = request.POST.get('ProcessNum')
    email = request.POST.get('email')
    try:
        user = MyUser.objects.filter(id=user_id)
        if user:
            user.update(name=name, is_active=is_active, process_num=process_num, email=email)
            if len(password) > 0:
                user = user.first()
                user.set_password(password)
                user.save()
            messages.success(request, '修改成功')
        else:
            messages.error(request, '修改失败，请重试')
        return redirect('manage_staff')
    except:
        messages.error(request, '修改失败，请重试')
        return redirect('manage_staff')


@login_required
def self_information(request):
    return render(request, 'self_information.html')


@login_required
@only_company
def company_information(request):
    return render(request, 'company_information.html')


@login_required
def modify_password(request):
    old_password = request.POST.get('old_password')
    new_password1 = request.POST.get('new_password1')
    new_password2 = request.POST.get('new_password2')
    user = auth.authenticate(username=request.user, password=old_password)
    if user:
        if old_password == new_password1 and old_password == new_password2:
            messages.error(request, '新密码不能与原密码一致！')
        elif new_password1 and new_password2 and new_password1 == new_password2:
            user.set_password(new_password1)
            user.save()
            messages.success(request, '修改成功！')
            if user.is_company:
                return redirect('login_company')
            else:
                return redirect('login_staff')
        else:
            messages.error(request, '密码不一致！')
    else:
        messages.error(request, '原密码错误！')
    url = request.META.get('HTTP_REFERER', '/')
    return HttpResponseRedirect(url)


def send_verification_mail(email, url, company_name, company_code):
    url = str(url)
    email = str(email)
    subject = '来自思密答的注册验证邮件(系统邮件，请勿回复)'
    text_content = '这是一封重要的邮件.'
    html_content = '<p><strong>尊敬的用户，您好！</strong></p>' \
                   '<br>' \
                   '<p>感谢您对思密答的支持。</p>' \
                   '<p>' + str(company_name) + '公司的公司代码是:' \
                   '<strong> <font size=5 color="blue">' + str(company_code) + '</font></strong> </p>'\
                   '<p>请点击以下的链接完成验证:</p>' \
                   '<a href="' + url + '">' + url + '</a>' \
                   '<p>注:此链接有效期为30分钟，过期未验证将失效。如非本人操作，请忽略此邮件，' \
                   '由此给您带来的不便请谅解。</p>' \
                   '<p>如有疑问，请登录思密答。</p>' \
                   '<hr style="height:1px;border:none;border-top:1px dashed #0066CC;" />' \
                   '<p>此邮件由思密答系统发出，系统不接受回信，请勿直接回复。</p>'
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def validate_user(request, verification_code):
    try:
        data = get_object_or_404(VerificationData, verification_code=verification_code)
        user = MyUser.objects.filter(username=data.username)
        user.update(is_verified=True)
        data.delete()
        return verification_success(request, user.first().company_code)
    except:
        return verification_fail(request)


def verification_success(request, company_code=None):
    return render(request, 'success.html', {'company_code': company_code})


def verification_fail(request):
    return render(request, 'fail.html')


def forget_password1(request):
    return render(request, 'forget_password1.html')


def forget_password2(request):
    username = request.POST.get('username')
    user = MyUser.objects.filter(username=username).first()
    if not user:
        messages.error(request, '用户不存在')
        return redirect('forget_password1')

    if not user.is_verified:
        messages.error(request, '得先认证邮箱')
        return redirect('forget_password1')

    user_email = user.email
    verification_code = str(random.randint(10000, 99999))
    data = VerificationData.objects.filter(username=username).first()
    if not data:
        data = VerificationData.objects.create(username=username, verification_code=verification_code)
    else:
        data.verification_code=verification_code
        data.save()
    return render(request, 'forget_password2.html', {'username': username, 'user_email': user_email, 'verification_code' : verification_code})


def forget_password3(request):
    try:
        username = request.POST.get('username')
        verification_code = request.POST.get('verification_code')
        data = VerificationData.objects.filter(username=username).first()
        if not data:
            messages.error(request, '已过期')
            return redirect('forget_password1')
        if data.verification_code == verification_code:
            return render(request, 'forget_password3.html', {'username': username})
        else:
            messages.error(request, '验证码错误，请重试!')
            return redirect('forget_password1')
    except:
        return redirect('forget_password1')


def forget_password4(request):
    username = request.POST.get('username')
    user = MyUser.objects.filter(username=username).first()
    new_password1 = request.POST.get('new_password1')
    new_password2 = request.POST.get('new_password2')
    if user:
        if new_password1 and new_password2 and new_password1 == new_password2:
            user.set_password(new_password1)
            user.save()
            return render(request, 'forget_password4.html')
        else:
            messages.error(request, '密码不一致！')
    return redirect('self_information')


@login_required
def modify_image(request):
    user = request.user
    if not user:
        return redirect('login_company')
    if request.FILES:
        try:
            file = request.FILES.get('image')
            user.image = handle_uploaded_file(file)
        except SizeError:
            messages.error(request, '超出文件系统大小限制！（10MB）')
            return redirect('self_information')
        except ExtensionError:
            messages.error(request, '文件格式错误！')
            return redirect('self_information')
        except:
            messages.error(request, '修改失败！')
            return redirect('self_information')
    user.save()
    messages.success(request, '修改成功')
    return redirect('self_information')


@login_required
@only_staff
def modify_status_to_true(request):
    user = request.user
    user.status = 1
    user.save()
    messages.success(request, '修改成功')
    return redirect('staff_chat')


@login_required
@only_staff
def modify_status_to_out(request):
    user = request.user
    user.status = 4
    user.save()
    messages.success(request, '修改成功')
    return redirect('staff_chat')


@login_required
@only_company
def detail(request):
    user_id = request.GET.get('staff_id')
    staff = MyUser.objects.filter(id=user_id).first()
    if not staff:
        messages.error(request, '该客服人员不存在')
        return redirect('index')
    elif staff.company_code != request.user.company_code:
        messages.error(request, '没有资格访问')
        return redirect('index')

    after_range_num = 5
    before_range_num = 4
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except:
        page = 1

    data = staff.chatrecord_set.all().order_by('-start_time')
    paginator = Paginator(data, 10)
    try:
        data_list = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        data_list = paginator.page(1)
    if page >= after_range_num:
        page_range = paginator.page_range[page - after_range_num:page + before_range_num]
    else:
        page_range = paginator.page_range[0:int(page) + before_range_num]
    data = []
    _index = 1
    for datum in data_list.object_list:
        _data = (datum, (data_list.number - 1) * 10 + _index, staff.chatdata_set.filter(user_ip=datum.user_IP, user_port=datum.user_Port).order_by('created_at'))
        data.append(_data)
        _index += 1

    for datum, num, chatting_record in data:
        new_msg = ""
        for record in chatting_record:
            new_msg = ""
            for i in range(len(record.Data)):
                if record.Data[i] == '\n':
                    new_msg += '\\n'
                else:
                    new_msg += record.Data[i]
            record.Data = new_msg
    return render(request, 'staff_detail.html', locals())


@login_required
@only_company
def modify_company_information(request):
    user = request.user
    phonenumber = request.POST.get('phonenumber')
    linkman = request.POST.get('linkman')
    chatterbot_nickname = request.POST.get('chatterbot_nickname')
    user.phonenumber = phonenumber
    user.linkman = linkman
    user.chatterbot_nickname = chatterbot_nickname
    if request.FILES.get('chatterbot_image') is not None:
        try:
            file = request.FILES.get('chatterbot_image')
            user.chatterbot_image = handle_uploaded_file(file)
        except SizeError:
            messages.error(request, '超出文件系统大小限制！')
            return redirect('company_information')
        except ExtensionError:
            messages.error(request, '文件格式错误！')
            return redirect('company_information')
        except:
            messages.error(request, '修改失败！')
            return redirect('company_information')
    user.save()
    messages.success(request, '修改成功')
    return redirect('company_information')


@login_required
def modify_nickname(request):
    user = request.user
    nickname = request.POST.get('nickname')
    user.nickname = nickname
    if request.FILES.get('image') is not None:
        try:
            file = request.FILES.get('image')
            user.image = handle_uploaded_file(file)
        except SizeError:
            messages.error(request, '超出文件系统大小限制！')
            return redirect('self_information')
        except ExtensionError:
            messages.error(request, '文件格式错误！')
            return redirect('self_information')
        except:
            messages.error(request, '修改失败！')
            return redirect('self_information')
    user.save()
    messages.success(request, '修改成功')
    return redirect('self_information')
