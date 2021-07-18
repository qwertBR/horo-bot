import time
import psycopg2
import requests
import telebot
from bs4 import BeautifulSoup
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from tqdm import tqdm


conn = psycopg2.connect(
    host="ec2-54-220-53-223.eu-west-1.compute.amazonaws.com",
    database="d27og815j0mbf6",
    user="moqnbmvsyckqmd",
    port="5432",
    password="",
)
cur = conn.cursor()

sign = dict()
date = dict()
sign['водолей'] = 'aquarius'
sign['овен'] = 'aries'
sign['телец'] = 'taurus'
sign['близнецы'] = 'gemini'
sign['рак'] = 'cancer'
sign['лев'] = 'leo'
sign['дева'] = 'virgo'
sign['рыбы'] = 'pisces'
sign['козерог'] = 'capricorn'
sign['стрелец'] = 'sagittarius'
sign['скорпион'] = 'scorpio'
sign['весы'] = 'libra'

date['сегодня'] = 'today'
date['неделя'] = 'week'
date['месяц'] = 'month'
date['год'] = 'year'


def get_from_mailru(sign, date="today"):
    url = 'https://horo.mail.ru/prediction/' + sign + '/' + date
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)'
                      ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    page = requests.get(url, headers=header)
    soup = BeautifulSoup(page.text, 'html.parser')
    obj = soup.find_all('p')
    horo = ""
    for el in obj:
        horo += el.text
    return horo


def create_sonnik():
    cur.execute("DELETE FROM sonnik")
    url = 'https://horo.mail.ru/sonnik/'
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/40.0.1423.13 Safari/537.36'}
    page = requests.get(url, headers=header)
    soup = BeautifulSoup(page.text, 'html.parser')
    lol = soup.find_all("a", {"class": "link_term"})
    sonnik = dict()
    for x in lol:
        sonnik[x.text] = x['href']
    print(soup)
    for el in tqdm(sonnik):
        url = "https://horo.mail.ru" + sonnik[el]
        page = requests.get(url, headers=header)
        soup = BeautifulSoup(page.text, 'html.parser')
        obj = soup.find_all('p')
        mean = ""
        for ell in obj:
            mean += ell.text + '\n'
        print(mean)
        cur.execute("INSERT INTO sonnik (sleep, url, meaning) VALUES (%s, %s, %s)", (el, sonnik[el], mean))
        time.sleep(1)
    conn.commit()


def create_horo():
    cur.execute("DELETE FROM horoscope")
    for s in tqdm(sign):
        t = get_from_mailru(sign[s], "today")
        time.sleep(1)
        w = get_from_mailru(sign[s], "week")
        time.sleep(1)
        y = get_from_mailru(sign[s], "year")
        cur.execute("INSERT INTO horoscope (sign, today, week, year) VALUES (%s, %s, %s, %s)", (s, t, w, y))
        conn.commit()


create_horo()


def catalog_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    key_today = KeyboardButton(text="Гороскоп на день")
    key_week = types.KeyboardButton(text="Гороскоп на неделю")
    key_year = types.KeyboardButton(text="Гороскоп на год")
    key_sonnik = types.KeyboardButton(text="Сонник")
    keyboard.add(key_today, key_week, key_year, key_sonnik)
    return keyboard


def catalog_sign():
    keyboard1 = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    key_aquarius = KeyboardButton(text="водолей")
    key_aries = KeyboardButton(text="овен")
    key_taurus = KeyboardButton(text="телец")
    key_gemini = KeyboardButton(text="близнецы")
    key_cancer = KeyboardButton(text="рак")
    key_leo = KeyboardButton(text="лев")
    key_virgo = KeyboardButton(text="дева")
    key_pisces = KeyboardButton(text="рыбы")
    key_capricorn = KeyboardButton(text="козерог")
    key_sagittarius = KeyboardButton(text="стрелец")
    key_scorpio = KeyboardButton(text="скорпион")
    key_libra = KeyboardButton(text="весы")
    keyboard1.add(key_aquarius, key_aries, key_taurus, key_gemini, key_cancer, key_leo, key_virgo, key_pisces,
                  key_capricorn, key_sagittarius, key_scorpio, key_libra)
    return keyboard1


bot = telebot.TeleBot('')


@bot.message_handler(commands=['start'])
def start_message(message):
    start_keyboard = catalog_sign()
    bot.send_message(message.chat.id, f'Здравствуйте! Выберите ваш знак задиака:)',
                     reply_markup=start_keyboard)


@bot.message_handler(content_types=["text"])
def answer(message):
    if message.text in {"водолей", "овен", "телец", "близнецы", "рак", "лев", "дева", "рыбы", "козерог", "стрелец",
                        "скорпион", "весы"}:
        cur.execute("SELECT * FROM users WHERE login = %s", (message.from_user.username,))
        if len(cur.fetchall()) != 0:
            cur.execute("UPDATE users SET sign = %s WHERE login = %s", (message.text, message.from_user.username))
            bot.send_message(message.chat.id, "Выберете пункт из меню", reply_markup=catalog_keyboard())
            conn.commit()
        else:
            cur.execute("INSERT INTO users (login, name, sign) VALUES (%s, %s, %s)", (
                message.from_user.username, message.from_user.first_name + " " + message.from_user.last_name,
                message.text))
            conn.commit()
            bot.send_message(message.chat.id, "Выберете пункт из меню", reply_markup=catalog_keyboard())
    elif message.text == "Гороскоп на день":
        cur.execute("SELECT sign from users where login = %s ", (message.from_user.username,))
        si = cur.fetchall()[0][0]
        cur.execute("SELECT today FROM horoscope WHERE sign = %s", (si,))
        ans = cur.fetchall()[0][0]
        bot.send_message(message.chat.id, ans, reply_markup=catalog_keyboard())
    elif message.text == "Гороскоп на неделю":
        cur.execute("SELECT sign from users where login = %s ", (message.from_user.username,))
        si = cur.fetchall()[0][0]
        cur.execute("SELECT week FROM horoscope WHERE sign = %s", (si,))
        ans = cur.fetchall()[0][0]
        bot.send_message(message.chat.id, ans, reply_markup=catalog_keyboard())
    elif message.text == "Гороскоп на год":
        cur.execute("SELECT sign from users where login = %s ", (message.from_user.username,))
        si = cur.fetchall()[0][0]
        cur.execute("SELECT year FROM horoscope WHERE sign = %s", (si,))
        ans = cur.fetchall()[0][0]
        bot.send_message(message.chat.id, ans, reply_markup=catalog_keyboard())
    elif message.text == "Сонник":
        cur.execute("SELECT sleep from sonnik")
        son = ""
        for el in cur.fetchall():
            son += el[0] + '\n'
        bot.send_message(message.chat.id, 'У нас есть такие сонники:')
        bot.send_message(message.chat.id, son)
    else:
        req = message.text.capitalize()
        cur.execute("SELECT meaning from sonnik where sleep = %s", (req,))
        res = cur.fetchall()
        if len(res) == 0:
            bot.send_message(message.chat.id, "У наc нет такого сонника(")
        else:
            print(res)
            bot.send_message(message.chat.id, res[0][0])


bot.polling()
