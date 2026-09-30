#!/usr/bin/env python3

import json
import os
import shutil
from base64 import b64encode

import datetime
import io

import yaml

import numpy as np
import pandas as pd

import requests
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv
load_dotenv()

def foodexport():
    #xls = read_diary()
    xls = export_diary()
    save_diary(xls)
    get_favorite_food(xls)

def export_diary():

    login = os.environ['MY_NET_DIARY_LOGIN']
    password = os.environ['MY_NET_DIARY_PASSWORD']

    today = datetime.datetime.now()

    year = today.year
    print(year)

    auth_url = 'https://www.mynetdiary.com/muiSignIn.do'
    data_url = 'https://www.mynetdiary.com/exportData.do?year=' + str(year)
    print(data_url) 

    headers = {
        'Content-Type': 'application/json',
    }

    payload_dict = {"login":login,"password":password,"rememberMe":"true"}

    data = json.dumps(payload_dict)


    s = requests.Session()
    auth = s.post('https://www.mynetdiary.com/muiSignIn.do', headers=headers, data=data, auth=('login', 'password'))

    print('===AUTH===')
    print (auth)

    print('==COOKIES==')
    for cookie in s.cookies:
        print (cookie.name, cookie.value)

    download = s.get(data_url)

    print('===DOWNLOAD==')
    print (download)

    return download.content

def get_favorite_food(download):

    xls = pd.ExcelFile(io.BytesIO(download))

    df = pd.read_excel(xls, sheet_name=[0, 2], index_col=None)

    df[0] = df[0].assign(**{'Date & Time': pd.to_datetime(df[0]['Date & Time'])})
    df[0] = df[0].sort_values(by=['Date & Time'])
    df[0].reset_index(drop=True, inplace=True)
    print(df[0][['Name', 'Meal', 'Date & Time']])
    d = df[0].to_dict(orient='index')

    df[2] = df[2].assign(**{'Date': pd.to_datetime(df[2]['Date'])})
    df[2] = df[2].sort_values(by=['Date'])
    df[2] = df[2][df[2]['Measurement'] == 'Daily Steps Count']
    df[2].reset_index(drop=True, inplace=True)
    print(df[2][['Date', 'Measurement', 'Value']])
    e = df[2].to_dict(orient='index')

    if e:
        with open('steps.yml', 'w') as file:
            yaml.dump(e, file)
    else:
        print('no steps data in export; keeping existing steps.yml')

    if not d:
        print('no diary entries in export; keeping existing recent_food.yml')
        return

    meal = d[len(d)-1]['Meal']
    if meal == "Breakfast":
        pretty_meal = "breakfast"
    elif meal == "Lunch":
        pretty_meal = "lunch"
    elif meal == "Dinner":
        pretty_meal = "dinner"
    elif meal == "Snack":
        pretty_meal ="a snack"
    mostrecentfood ="food: For " + pretty_meal + " I had "
    snacktime = d[len(d)-1]['Date & Time']
    counter = 1
    if len(d) > 0:
        while snacktime == d[len(d)-counter]['Date & Time'] and meal == d[len(d)-counter]['Meal']:
            mostrecentfood += d[len(d)-counter]['Name']
            print(len(d))
            if len(d) < 3:
                break
            if snacktime == d[len(d)-(counter+1)]['Date & Time']:
                if snacktime == d[len(d)-(counter+2)]['Date & Time']:
                    mostrecentfood += ", "
                elif snacktime == d[len(d)-(counter+1)]['Date & Time']:
                    mostrecentfood += " & "
            counter += 1
    else:
        mostrecentfood = "not available"
        print(mostrecentfood)
    with open('recent_food.yml', 'w') as file:
        file.write(mostrecentfood)

def save_diary(download):
    with open('NewDiary.xls', 'wb') as file:
        file.write(download)

def read_diary():
    with open('NewDiary.xls', 'rb') as file:
        return file.read()

if __name__ == "__main__":
    foodexport()
