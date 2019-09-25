# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import InputRequired, Length, AnyOf
import pandas as pd
import os, subprocess
from data import Data
from projconfig import Projconfig #load project variables and stuff

PC = Projconfig() #initialse local configuarion variables
imageDir = PC.staticDir+PC.imageDir #where images sit
DF_file = PC.staticDir+PC.DF_file #where df sits

DF = pd.read_pickle( DF_file ) #load dataframe
DATA = Data( DF ) #initialise userdata



def df_getUniqueColItems(df, colStr ):
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

def boutonfield(name='', label=[], list=[]):
    d = {
        'name' : name,
        'label': label,
        'value': range(0,len(label)),
        'list': list,
        'num' : len(label)
        }
    return d

def radiofield(df, name=''):
    l = df_getUniqueColItems(df,name)
    d = {
        'name': name,
        'label': l,
        'value': range(0,len(l)),
        'num'  : len(l)
        }
    return d

class Guidatafix:
    totalnum = len(DF)
    sortMode = boutonfield(name='sortMode', label=['sorted','shuffle'])
    displayMode = boutonfield(name='displayMode', label=['Grid','Stapel'])
    imSize = boutonfield(name='imSize', label=['k','K','g', 'G'], list=['200px','400px','600px','800px'])
    kurzel = radiofield(DF, name='kurzel')
    topic = radiofield(DF, name='topic')
    basal = radiofield(DF, name='basal')
    diff = radiofield(DF, name='diff')
    qpics_fn = DF['qImage_path'].to_list()
    apics_fn = DF['aImage_path'].to_list()

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
            },
        'kurzel': {
            'isSel': [False for item in gdfix.kurzel['label']],
            'numSel' : 0
            },
        'topic': {
            'isSel': [False for item in gdfix.kurzel['label']],
            'numSel' : 0
            },
        'basal': {
            'isSel': [False for item in gdfix.kurzel['label']],
            'numSel' : 0
            },
        'diff': {
            'isSel': [False for item in gdfix.kurzel['label']],
            'numSel' : 0
            }
    }
    return ud

def guidatauser_update(gdfix, data):
    '''
    As all input elements are buttons, the data elements
    consist of a imutabel tuple of the form [(source-btn,value)].
    This input is set to True.
    '''
    name = data[0][0] #e.g. 'imSize'
    value = data[0][1] #e.g. '100px'







gdfix = Guidatafix()
gduser = guidatauser_init(gdfix)
print(gduser['sortMode']['isSel'])



# create the application object
app = Flask(__name__)
app.config["SECRET_KEY"] = "bigsecret!"
app.config["DEBUG"] = True











def df_filterByCol( df, colStr, whatStrList ):
    '''
        Gets a new df with only rows containing the strings in WHATSTRLIST in COLSTR.
        Empty whatStrList does nothing to df.
        Empty df does nothing.
    '''
    if len(whatStrList)>0 and ~df.empty:
        df = df[df[colStr].str.contains('|'.join(whatStrList))]

    return df

def df_sortByCol( df, colStr ):
    "sort df by column COLSTR"
    df = df.sort_values(by=colStr, ascending=True)
    return df



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

    # if "userdata" not in session:
    #     session["userdata"]=DATA

    #userdata = session["userdata"]
    userdata=DATA
    r7=''

    #just for testing
    if request.method == 'POST':
        #I am only here because soemthing was triggered!

        #buttons, so if triggered, will be not empty
        r1 = request.form.getlist('imSize')
        r2 = request.form.getlist('displayMode')

        r7 = request.form

        if len(r1)>1:
            userdata.update_isSel( r1 )
            userdata.update_filterList()
            userdata.SHOWFLAG = False

        elif len(r2)>1:
            userdata.update_isSel( r2 )
            userdata.update_filterList()
            userdata.SHOWFLAG = False

        else:
            #I am here because one of the checkmarks in a group was triggered (kurzel, ...).
            #All groups that did not trigger the response return empty [].
            #The group that triggered the response returns ['kurzel','WiD',...].
            #In the case where the only mark in a group gets uncheck: ['kurzel']

            #update selections
            kur = request.form.getlist('kurzel')
            userdata.update_isSel( kur )
            top = request.form.getlist('topic')
            userdata.update_isSel( top )
            bas = request.form.getlist('basal')
            userdata.update_isSel( bas )
            dif = request.form.getlist('diff')
            userdata.update_isSel( dif )

            #filter df
            userdata.update_filterList()
            df = df_filterByCol( DF, 'kurzel', userdata.kurzel['filterList'] )
            df = df_filterByCol( df, 'topic', userdata.topic['filterList'] )
            df = df_filterByCol( df, 'basal', userdata.basal['filterList'] )
            df = df_filterByCol( df, 'diff', userdata.diff['filterList'] )

            userdata.SHOWFLAG = True #make sure input menue stays down

            #check if I need to shuffle
            r3 = request.form.getlist('sortMode')
            if len(r3)>1: #yep
                userdata.update_isSel( r3 )
                df = df.sample(frac=1) #shuffle rows
                userdata.SHOWFLAG = False

            #update num and pics based on df
            userdata.update_num(df)
            userdata.update_pics(df)

        session["test"]="test2"

    return render_template('lul.html', DATA=userdata, GDFIX=gdfix, GDUSER=gduser,  r7=r7)

#clears cache in browser
# @app.after_request
# def add_header(response):
#     response.cache_control.max_age = 0
#     return response

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run()
