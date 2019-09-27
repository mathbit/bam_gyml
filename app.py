# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import InputRequired, Length, AnyOf
import pandas as pd
import os, subprocess
from collections import Counter
from projconfig import Projconfig #load project variables and stuff

PC = Projconfig() #initialse local configuarion variables
imageDir = PC.staticDir+PC.imageDir #where images sit
DF_file = PC.staticDir+PC.DF_file #where df sits

DF = pd.read_pickle( DF_file ) #load dataframe
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
    if len(df)>0 and len(lis)>0:
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
    Empty df does nothing.
    Empty whatStrList produces empty df
    '''
    # if len(whatStrList)>0 and ~df.empty:
    #     df = df[df[colStr].str.contains('|'.join(whatStrList))]

    # if len(whatStrList) == 0:
    #     whatStrList=['--qwerty--'] #make sure to return emtpy dataframe

    if ~df.empty:
        df = df[df[colStr].str.contains('|'.join(whatStrList))]
        I = list(df[colStr].str.contains('|'.join(whatStrList)))
        print(I)
    return df

def _df_findSelectedCol(df, colStr, whatStrList ):
    '''
    Returns a list with truth-values, one for each column in df
    Entry is True, if at least one of the comma-seperated tag in
    the column colStr is in whatStrList.
    '''
    # if len(whatStrList)>0 and ~df.empty:
    #     df = df[df[colStr].str.contains('|'.join(whatStrList))]

    if ~df.empty:
        bool = df[colStr].str.contains('|'.join(whatStrList))

    print(bool)

    return bool

def _switchfield(name='', label=[], list=[]):
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
        'sortMode' : _switchfield(name='sortMode', label=['sorted','shuffle']),
        'displayMode' : _switchfield(name='displayMode', label=['Grid','Stapel']),
        'imSize' : _switchfield(name='imSize', label=['k','K','g', 'G'], list=['200px','400px','600px','800px'])
    }

    for name in DF_HEADERS:
        gd[name] = _radiofield(DF, name=name)

    return gd

def guidatauser_init(gdf):
    '''
    Sets the gui-buttons based on gdfix
    '''
    ud = {
        'dropdownmenu_down': False,
        'sortMode': 0,
        'displayMode': 0,
        'imSize': 2
    }

    return ud

def excFilter_init(gdf):
    '''
    Sets the excercise filter using gdfix
    '''
    ef = {}
    for name in DF_HEADERS:
        ef[name] = [0 for item in gdf[name]['label']]

    return ef

def guidatauser_update(gdu, data):
    '''
    Updates gui user data gdu
    As all input elements are buttons, the data elements
    consist of a dict of the simple form {name, value}.
    '''

    if len(data)==0:
        return gdu #nothing to update

    for key, value in data.items():
        name = key #e.g. 'imSize'
        val = int(value) #e.g. '0'

    if name in ['sortMode','displayMode','imSize']:
        #only one button is allowed to be active
        #gdu['dropdownmenu_down'] = False
        gdu[name] = val

    return gdu

def excFilter_update(ef, data):
    '''
    Updates the filter ef
    As all input elements are buttons, the data elements
    consist of a dict of the simple form {name, value}.
    '''

    if len(data)==0:
        return ef #nothing to update

    for key, value in data.items():
        name = key #e.g. 'imSize'
        val = value #e.g. '0'

    if name in DF_HEADERS:
        #update pressed button: 0=neutral, 1=include, 2=exclude
        #gduser['dropdownmenu_down'] = True
        ef[name][int(val)] = ef[name][int(val)] + 1
        if ef[name][int(val)] > 2:
            ef[name][int(val)] = 0

    return ef

def df_applyExcfilter(gdf, ef):
    '''
    Create new dataframe from DF based on gdfix gdf and excercise filter ef.
    '''
    df = DF
    for name in DF_HEADERS:
        R = ef[name] #could be 0 (ignore),1 (include), or 2 (exclude)
        wsl_incl = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] == 1 ]
        df = _df_filterByCol(df, name, wsl_incl )
        wsl_excl  = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] != 2  ]
        df = _df_filterByCol(df, name, wsl_excl )

    # if shuffle:
    #     df = df.sample(frac=1)

    return df

def _complementBool(boollist):
    return [not item for item in boollist]

def df_applyExcfilter1(gdf, ef):
    '''
    Create new dataframe from DF based on gdfix gdf and excercise filter ef.
    '''
    BOOL = [False for i in range(0,len(DF))]
    for name in DF_HEADERS:
        R = ef[name] #could be 0 (ignore),1 (include), or 2 (exclude)
        wsl_incl = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] == 1 ]
        df = _df_filterByCol(df, name, wsl_incl )
        wsl_excl  = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] != 2  ]
        df = _df_filterByCol(df, name, wsl_excl )

    # if shuffle:
    #     df = df.sample(frac=1)

    return df

def df_getExcnum(df, gdf):
    '''
    Gets number of exc in df for each keyword specified in gdf.
    If df is empty, the returned values are 0.
    '''
    num = {}
    for name in DF_HEADERS:
        num[name] = _df_compareWithList( df, name, gdf[name]['label'] )

    return num

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


gdfix = guidatafix()

gduser = guidatauser_init(gdfix)
excfilter = excFilter_init(gdfix)
#
# gduser = guidatauser_update(gduser, {'imSize':'3'})
excfilter = excFilter_update(excfilter, {'kurzel':'0'})
#
df = df_applyExcfilter(gdfix, excfilter)
#print(df)
# excnum = df_getExcnum(df, gdfix)
# ipaths = df_getImagepaths(df)

exit()

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

    if 'gduser' not in session:
        session['gduser'] = guidatauser_init(gdfix)

    if 'excfilter' not in session:
        session['excfilter'] = excFilter_init(gdfix)

    if request.method == 'GET':
        answ = request.form.to_dict()
        gduser = guidatauser_init(gdfix)
        excfilter = excFilter_init(gdfix)

        df = df_applyExcfilter(gdfix, excfilter)
        excnum = df_getExcnum(df, gdfix)
        impaths = df_getImagepaths(df)

        session['gduser'] = gduser
        session['excfilter'] = excfilter

    elif request.method == 'POST':
        gduser = session['gduser']
        excfilter = session['excfilter']

        answ = request.form.to_dict() #get response (one of the buttons)
        gduser = guidatauser_update(gduser, answ)
        excfilter = excFilter_update(excfilter, answ)

        df = df_applyExcfilter(gdfix, excfilter)
        excnum = df_getExcnum(df, gdfix)
        impaths = df_getImagepaths(df)

        if 'kurzel' in answ or 'topic' in answ or 'basal' in answ or 'diff' in answ:
            gduser['dropdownmenu_down'] = True
        else:
            gduser['dropdownmenu_down'] = False

        session['gduser']=gduser
        session['excfilter'] = excfilter

    return render_template('lul.html', DF=df, GDFIX=gdfix, GDUSER=gduser, EXCFILTER=excfilter, EXCNUM=excnum, IMPATHS=impaths, answ=answ)

#clears cache in browser
# @app.after_request
# def add_header(response):
#     response.cache_control.max_age = 0
#     return response

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run()
