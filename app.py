# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import InputRequired, Length, AnyOf
import sqlite3
import pandas as pd
import os, subprocess
from collections import Counter
from projconfig import Projconfig #load project variables and stuff

PC = Projconfig() #initialse local configuarion variables
imageDir = PC.staticDir+PC.imageDir #where images sit
DF_file = PC.staticDir+PC.DF_file_sus #where df sits

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

def guidatauser_update(gdu, name='', val=''):
    '''
    Updates gui user data gdu
    '''

    if len(name)>0 and name in ['sortMode','displayMode','imSize']:
        #only one button is allowed to be active
        #gdu['dropdownmenu_down'] = False
        gdu[name] = int(val)

    return gdu

def excFilter_update(ef, name='', val=''):
    '''
    Updates the filter ef
    '''

    if len(name)>0 and name in DF_HEADERS:
        #update pressed button: 0=neutral, 1=include, 2=exclude
        #gduser['dropdownmenu_down'] = True
        ef[name][int(val)] = ef[name][int(val)] + 1
        if ef[name][int(val)] > 2:
            ef[name][int(val)] = 0

    return ef

def df_applyExcfilter1(gdf, ef):
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

    return df


def df_applyExcfilter(gdf, ef, shuffle = False):
    '''
    Create new dataframe from DF based on gdfix gdf and excercise filter ef.
    '''
    BOOL_incl = [False for i in range(0,len(DF))]
    BOOL_excl = [False for i in range(0,len(DF))]
    for name in DF_HEADERS:
        R = ef[name] #could be 0 (ignore),1 (include), or 2 (exclude)
        wsl_incl = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] == 1 ]
        wsl_excl = [ gdf[name]['label'][i] for i in range(0,len(R)) if R[i] == 2  ]

        if len(wsl_incl) > 0:
            b = _df_findSelectedCol(DF, name, wsl_incl )
            BOOL_incl = [BOOL_incl[i] or b[i] for i in range(0,len(DF))]

        if len(wsl_excl) > 0:
            b = _df_findSelectedCol(DF, name, wsl_excl )
            BOOL_excl = [BOOL_excl[i] or b[i] for i in range(0,len(DF))]

        BOOL = [not BOOL_excl[i] and BOOL_incl[i] for i in range(0,len(DF))]
        df = DF[BOOL]

    if shuffle:
        df = df.sample(frac=1)

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





# create the application object
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///luldata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "bigsecret!"
app.config["DEBUG"] = True

db = SQLAlchemy(app)

gdfix = guidatafix()

# to create the table container for the first time, go to console
# type python, and do the folloing on the python prompt:
# >>> from app import db
# >>> db.create_all()
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30))

    filters = db.relationship('Filter', backref = 'filter', lazy='dynamic')

    def __repr__(self):
        return '<Member %r>' % self.username

class Filter(db.Model):
    '''
    Strings decoding the seslections, e.g. '00110120'
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    kurzel = db.Column(db.String(50))
    topic = db.Column(db.String(50))
    basal = db.Column(db.String(10))
    diff = db.Column(db.String(10))
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))

def db_addMembers():
    '''
    Add the Kürzel to the database member.
    Do this only by hand from the console as follows:
    >>> from app import db
    >>> from app import Member
    >>> from app import addMembers
    >>> db_addMembers()
    '''
    kurzellist = gdfix['kurzel']['label']
    for k in kurzellist:
        m = Member(username = k, password = 'empty')
        db.session.add(m)
        db.session.commit()

def db_addfilter(username, filtername, filter):
    '''
    adds a filter to the specifiend username
    '''
    mem = Member.query.filter(Member.username == username).first()
    fil = Filter(name=filtername,
            kurzel = ''.join(map(str, filter['kurzel'])), #convert list [0,1,0,1] to string '0101'
            topic = ''.join(map(str, filter['topic'])),
            basal = ''.join(map(str, filter['basal'])),
            diff = ''.join(map(str, filter['diff'])),
            member_id = mem.id
            )
    db.session.add(fil)
    db.session.commit()

def db_getfilternames(username):
    '''
    Get all filters for username, also their database id's
    '''
    teac = {}

    mem = Member.query.filter(Member.username == username).first()
    fil = mem.filters.all()

    teac['name'] = username
    teac['filterid'] = [fil[i].id for i in range(0,len(fil))]
    teac['filtername'] = [fil[i].name for i in range(0,len(fil))]
    teac['num'] =  len(fil)

    return teac



# def connect_db():
#     'connects to db'
#     sql = sqlite3.connect('/home/tom/prgs/bam_gyml/data.db')
#     sql.row_factory = sqlite3.Row
#     return sql
#
# def get_db():
#     if not hasattr(g, 'sqlite3'):
#         g.sqlite_db = connect_db()
#     return g.sqlite_db

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), AnyOf(gdfix['kurzel']['label'], message='Kürzel in Overleaf')] )
    password = PasswordField('Password', validators=[InputRequired()])

class FilterNameForm(FlaskForm):
    filtername = StringField('Username', validators=[InputRequired()])


# @app.teardown_appcontext
# def close_db(error):
#     if hasattr(g, 'sqlite_db'):
#         g.sqlite_db.close()


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = form.username.data
        passwd = form.password.data
        res = Member.query.filter(Member.username == user).first()
        passwd1 = res.password

        if passwd1 == passwd:
            session['teacher'] = user
            return redirect(url_for('lul'))

    return render_template('login.html', form=form)

@app.route('/view_db')
def view_db():
    db = get_db()

@app.route('/lul', methods=['POST', 'GET'])
def lul():

    form = FilterNameForm()
    teacher = {}

    if 'teacher' not in session:
        return redirect(url_for('login'))

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

        teacher = db_getfilternames(session['teacher'])

        session['gduser'] = gduser
        session['excfilter'] = excfilter

    elif request.method == 'POST':
        gduser = session['gduser']
        excfilter = session['excfilter']
        teacher = db_getfilternames(session['teacher'])

        answ = request.form.to_dict() #get response (one of the buttons)
        for key, value in answ.items(): #take last one
            name = key #e.g. 'imSize'
            val = value #e.g. 0

        gduser = guidatauser_update(gduser, name = name, val = val)
        excfilter = excFilter_update(excfilter, name = name, val = val)

        df = df_applyExcfilter(gdfix, excfilter, shuffle = gduser['sortMode']==1)
        excnum = df_getExcnum(df, gdfix)
        impaths = df_getImagepaths(df)

        if name in DF_HEADERS:
            gduser['dropdownmenu_down'] = True
        else:
            gduser['dropdownmenu_down'] = False

        if form.validate_on_submit(): #a new filtername was added for the current selection
            db_addfilter(teacher['name'], form.filtername.data, excfilter)
            teacher = db_getfilternames(session['teacher'])
            gduser['dropdownmenu_down'] = True

        session['gduser']=gduser
        session['excfilter'] = excfilter

    return render_template('lul.html', TEACHER=teacher, form=form, GDFIX=gdfix, GDUSER=gduser, EXCFILTER=excfilter, EXCNUM=excnum, IMPATHS=impaths, answ=answ)

#clears cache in browser
# @app.after_request
# def add_header(response):
#     response.cache_control.max_age = 0
#     return response

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run()
