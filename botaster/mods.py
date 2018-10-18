#!/usr/bin/python3.6
import requests
import subprocess
import tempfile
import os
import sys
import xml.etree.ElementTree as XmlElementTree
import httplib2
import uuid
import random
from yandex_speech import TTS
import json

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import smtplib
from os.path import basename


YANDEX_API_KEY = '3c28338a-219d-4ca4-9243-a0e4e673c4f6'#'16a830d4-b0a9-4bcd-830f-af208fdb83a1'

YANDEX_ASR_HOST = 'asr.yandex.net'
YANDEX_ASR_PATH = '/asr_xml'
CHUNK_SIZE = 1024 ** 2

#tmppath = '/tmp/bot_anton_log/'
speaker = 'ermil'  # ermil alyss

def log(a):
    import datetime
    with open(tmppath + 'debug_blm_log', 'a') as f:
        f.write(' '.join([datetime.datetime.now().isoformat(), str(a), '\n']))

def get_descripton(text):
    try:
        url = 'http://192.168.133.182/api/v1.0/get_type'
        data = {'description': text}
        r = requests.post(url, json=data, timeout=5).json()
        return r['type']
    except Exception:
        return 'не смог определить тип'

def get_temp_files(fullcall_id):
    call_id = fullcall_id.split('/')[-1]
    tmppath = '/'.join(fullcall_id.split('/')[:-1]) + '/'
    return [tmppath + x for x in os.listdir(tmppath) if x.find(call_id) != -1]

def alarm_to_telegramm(mess):
    p = 'https://mike007:R7i7YbE@91.211.88.155:65233'
    proxy={'https':p, 'http':p}
    token='580440068:AAHS2uckeIu-ygxOKEvCaGrPExdK9COf_rA'
    chat = 326404173 #blm47
    data = {"chat_id":chat,
               "text":mess}
    url = 'https://api.telegram.org/bot%s/sendMessage' % token
    requests.post(url, data=data, proxies=proxy, timeout=3)

def send_to_help(body_text, fullcall_id, subject='From bot_Anton', to_emails=['help@respect-mail.ru'], cc_emails=None):
    from_addr = 'bot_Anton@respect-mail.ru'
    file_to_attach = get_temp_files(fullcall_id)
    file_to_attach = [x for x in file_to_attach if x.find('.wav') != -1]
    # create the message
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    msg.attach(MIMEText(body_text))

    msg["To"] = ', '.join(to_emails)

    if cc_emails != None:
        msg["cc"] = ', '.join(cc_emails)
        emails = to_emails + cc_emails
    else:
        emails = to_emails

    try:
        for f in file_to_attach:
            with open(f, "rb") as fh:
                part = MIMEApplication(fh.read(), Name=basename(f))
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)
    except IOError:
        msg = "Error opening attachment file %s on file-> %s" % (file_to_attach, f)
        print(msg)
        sys.exit(1)
    msg = msg.as_string()

    server = smtplib.SMTP('mail.respect-mail.ru', 587)
    server.login('bot_anton@respect-mail.ru', 'XSuy43F7zTVp')
    server.sendmail(from_addr, emails, msg)
    server.quit()
    return True

def message_parser(fl):
    with open(fl, 'r') as f:
        con = json.loads(f.read())
    text = ''
    for n in sorted(con.keys()):
        for s in sorted(con[n].keys(), reverse=True):
            text += '%s : \n- %s \n\n'%(s, con[n][s])
    return text

def dialog_log(fname, text):
    if fname.find('out') == -1:
        fl = fname[:fname.find('label')]
        step = fname[fname.find('label')+5:fname.find('.wav')]
        type = 'Client'
    else:
        fl = fname[:fname.find('out')]
        step = fname[fname.find('label')+5:]
        type = 'Bot_Anton'
    print(' '.join([fl, step, type]))
    try:
        with open(fl, 'r') as f:
            context = json.loads(f.read())
    except FileNotFoundError:
        context = {}
    try:
        context[step].update({type:text})
    except KeyError:
        context.update({step:{type:text}})
    with open(fl, 'w') as f:
        f.write(json.dumps(context))
    return context


def convert_to_pcm16b16000r(in_filename=None, in_bytes=None):
    with tempfile.TemporaryFile() as temp_out_file:
        temp_in_file = None
        if in_bytes:
            temp_in_file = tempfile.NamedTemporaryFile(delete=False)
            temp_in_file.write(in_bytes)
            in_filename = temp_in_file.name
            temp_in_file.close()
        if not in_filename:
            raise Exception('Neither input file name nor input bytes is specified.')

        # Запрос в командную строку для обращения к FFmpeg
        command = [
            r'ffmpeg',  # путь до ffmpeg.exe
            '-i', in_filename,
            '-f', 's16le',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-'
        ]

        proc = subprocess.Popen(command, stdout=temp_out_file, stderr=subprocess.DEVNULL)
        proc.wait()

        if temp_in_file:
            os.remove(in_filename)

        temp_out_file.seek(0)
        return temp_out_file.read()


def read_chunks(chunk_size, bytes):
    while True:
        chunk = bytes[:chunk_size]
        bytes = bytes[chunk_size:]

        yield chunk

        if not bytes:
            break


def speech_to_text(filename=None, bytes=None, request_id=uuid.uuid4().hex, topic='notes', lang='ru-RU',
                   key=YANDEX_API_KEY):
    # Если передан файл
    if filename:
        with open(filename, 'br') as file:
            bytes = file.read()
    if not bytes:
        raise Exception('Neither file name nor bytes provided.')

    # Конвертирование в нужный формат
    bytes = convert_to_pcm16b16000r(in_bytes=bytes)

    # Формирование тела запроса к Yandex API
    url = YANDEX_ASR_PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
        request_id,
        key,
        topic,
        lang
    )

    # Считывание блока байтов
    chunks = read_chunks(CHUNK_SIZE, bytes)

    # Установление соединения и формирование запроса
    connection = httplib2.HTTPConnectionWithTimeout(YANDEX_ASR_HOST)

    connection.connect()
    connection.putrequest('POST', url)
    connection.putheader('Transfer-Encoding', 'chunked')
    connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
    connection.endheaders()

    # Отправка байтов блоками
    for chunk in chunks:
        connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
        connection.send(chunk)
        connection.send('\r\n'.encode())

    connection.send('0\r\n\r\n'.encode())
    response = connection.getresponse()

    # Обработка ответа сервера
    if response.code == 200:
        response_text = response.read()
        xml = XmlElementTree.fromstring(response_text)

        if int(xml.attrib['success']) == 1:
            max_confidence = - float("inf")
            text = ''

            for child in xml:
                if float(child.attrib['confidence']) > max_confidence:
                    text = child.text
                    max_confidence = float(child.attrib['confidence'])

            if max_confidence != - float("inf"):
                return text
            else:
                # Создавать собственные исключения для обработки бизнес-логики - правило хорошего тона
                raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
        else:
            raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
    else:
        raise SpeechException('Unknown error.\nCode: %s\n\n%s' % (response.code, response.read()))


class SpeechException(Exception):
    print(Exception)



def text_to_speech(text, file, key=YANDEX_API_KEY, speaker=speaker):

    tts = TTS(speaker, "wav", '%s' % key, emotion='good', speed='0.9', quality='lo')
    try:
        tts.generate(text.encode('utf-8'))
    except Exception:
        tts.generate(text)
    tts.save(file)
