# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import InputRequired, Length, AnyOf
import pandas as pd
import os, subprocess
from collections import Counter
from data import Data
from projconfig import Projconfig #load project variables and stuff

PC = Projconfig() #initialse local configuarion variables
imageDir = PC.staticDir+PC.imageDir #where images sit
DF_file = PC.staticDir+PC.DF_file #where df sits

DF = pd.read_pickle( DF_file ) #load dataframe
DATA = Data( DF ) #initialise userdata
DF_HEADERS = ['kurzel', 'topic', 'basal', 'diff']


def _df_getUniqueColItems(df, colStr ):
    '''
    Get the unique elements of the column COLSTR from df.
    Komma-separated items are taken as several items.
    List is alphabetically sorted.
    '''
    if df.empty:
        lis = []
    else:
        s = ','.join(df[colStr].tolist()) #create comma-sepeated string
        LIS = s.split(',') #split at commas, list of all keywords
        lis = list(set(LIS)) #make items unique

    return sorted(lis) #return sorted list

def _df_compareWithList(df, colStr, lis):
    '''
    Counts how often the unique elements in lis are in COLSTR of df.
    A Comma-separated item in df is taken as several items.
    Returns a list N with N[i] is number of occurences of lis[i] in df.
    '''
    if ~df.empty and len(lis)>0:
        N = [0 for item in lis]
        s = ','.join(df[colStr].tolist()) #create comma-sepeated string
        LIS = s.split(',') #split at commas, list of all keywords
        M = Counter(LIS)
        for i in range(0,len(lis)):
            N[i] = M[lis[i]]
    else:
        N = [0 for item in lis]

    return N

def _df_filterByCol(df, colStr, whatStrList ):
    '''
        Gets a new df with only rows containing the strings in WHATSTRLIST in COLSTR.
        Empty whatStrList does nothing to df.
        Empty df does nothing.
    '''
    if len(whatStrList)>0 and ~df.empty:
        df = df[df[colStr].str.contains('|'.join(whatStrList))]

    return df

def _boutonfield(name='', label=[], list=[]):
    d = {
        'name' : name,
        'label': label,
        'value': range(0,len(label)),
        'list': list,
        'num' : len(label)
        }
    return d

def _radiofield(df, name=''):
    l = _df_getUniqueColItems(df,name)
    d = {
        'name': name,
        'label': l,
        'value': range(0,len(l)),
        'num'  : len(l)
        }
    return d

def guidatafix():
    gd = {
        'totalnum' : len(DF),
        'sortMode' : _boutonfield(name='sortMode', label=['sorted','shuffle']),
        'displayMode' : _boutonfield(name='displayMode', label=['Grid','Stapel']),
        'imSize' : _boutonfield(name='imSize', label=['k','K','g', 'G'], list=['200px','400px','600px','800px'])
    }

    for name in DF_HEADERS:
        gd[name] = _radiofield(DF, name=name)

    qpics_fn = DF['qImage_path'].to_list()
    apics_fn = DF['aImage_path'].to_list()

    return gd

def guidatauser_init(gdfix):
    ud = {
        'dropdownmenu_down': False,
        'fromwhom': '',
        'sortMode': {
            'isSel': [True, False]
            },
        'displayMode': {
            'isSel': [True, False]
            },
        'imSize': {
            'isSel': [False, False, True, False]
            }
    }

    for name in DF_HEADERS:
        ud[name] = {
            'isSel': [0 for item in gdfix[name]['label']],
            'num' : [0 for item in gdfix[name]['label']],
            }

    return ud

def guidatauser_updateSelection(gduser, data):
    '''
    Determines the logic of the gui.
    As all input elements are buttons, the data elements
    consist of a dict of the simple form {name, value}.
    '''

    if len(data)==0:
        return gduser #nothing to update

    for key, value in data.items():
        name = key #e.g. 'imSize'
        val = value #e.g. '0'

    if name in ['sortMode','displayMode','imSize']:
        #only one button is allowed to be active
        gduser['dropdownmenu_down'] = False
        gduser[name]['isSel'] = [False for i in gduser[name]['isSel']]
        gduser[name]['isSel'][int(val)] = True

    elif name in DF_HEADERS:
        #update pressed button: 0=neutral, 1=include, 2=exclude
        gduser['dropdownmenu_down'] = True
        gduser[name]['isSel'][int(val)] = gduser[name]['isSel'][int(val)] + 1
        if gduser[name]['isSel'][int(val)] > 2:
            gduser[name]['isSel'][int(val)] = 0

    gduser['fromwhom'] = name

    return gduser

