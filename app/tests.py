from django.test import TestCase
from django.test.client import Client
from .models import *
from OnlineCustomerService.settings import LOGIN_URL
from .chatbot import create_database
import pymysql
import os

# 通过输入 python manage.py test OR ./manage.py test 执行此文件

# You can change this value to what you want
default_company_name = 'aaa'
default_change_company_name = 'bbb'
default_staff_name = 'ccc'
default_change_staff_name = 'ddd'
default_change_image_url = 'images/chatterbot_default_image.png'
default_change_chatterbot_nickname = '机器人'
default_change_chatterbot_image = 'images/default_image.png'
default_change_company_phonenum = '00011112222'
default_change_company_manager_name = '李在弦'

class Test01Index(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        # 访问首页， 不会出错
        response = index_test(self.c)
        self.assertEqual(response.status_code, 200)


def index_test(c):
    users = MyUser.objects.filter(is_company=True, is_active=True, is_verified=True)
    companies = []
    for user in users:
        company = (user.username, user.company_code)
        companies.append(company)
    response = c.post('/', {'companies': companies})
    return response


class Test02SignUp(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        # 注册成功
        response = sign_up(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login_company')
        # 注册失败
        response1 = sign_up_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/signup')
        # 认证成功
        response2 = verification(self.c)
        self.assertEqual(response2.status_code, 200)
        # 认证失败
        response3 = verification_fail(self.c)
        self.assertEqual(response3.status_code, 404)


def sign_up(c):
    response = c.post('/signup/submit',
                      {'username': default_company_name, 'password': default_company_name,
                       'password2': default_company_name,
                       'email': '15510380063@163.com', 'company_name': default_company_name})
    return response


def sign_up_fail(c):
    response = c.post('/signup/submit',
                      {'username': '', 'password': '',
                       'password2': '',
                       'email': '', 'company_name': ''})
    return response


def verification(c):
    verif = VerificationData.objects.get(username=default_company_name)
    response = c.post('/verification/' + str(verif.verification_code))
    return response


def verification_fail(c):
    response = c.post('/verification/')
    return response


class Test03LoginCompany(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        # 登录失败
        response1 = company_login_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/login_company')
        # 登录成功
        response = company_login(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')


def company_login(c):
    user = MyUser.objects.get(username=default_company_name)
    response = c.post('/authenticate_company',
                      {'username': default_company_name, 'password': default_company_name,
                       'company_code': user.company_code})
    return response


def company_login_fail(c):
    user = MyUser.objects.get(username=default_company_name)
    response = c.post('/authenticate_company',
                      {'username': '', 'password': '',
                       'company_code': 0})
    return response


class Test04VisitCompanyPage(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        # 访问企业页面，不会出错
        response = visit_company_page(self.c)
        user = MyUser.objects.get(username=default_company_name)
        self.assertEqual(response['response'].status_code, 200)
        self.assertEqual(response['company_code'], user.company_code)


def visit_company_page(c):
    user = MyUser.objects.get(username=default_company_name)
    company = MyUser.objects.get(is_company=True, is_active=True, is_verified=True, company_code=user.company_code)
    response = c.post('/example/' + str(user.company_code), {'company': company})
    return {
        'response': response,
        'company_code': user.company_code
    }


class Test05Logout(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        # 登出，不会出错
        response = logout(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')


def logout(c):
    response = c.post('/logout')
    return response


class Test06CreateStaff(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        # 失败创建新客服人员
        response1 = create_staff_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/manage_staff')
        self.assertEqual(MyUser.objects.filter(is_admin=False, is_company=False).first(), None)
        # 成功创建新客服人员
        response = create_staff(self.c)
        staff = MyUser.objects.get(username=default_staff_name)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_staff')
        self.assertEqual(staff.username, default_staff_name)


def create_staff(c):
    response = c.post('/manage_staff/add',
                      {'username': default_staff_name, 'name': default_staff_name,
                       'is_active': 1,
                       'email': '15510380063@163.com', 'ProcessNum': 5,
                       'password': default_staff_name})
    return response


def create_staff_fail(c):
    response = c.post('/manage_staff/add',
                      {'username': '', 'name': '',
                       'is_active': 1,
                       'email': '', 'ProcessNum': 0,
                       'password': ''})
    return response


class Test07DeleteStaff(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        create_staff(self.c)
        # 失败删除客服人员
        response1 = delete_staff_fail(self.c)
        self.assertEqual(response1.status_code, 404)
        # 成功删除客服人员
        response = delete_staff(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_staff')
        self.assertEqual(MyUser.objects.filter(username=default_staff_name).first(), None)


def delete_staff(c):
    bbb_user = MyUser.objects.get(username=default_staff_name, is_company=False, is_admin=False)
    response = c.post('/manage_staff/delete/' + str(bbb_user.id))
    return response


def delete_staff_fail(c):
    try:
        response = c.post('/manage_staff/delete/')
    except:
        return None
    return response


class Test08ModifyStaff(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        create_staff(self.c)
        # 修改客服人员个人信息，不会出错
        response = modify_staff(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_staff')
        self.assertEqual(MyUser.objects.get(username=default_staff_name).email, default_change_staff_name + '@163.com')
        self.assertEqual(MyUser.objects.get(username=default_staff_name).is_active, 1)
        self.assertEqual(MyUser.objects.get(username=default_staff_name).name, default_change_staff_name)
        self.assertEqual(MyUser.objects.get(username=default_staff_name).process_num, 5)


def modify_staff(c):
    bbb_user = MyUser.objects.get(username=default_staff_name, is_company=False, is_admin=False)
    response = c.post('/manage_staff/modify/' + str(bbb_user.id),
                      {'password': default_change_staff_name, 'name': default_change_staff_name,
                       'is_active': 1,
                       'email': default_change_staff_name + '@163.com', 'ProcessNum': 5})
    return response


class Test09SelfInformation(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        # 显示个人信息，不会出错
        response = self_information(self.c)
        self.assertEqual(response.status_code, 200)


def self_information(c):
    response = c.post('/self_information')
    return response


class Test10CompanyInformation(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        # 显示企业信息，不会出错
        response = company_information(self.c)
        self.assertEqual(response.status_code, 200)


def company_information(c):
    response = c.post('/company_information')
    return response


class Test11ModifyPassword(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        # 失败修改密码
        response1 = modify_password_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/')
        old_pass = MyUser.objects.get(username=default_company_name).password
        # 成功修改密码
        response = modify_password(self.c)
        new_pass = MyUser.objects.get(username=default_company_name).password
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login_company')
        self.assertNotEqual(old_pass, new_pass)


def modify_password(c):
    response = c.post('/modify_password',
                      {'old_password': default_company_name, 'new_password1': default_change_company_name,
                       'new_password2': default_change_company_name})
    return response


def modify_password_fail(c):
    response = c.post('/modify_password',
                      {'old_password': default_company_name, 'new_password1': '',
                       'new_password2': ''})
    return response


class Test12ForgetPassword(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)

        # 失败找回密码步骤2
        response1 = forget_password1(self.c)
        self.assertEqual(response1.status_code, 200)
        response2 = forget_password2_fail(self.c)
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(response2.url, '/forget_password1')

        # 失败找回密码步骤3
        response1 = forget_password1(self.c)
        self.assertEqual(response1.status_code, 200)
        response2 = forget_password2(self.c)
        self.assertEqual(response2.status_code, 200)
        response3 = forget_password3_fail(self.c)
        self.assertEqual(response3.status_code, 302)
        self.assertEqual(response3.url, '/forget_password1')

        # 失败找回密码步骤4
        response1 = forget_password1(self.c)
        self.assertEqual(response1.status_code, 200)
        response2 = forget_password2(self.c)
        self.assertEqual(response2.status_code, 200)
        response3 = forget_password3(self.c)
        self.assertEqual(response3.status_code, 200)
        response4 = forget_password4_fail(self.c)
        self.assertEqual(response4.status_code, 302)
        self.assertEqual(response4.url, '/self_information')

        # 成功找回密码功能
        response1 = forget_password1(self.c)
        self.assertEqual(response1.status_code, 200)
        response2 = forget_password2(self.c)
        self.assertEqual(response2.status_code, 200)
        response3 = forget_password3(self.c)
        self.assertEqual(response3.status_code, 200)
        old_pass = MyUser.objects.get(username=default_company_name).password
        response4 = forget_password4(self.c)
        new_pass = MyUser.objects.get(username=default_company_name).password
        self.assertEqual(response4.status_code, 200)
        self.assertNotEqual(old_pass, new_pass)


def forget_password1(c):
    response = c.post('/forget_password1')
    return response


def forget_password2(c):
    response = c.post('/forget_password2',
                      {'username': default_company_name})
    verification(c)
    return response


def forget_password2_fail(c):
    response = c.post('/forget_password2',
                      {'username': 'kkkkkkkkkkk'})
    return response


def forget_password3(c):
    verif = VerificationData.objects.get(username=default_company_name)
    response = c.post('/forget_password3',
                      {'username': default_company_name, 'verification_code': verif.verification_code})
    return response


def forget_password3_fail(c):
    response = c.post('/forget_password3',
                      {'username': 'kkkkkkkkkkkkkk', 'verification_code': 'kkkkkkkkkkkkkkkkk'})
    return response


def forget_password4(c):
    response = c.post('/forget_password4',
                      {'username': default_company_name, 'new_password1': default_change_company_name,
                       'new_password2': default_change_company_name})
    return response


def forget_password4_fail(c):
    response = c.post('/forget_password4',
                      {'username': default_company_name, 'new_password1': '',
                       'new_password2': ''})
    return response


class Test13ModifyImage(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)

        # 失败修改图片
        response1 = modify_image_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/self_information')
        self.assertEqual(MyUser.objects.get(username=default_company_name).image.url, '/images/default_image.png')
        # 成功修改图片
        response = modify_image(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/self_information')
        self.assertEqual(MyUser.objects.get(username=default_company_name).image.url, '/' + default_change_image_url)


def modify_image(c):
    data = {
        'image': open(default_change_image_url, 'rb')
    }
    response = c.post('/modify_image', data=data)
    return response


def modify_image_fail(c):
    data = {
        'image': open('app/static/js/date.js', 'rb')
    }
    response = c.post('/modify_image', data=data)
    return response


class Test14ModifyCompanyInformation(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        # 失败修改企业信息
        response1 = modify_company_information_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/company_information')
        self.assertEqual(MyUser.objects.get(username=default_company_name).image.url, '/images/default_image.png')
        # 成功修改企业信息
        response = modify_company_information(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/company_information')
        self.assertEqual(MyUser.objects.get(username=default_company_name).image.url,
                         '/' + default_change_chatterbot_image)
        self.assertEqual(MyUser.objects.get(username=default_company_name).phonenumber, default_change_company_phonenum)
        self.assertEqual(MyUser.objects.get(username=default_company_name).linkman, default_change_company_manager_name)
        self.assertEqual(MyUser.objects.get(username=default_company_name).chatterbot_nickname,
                         default_change_chatterbot_nickname)


def modify_company_information(c):
    data = {
        'phonenumber': default_change_company_phonenum,
        'linkman': default_change_company_manager_name,
        'chatterbot_nickname': default_change_chatterbot_nickname,
        'chatterbot_image': open(default_change_chatterbot_image, 'rb')
    }
    response = c.post('/modify_company_information', data=data)
    return response


def modify_company_information_fail(c):
    data = {
        'phonenumber': default_change_company_phonenum,
        'linkman': default_change_company_manager_name,
        'chatterbot_nickname': default_change_chatterbot_nickname,
        'chatterbot_image': open('app/static/js/date.js', 'rb')
    }
    response = c.post('/modify_company_information', data=data)
    return response


class Test15LoginStaff(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        create_staff(self.c)
        logout(self.c)
        # 失败客服人员登录
        response1 = staff_login_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/login_staff')
        # 成功客服人员登录
        response = staff_login(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/staff_chat')


def staff_login(c):
    user = MyUser.objects.get(username=default_staff_name)
    response = c.post('/authenticate_staff', {
        'username': default_staff_name,
        'password': default_staff_name,
        'company_code': user.company_code
    })
    return response


def staff_login_fail(c):
    user = MyUser.objects.get(username=default_staff_name)
    response = c.post('/authenticate_staff', {
        'username': default_staff_name,
        'password': default_staff_name,
        'company_code': 0
    })
    return response


class Test16ModifyNickname(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        create_staff(self.c)
        logout(self.c)
        staff_login(self.c)
        # 失败修改客服人员昵称
        response1 = modify_nickname_fail(self.c)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, '/self_information')
        self.assertEqual(MyUser.objects.get(username=default_staff_name).nickname, '客服人员')
        # 成功修改客服人员昵称
        response = modify_nickname(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/self_information')
        self.assertEqual(MyUser.objects.get(username=default_staff_name).nickname, default_staff_name)
        self.assertEqual(MyUser.objects.get(username=default_staff_name).image.url, '/' + default_change_image_url)


def modify_nickname(c):
    user = MyUser.objects.get(username=default_staff_name)
    response = c.post('/modify_nickname', {
        'nickname': default_staff_name,
        'image': open(default_change_image_url, 'rb')
    })
    return response


def modify_nickname_fail(c):
    user = MyUser.objects.get(username=default_staff_name)
    response = c.post('/modify_nickname', {
        'nickname': default_staff_name,
        'image': open('app/static/js/date.js', 'rb')
    })
    return response


class Test17ModifyStatusToTrue(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        create_staff(self.c)
        logout(self.c)
        staff_login(self.c)
        # 修改客服人员当前状态，不会出错
        response = modify_status_to_true(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/staff_chat')
        self.assertEqual(MyUser.objects.get(username=default_staff_name).status, 1)


def modify_status_to_true(c):
    response = c.post('/modify_status_to_true')
    return response


class Test18ModifyStatusToOut(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        create_staff(self.c)
        logout(self.c)
        staff_login(self.c)
        # 修改客服人员当前状态，不会出错
        response = modify_status_to_out(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/staff_chat')
        self.assertEqual(MyUser.objects.get(username=default_staff_name).status, 4)


def modify_status_to_out(c):
    response = c.post('/modify_status_to_out')
    return response


class Test19StaffDetail(TestCase):
    def setUp(self):
        self.c = Client()

    def test(self):
        sign_up(self.c)
        verification(self.c)
        company_login(self.c)
        create_staff(self.c)
        # 显示客服人员信息，不会出错
        response = staff_detail(self.c)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')


def staff_detail(c):
    staff = MyUser.objects.get(username=default_staff_name)
    response = c.post('/staff_detail', {'staff_id': staff.id})
    return response


def login(client, company_code):
    response = client.post('/authenticate_company',
                           {'company_code': company_code, 'username': 'test_company',
                            'password': 'test_password'})
    return response


def add_answer(client, value):
    response = client.post('/manage_answer/add', value)
    return response


def modify_answer(client, url, value):
    response = client.post('/manage_answer/modify/' + str(url), value)
    return response


def delete_answer(client, url):
    response = client.post('/manage_answer/delete/' + str(url))
    return response


def add_robot(client, value):
    response = client.post('/manage_robot/add', value)
    return response


def modify_robot(client, url, value):
    response = client.post('/manage_robot/modify/' + str(url), value)
    return response


def add_faq(client, index):
    response = client.post('/manage_FAQ/add/' + str(index))
    return response


def up_faq(client, index):
    response = client.post('/manage_FAQ/up/' + str(index))
    return response


def down_faq(client, index):
    response = client.post('/manage_FAQ/down/' + str(index))
    return response


def delete_faq(client, index):
    response = client.post('/manage_FAQ/delete/' + str(index))
    return response


def primary_setup():
    company = MyUser.objects.create_company(username='test_company', password='test_password',
                                            email='kjs_214@naver.com', company_name='test_company_name')
    company.is_verified = True
    company.save()
    company_code = str(company.company_code)
    create_database(company_code)
    return company


class Test20AddAnswer(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_answer(self.client, {'company_code': self.company.company_code, 'answer_text': 'test_answer_1'})
        answer = AnswerList.objects.filter(company_code=self.company.company_code, answer='test_answer_1')
        self.assertIsNotNone(answer.first())


class Test21ModifyAnswer(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_answer(self.client, {'company_code': self.company.company_code, 'answer_text': 'test_answer_1'})
        modify_answer(self.client, '2',
                      {'company_code': self.company.company_code, 'answer_text': 'test_answer_1_modified'})
        answer = AnswerList.objects.filter(company_code=self.company.company_code, answer='test_answer_1_modified')
        self.assertIsNotNone(answer.first())


class Test22DeleteAnswer(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_answer(self.client, {'company_code': self.company.company_code, 'answer_text': 'test_answer_1'})
        delete_answer(self.client, '1')
        answer = AnswerList.objects.filter(company_code=self.company.company_code, answer='test_answer_1')
        self.assertIsNotNone(answer.first())


class Test23AddRobot(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_robot(self.client, {'text': 'test_text_1', 'statement_text': 'test_statement_text_1'})
        conn = pymysql.connect(host="localhost", user="root", passwd="qlalfqjsgh12",
                               db='robot_' + str(self.company.company_code), charset="utf8")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ResponseTable WHERE text='test_text_1' and statement_text='test_statement_text_1'")
        self.assertIsNotNone(cursor.fetchone())
        cursor.close()
        conn.close()


class Test24ModifyRobot(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_robot(self.client, {'text': 'test_text_1', 'statement_text': 'test_statement_text_1'})
        modify_robot(self.client, '1',
                     {'text': 'test_text_1_modified', 'statement_text': 'test_statement_text_1_modified'})
        conn = pymysql.connect(host="localhost", user="root", passwd="qlalfqjsgh12",
                               db='robot_' + str(self.company.company_code), charset="utf8")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ResponseTable WHERE text='test_text_1' and statement_text='test_statement_text_1'")
        self.assertIsNone(cursor.fetchone())
        cursor.execute(
            "SELECT * FROM ResponseTable WHERE text='test_text_1_modified' and statement_text='test_statement_text_1_modified'")
        self.assertIsNotNone(cursor.fetchone())
        cursor.close()
        conn.close()


class Test25AddFAQ(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_robot(self.client, {'text': 'test_text_1', 'statement_text': 'test_statement_text_1'})
        add_faq(self.client, '1')
        conn = pymysql.connect(host="localhost", user="root", passwd="qlalfqjsgh12",
                               db='robot_' + str(self.company.company_code), charset="utf8")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT FAQ FROM ResponseTable WHERE id='1'")
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.close()
        conn.close()


class Test26UpFAQ(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_robot(self.client, {'text': 'test_text_1', 'statement_text': 'test_statement_text_1'})
        add_robot(self.client, {'text': 'test_text_2', 'statement_text': 'test_statement_text_2'})
        add_faq(self.client, '1')
        add_faq(self.client, '2')
        up_faq(self.client, '2')
        conn = pymysql.connect(host="localhost", user="root", passwd="qlalfqjsgh12",
                               db='robot_' + str(self.company.company_code), charset="utf8")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT FAQ FROM ResponseTable WHERE id='2'")
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.execute(
            "SELECT FAQ FROM ResponseTable WHERE id='1'")
        self.assertEqual(cursor.fetchone()[0], 2)
        cursor.close()
        conn.close()


class Test27DeleteFAQ(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        add_robot(self.client, {'text': 'test_text_1', 'statement_text': 'test_statement_text_1'})
        add_robot(self.client, {'text': 'test_text_2', 'statement_text': 'test_statement_text_2'})
        add_faq(self.client, '1')
        add_faq(self.client, '2')
        delete_faq(self.client, '1')
        conn = pymysql.connect(host="localhost", user="root", passwd="qlalfqjsgh12",
                               db='robot_' + str(self.company.company_code), charset="utf8")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT FAQ FROM ResponseTable WHERE id='2'")
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.execute(
            "SELECT FAQ FROM ResponseTable WHERE id='1'")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.close()
        conn.close()


class Test28SetFAQToCompany(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        self.client.post('/manage_FAQ/company')
        company = MyUser.objects.get(company_code=self.company.company_code, is_company=True)
        self.assertEqual(company.is_set_faq, True)


class Test29SetFAQToRobot(TestCase):
    def setUp(self):
        self.company = primary_setup()
        self.client = Client()

    def test(self):
        login(self.client, self.company.company_code)
        self.client.post('/manage_FAQ/company')
        self.client.post('/manage_FAQ/robot')
        company = MyUser.objects.get(company_code=self.company.company_code, is_company=True)
        self.assertEqual(company.is_set_faq, False)


class Test30JumpPage(TestCase):
    def setUp(self):
        self.company = MyUser.objects.create_company(username='test_company', password='test_password',
                                                     email='kjs_214@naver.com', company_name='test_company_name')
        self.company.is_verified = True
        self.company.save()
        company_code = str(self.company.company_code)
        create_database(company_code)
        self.staff = MyUser.objects.create_staff(username='test_staff', password='test_password',
                                                 email='kjs_214@naver.com', company_code=company_code, is_active='True',
                                                 name='tester', process_num=3)
        self.client = Client()
        self.no_limit = ['/', '/preview', '/chat_' + company_code, '/m_chat_' + company_code,
                         '/toolbar_chat_' + company_code, '/example/' + company_code, '/image_send', '/send_image']
        self.only_company = ['/manage_staff', '/manage_robot', '/manage_answer', '/manage_answer/add',
                             '/manage_answer/modify/1', '/manage_answer/delete/1', '/manage_robot/add',
                             '/manage_robot/add', '/manage_robot/modify/1', '/manage_FAQ', '/manage_FAQ/add/1',
                             '/manage_FAQ/add/2', '/manage_FAQ/up/2', '/manage_FAQ/down/2', '/manage_FAQ/delete/2',
                             '/manage_robot/delete/1', '/manage_robot/delete/2', '/manage_FAQ/company',
                             '/manage_FAQ/robot', '/chatting_graph', '/todays_graph', '/area_graph']
        self.company_302 = ['/manage_answer/add', '/manage_answer/modify/1', '/manage_answer/delete/1',
                            '/manage_robot/add', '/manage_robot/add', '/manage_robot/modify/1', '/manage_FAQ/add/1',
                            '/manage_FAQ/add/2', '/manage_FAQ/up/2', '/manage_FAQ/down/2', '/manage_FAQ/delete/2',
                            '/manage_robot/delete/1', '/manage_robot/delete/2', '/manage_FAQ/company',
                            '/manage_FAQ/robot']
        self.only_staff = ['/staff_base', '/staff_chat']

    def test01_permission_not_log_in(self):
        for url in self.no_limit:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)
        for url in self.only_company:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url[:14], LOGIN_URL)
        for url in self.only_staff:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url[:14], LOGIN_URL)

    def test02_permission_company(self):
        self.client.post('/authenticate_company',
                         {'company_code': self.company.company_code, 'username': self.company.username,
                          'password': 'test_password'})
        for url in self.no_limit:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)
        for url in self.only_company:
            if url in self.company_302:
                continue
            else:
                response = self.client.post(url)
                self.assertEqual(response.status_code, 200)
        for url in self.only_staff:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url[:14], LOGIN_URL)

    def test03_permission_staff(self):
        self.client.post('/authenticate_staff',
                         {'company_code': self.staff.company_code, 'username': self.staff.username,
                          'password': 'test_password'})
        for url in self.no_limit:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)
        for url in self.only_company:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url[:14], LOGIN_URL)
        for url in self.only_staff:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)

    def test04_company_database(self):
        self.client.post('/authenticate_company',
                         {'company_code': self.company.company_code, 'username': self.company.username,
                          'password': 'test_password'})
        response = self.client.post('/manage_answer/add',
                                    {'company_code': self.company.company_code, 'answer_text': 'test_answer_1'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_answer')

        response = self.client.post('/manage_answer/modify/1', {'answer_text': 'test_answer_1_modified'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_answer')

        response = self.client.post('/manage_answer/delete/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_answer')

        response = self.client.post('/manage_robot/add',
                                    {'text': 'test_text_1', 'statement_text': 'test_statement_text_1'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_robot')

        response = self.client.post('/manage_robot/add',
                                    {'text': 'test_text_2', 'statement_text': 'test_statement_text_2'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_robot')

        response = self.client.post('/manage_robot/modify/2',
                                    {'text': 'test_text_2_modified',
                                     'statement_text': 'test_statement_text_2_modified'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_robot')

        response = self.client.post('/manage_FAQ/add/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_FAQ')

        response = self.client.post('/manage_FAQ/add/2')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_FAQ')

        response = self.client.post('/manage_FAQ/up/2')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_FAQ')

        response = self.client.post('/manage_FAQ/down/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_FAQ')

        response = self.client.post('/manage_FAQ/delete/2')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_FAQ')

        response = self.client.post('/manage_FAQ/delete/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_FAQ')

        response = self.client.post('/manage_robot/delete/2')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_robot')

        response = self.client.post('/manage_FAQ/company')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_robot')

        response = self.client.post('/manage_FAQ/robot')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage_robot')