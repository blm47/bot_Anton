#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import sys
import time
import asterisk.agi
from botaster.speech_corrections import text_replace, answers
#from botaster.mods import speech_to_text, text_to_speech, tmppath, log, get_descripton
#from botaster.mods import dialog_log, message_parser, send_to_help
from botaster.mods import *

try:
    agi=asterisk.agi.AGI()
except Exception as err:
    print('AGI greate except -> %s'%err)

def get_file():
    return sys.argv[1]+'label'+sys.argv[2].replace(' ','')+'.wav'
def set_file():
    return sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')

def clear_cache():
    tmppath = '/'.join(sys.argv[1].split('/')[:-1]) + '/'
    tmpfiles = os.listdir(tmppath)
    cache = [tmppath + '/' + i for i in tmpfiles if os.stat(tmppath + '/' + i).st_atime + 60*60*24*2 < time.time()]
    for i in cache:
        os.remove(i)
    agi.verbose('Cache cleared!')

clear_cache()

if sys.argv[2].replace(' ','')=="1":
    try:
        f1 = get_file()
        #agi.set_variable('audio', '/var/lib/asterisk/agi-bin/default_speech/wait_pls')
        agi.verbose('Start recognise wav')
        result=speech_to_text(f1)
        agi.verbose('File :%s | Recognised as : %s'%(f1, result))
        dialog_log(f1, result)
        agi.verbose('Start geting Description...')
        description = get_descripton(result)
        result = text_replace(result)
        agi.verbose('Description geted -> %s'%description)
        description = text_replace(description)
        f2=  set_file()
        text = 'Вы сказали '+result+' -'*5 + 'Ваша проблема классифицирована как ' + ' -'*3 + description + ' -'*10 + \
        'Вы - хаат+ите оставить - заявку? - '
#            'А теперь давайте поиграем - - - Вы - хоот+ите купить - слона?'
#               ' С вас печеньки моему разработчику - - - Михаилу!'
        text_to_speech(text, f2 + '.wav')
        dialog_log(f2, text)
        agi.set_variable('audio', u'%s'%f2)
        agi.set_variable('label', '1')
    except Exception as err:
        err = '%s' % err
        agi.verbose('Error: -> %s'% err)
        if err.find('Unknown error') != -1:
            alarm_to_telegramm('yandex Speech cert experied ! \n %s' % err)
        agi.set_variable('audio', '/var/lib/asterisk/agi-bin/default_speech/repeat_pls')
        agi.set_variable('label', '0')
        agi.verbose('label=0')

elif sys.argv[2].replace(' ','')=="2":
    try:
        f1 = get_file()
        result=speech_to_text(f1)
        dialog_log(f1, result)
        f2 = set_file()
        agi.verbose('step=2... recognised request: %s'%result)
        if any([True for i in answers['yes'] if result.find(i) != -1]): #ответ Да
            text = 'Ваша проблема - - п+ереданна в - ай ти отдел. - - Вы можете оставаться на линии - - и \
            вам ответит - первый освободившийся специалист'
#+  'А так же - -  С вас печеньки моему разработчику - - - Михаилу!'
            text_to_speech(text, f2 + '.wav')
            dialog_log(f2, text)
            agi.set_variable('audio', u'%s'%f2)
            agi.set_variable('label', '2')
            #"""Отправляем заявку на хелп"""
            message = 'Обработан входящий звонок с номера: %s \n'%sys.argv[3] +\
            message_parser(sys.argv[1])
            res = send_to_help(message,sys.argv[1])
            if res == True:
                agi.verbose('Mail sended')
            agi.set_variable('flag', '2')
        elif any([True for i in answers['no'] if result.find(i) != -1]): #ответ Нет
            text = 'Я сообщил о вашей проблеме своим коллегам. - - Вы можете оставаться на линии - - и \
            вам ответит - первый освободившийся специалист'
            text_to_speech(text, f2 + '.wav')
            dialog_log(f2, text)
            agi.set_variable('audio', u'%s'%f2)
            #"""Отправляем заявку на хелп"""
            message = 'Обработан входящий звонок с номера: %s \n'%sys.argv[3] +\
            message_parser(sys.argv[1])
            res = send_to_help(message,sys.argv[1])
            if res == True:
                agi.verbose('Mail sended')
            agi.set_variable('flag', '2')
        else:
            text = 'Простите - я не понял вашего ответа - отпр+авить заявку \
            в ай ти отдел - - скажите ддаа или ннеетт'
            text_to_speech(text, f2 + '.wav')
            dialog_log(f2, text)
            agi.set_variable('audio', u'%s'%f2)
            agi.set_variable('label', '1')
    except Exception as err:
        agi.set_variable('audio', '/var/lib/asterisk/agi-bin/default_speech/repeat_pls')
        agi.set_variable('label', '1')
        agi.verbose('return to label=1. Except: %s' % err)
