from chatterbot.storage import DjangoStorageAdapter
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from django.utils import timezone
import datetime
from chatterbot import ChatBot
from chatterbot.storage.sql_storage import *
import pymysql
from .models import MyUser
from chatterbot.trainers import ListTrainer
from .error import *


def create_database(company_code):
    db_name = 'robot_' + str(company_code)
    conn = pymysql.connect(host="localhost", user="root", passwd="qlalfqjsgh12", charset="utf8")
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;' % db_name)
    conn.select_db(db_name)
    cursor.close()
    conn.close()


def chatterbot_filter_by(request, **kwargs):
    company_code = request.user.company_code
    database_url = str(company_code)
    chatbot = ChatBot(
        database_url,
        database=database_url
    )
    session = chatbot.storage.Session()
    _statement_query = []
    _response_query = session.query(ResponseTable).filter_by(**kwargs)

    if _response_query.first():
        _statement = _response_query.first().statement_text
        _statement_query = session.query(StatementTable).filter_by(text=_statement)
    return {'response': _response_query, 'statement': _statement_query, 'session': session}


def chatterbot_filter(request, *criterion):
    company_code = request.user.company_code
    database_url = str(company_code)
    chatbot = ChatBot(
        database_url,
        database=database_url
    )
    session = chatbot.storage.Session()
    _statement_query = []
    _response_query = session.query(ResponseTable).filter(*criterion)

    if _response_query.first():
        _statement = _response_query.first().statement_text
        _statement_query = session.query(StatementTable).filter(StatementTable.text == _statement)
    return {'response': _response_query, 'statement': _statement_query, 'session': session}


def chatterbot_update(_query, values):
    response = _query['response']
    statement = _query['statement']
    if 'statement_text' in values:
        statement_text = values['statement_text']
        statement.update({'text': statement_text})
        del values['statement_text']

    session = _query['session']
    response.update(values)
    session.commit()


def chatterbot_add(request, text, statement_text):
    company_code = request.user.company_code
    database_url = str(company_code)
    chatbot = ChatBot(
        database_url,
        database=database_url
    )
    session = chatbot.storage.Session()
    _response_query = session.query(ResponseTable).filter_by(text=str(text)).first()
    _statement_query = session.query(StatementTable).filter_by(text=str(statement_text)).first()
    if _response_query or _statement_query:
        raise DuplicationError

    chatbot.set_trainer(ListTrainer)
    chatbot.train([
        text,
        statement_text
    ])


def chatterbot_delete(request, id):
    company_code = request.user.company_code
    database_url = str(company_code)
    chatbot = ChatBot(
        database_url,
        database=database_url
    )
    session = chatbot.storage.Session()
    to_delete = session.query(ResponseTable).filter_by(id=id)
    text=to_delete.first().text
    statement_text = to_delete.first().statement_text
    session.query(StatementTable).filter_by(text=text).delete()
    session.query(StatementTable).filter_by(text=statement_text).delete()
    to_delete.delete()
    session.commit()


def chatterbot_get_response(chatbot, msg):
    if len(msg) == 0:
        return "需要我帮忙吗？"
    session = chatbot.storage.Session()
    _responses = session.query(ResponseTable).all()
    if len(_responses) == 0:
        return '很抱歉，不是很懂您的问题哦'
    response = chatbot.get_response(msg)
    _response_query = session.query(ResponseTable).filter_by(statement_text=str(response))
    for _query in _response_query:
        _query.occurrence += 1
    session.commit()
    return response


def chatterbot_order(chatbot, company_code):
    try:
        responses = []
        user = MyUser.objects.get(is_company=True, company_code=int(company_code))
        if user.is_set_faq:
            db_name = 'robot_' + str(company_code)
            conn = pymysql.connect(host="localhost", user="root", passwd="qlalfqjsgh12", db=db_name, charset="utf8")
            cursor = conn.cursor()
            cursor.execute('SELECT text, FAQ FROM ResponseTable WHERE FAQ > 0 ORDER BY FAQ ASC')
            index = 0
            for _query in cursor:
                index += 1
                responses.append((str(index) + '. ' + str(_query[0]), str(_query[0])))
                if (index >= 5):
                    break
            cursor.close()
            conn.close()
        else:
            session = chatbot.storage.Session()
            _response_query = session.query(ResponseTable).filter().order_by(-ResponseTable.occurrence)
            index = 0
            for _query in _response_query:
                index += 1
                responses.append((str(index) + '. ' + str(_query.text), str(_query.text)))
                if (index >= 5):
                    break
        return responses
    except:
        responses = []
        return responses


def chatterbot_change_FAQ(_query, _to_change):
    session_first = _query['session']
    session_second = _to_change['session']
    temp = _query['response'].first().FAQ
    _response_first = _query['response'].first()
    _response_second = _to_change['response'].first()

    _response_first.FAQ = _response_second.FAQ
    _response_second.FAQ = temp

    session_first.commit()
    session_second.commit()