def filterDataframe(gdf, gdu):
    '''
    Create new dataframe from DF based on gdfix gdf and gduser gdu.
    '''
    df = DF
    for name in DF_HEADERS:
        R = gdu[name]['isSel'] #could be 0 (ignore),1 (include), or 2 (exclude)
        wsl_incl = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] == 1 ]
        df = _df_filterByCol(df, name, wsl_incl )
        wsl_exc  = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] != 2  ]
        df = _df_filterByCol(df, name, wsl_incl )

    return df

def guidatauser_updateNum(df, gdf, gdu):
    '''
    Updates all num fields in the dict based on (a filtered) df.
    If df is empty, the returned values are 0.
    '''
    for name in DF_HEADERS:
        gdu[name]['num'] = _df_compareWithList( df, name, gdf[name]['label'] )

    return gdu

def df_getImagepaths(df):
    '''
    Gets the paths to the pictures based on (a filtered) df.
    If df is empty, empty lists are returned.
    '''
    ip = {}
    if len(df)>0:
        ip['ques'] = df['qImage_path'].to_list()
        ip['answ'] = df['aImage_path'].to_list()
    else:
        ip['ques'] = []
        ip['answ'] = []

    return ip

def df_sortByCol( df, colStr ):
    "sort df by column COLSTR"
    df = df.sort_values(by=colStr, ascending=True)
    return df

def df_shuffle( df ):
    return df.sample(frac=1)



gdfix = guidatafix()
gduser = guidatauser_init(gdfix)
gduser = guidatauser_updateSelection(gduser, {'kurzel':'0'})
df = filterDataframe(gdfix, gduser)
gduser = guidatauser_updateNum(df, gdfix, gduser)
ipaths = df_getImagepaths(df)

print(df)
# print(gduser['imSize']['isSel'])
# gduser = guidatauser_update(gduser, {'imSize':'1'})
# print(gduser['imSize']['isSel'])
print(gduser)
print(ipaths)


# create the application object
app = Flask(__name__)
app.config["SECRET_KEY"] = "bigsecret!"
app.config["DEBUG"] = True


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=2, max=10, message='Must be between 2 and 10 characters')])
    password = PasswordField('Password', validators=[InputRequired(), AnyOf(values=['bam', 'gym'])])
    language = SelectMultipleField(u'Programming Language', choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])



# use decorators to link the function to a url
@app.route('/')
def index():
    # return redirect(url_for('lul'))
    return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        return 'username: {}, password: {}, language: {}'.format(form.username.data, form.password.data, form.language.data)

    return render_template('login.html', form=form)

@app.route('/lul', methods=['POST', 'GET'])
def lul():

    if 'gduser' not in session or request.method == 'GET':
        session['gduser'] = guidatauser_init(gdfix)

    gduser = session['gduser']
    imPaths = df_getImagepaths([])

    #imPaths = df_getImagepaths([])
    userdata=DATA
    answ=[]


    #just for testing
    if request.method == 'POST':
        answ = request.form.to_dict() #get response (one of the buttons)
        gduser = guidatauser_updateSelection(gduser, answ) #update response
        df = filterDataframe(gdfix, gduser) #filter dataframe
        gduser = guidatauser_updateNum(df, gdfix, gduser) #update number of problems
        session['gduser']=gduser

        if gduser['sortMode']['isSel'][0]:
            df = df_sortByCol(df, 'diff')
        else:
            df = df_shuffle(df)

        imPaths = df_getImagepaths(df) #get the image paths

        #
        #     #check if I need to shuffle
        #     r3 = request.form.getlist('sortMode')
        #     if len(r3)>1: #yep
        #         userdata.update_isSel( r3 )
        #         df = df.sample(frac=1) #shuffle rows
        #         userdata.SHOWFLAG = False
        #
        #     #update num and pics based on df
        #     userdata.update_num(df)
        #     userdata.update_pics(df)

        #session["test"]="test2"

    return render_template('lul.html', DATA=userdata, GDFIX=gdfix, GDUSER=gduser, IMPATHS=imPaths, answ=answ)

#clears cache in browser
# @app.after_request
# def add_header(response):
#     response.cache_control.max_age = 0
#     return response

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run()