elif sys.argv[2].replace(' ','')=="3":
    agi.set_variable('flag', '2')

    #
    #
    # if 'да' in str(result.encode('utf-8')):
    #     agi.verbose('Yes')
    #     #///////////////////////////////
    #     # Здест должна быть проверка на существование абонента в базе данных
    #     #/////////////////////////////
    #
    #     file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
    #     text_to_speech(u'Вы хотите купить слона?', file+'.mp3')
    #     agi.set_variable('audio', file)
    # elif 'нет' in str(result.encode('utf-8')):
    #     agi.verbose('No')
    #     # Ставим метку в 0 что бы вернуться к шагй 1 и проигрываем файл
    #     agi.set_variable('label', '0')
    #     agi.set_variable('audio', '/etc/asterisk/ivr/Good_evening_Anton.wav')
    # else:
    #     agi.verbose('Error')
    #     # Если ответ не да и ни нет, говорим об ошибки и ставим метку на 1 что бы вернуться к шагу 2
    #     agi.set_variable('label', '1')
# elif sys.argv[2].replace(' ','')=="3":
#     agi.verbose('label='+sys.argv[2].replace(' ',''))
#     try:
#         result=speech_to_text(sys.argv[1]+'label'+sys.argv[2].replace(' ',''))
#     except:
#         agi.set_variable('label', '2')
#     if 'да' in str(result.encode('utf-8')):
#         agi.verbose('Hot')
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Сообщите показания горячего счетчика', file+'.mp3')
#         agi.set_variable('audio', file)
#     elif 'нет' in str(result.encode('utf-8')):
#         agi.verbose('Cold')
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Сообщите показания холодного счетчика', file+'.mp3')
#         agi.set_variable('audio', file)
#     else:
#         agi.verbose('Error')
#         agi.set_variable('label', '2')
# elif sys.argv[2].replace(' ','')=="4":
#     agi.verbose('label='+sys.argv[2].replace(' ',''))
#     try:
#         result=speech_to_text(sys.argv[1]+'label'+sys.argv[2].replace(' ',''))
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Ваши показания '+result+u'Скажите да или нет', file+'.mp3')
#         agi.set_variable('audio', file)
#     except:
#         agi.set_variable('label', '3')
#         agi.verbose('label=3')
# elif sys.argv[2].replace(' ','')=="5":
#     try:
#         result=speech_to_text(sys.argv[1]+'label'+sys.argv[2].replace(' ',''))
#     except:
#         agi.set_variable('label', '1')
#     if 'да' in str(result.encode('utf-8')):
#
#         #/////////////
#         #Обрабатываем результат и заносим в базу
#         #/////////////
#
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Хотите сообщить показания другого счетчика да или нет?', file+'.mp3')
#         agi.set_variable('audio', file)
#     elif 'нет' in str(result.encode('utf-8')):
#         agi.set_variable('label', '2')
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Показания какого счетчика вы хотите сообщить горячего или холодного?', file+'.mp3')
#         agi.set_variable('audio', file)
#     else:
#         agi.verbose('Error')
#         agi.set_variable('label', '2')
# elif sys.argv[2].replace(' ','')=="6":
#     try:
#         result=speech_to_text(sys.argv[1]+'label'+sys.argv[2].replace(' ',''))
#     except:
#         agi.set_variable('label', '1')
#     if 'да' in str(result.encode('utf-8')):
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Показания какого счетчика вы хотите сообщить горячего или холодного?', file+'.mp3')
#         agi.set_variable('audio', file)
#         agi.set_variable('label', '2')
#     elif 'нет' in str(result.encode('utf-8')):
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Досвидания', file+'.mp3')
#         agi.set_variable('audio', file)
#     else:
#         agi.verbose('Error')
#         file=sys.argv[1]+'outlabel'+sys.argv[2].replace(' ','')
#         text_to_speech(u'Хотите сообщить показания другого счетчика да или нет', file+'.mp3')
#         agi.set_variable('label', '5')
