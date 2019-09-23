# import the Flask class from the flask module
from flask import Flask, render_template, url_for, request, redirect, session
import pandas as pd
import os, subprocess
from data import Data
from projconfig import Projconfig #load project variables and stuff

PC = Projconfig() #initialse variables
imageDir = PC.staticDir+PC.imageDir #where images sit
DF_file = PC.staticDir+PC.DF_file #where df sits
DF = pd.read_pickle( DF_file ) #load dataframe
DATA = Data( DF ) #intiialise userdata

# create the application object
app = Flask(__name__)
app.config["SECRET_KEY"] = "bigsecret!"


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


# use decorators to link the function to a url
@app.route('/')
def index():
    return redirect(url_for('lul'))

@app.route('/lul', methods=['POST', 'GET'])
def lul():

    if "userdata" not in session:
        session["userdata"]=DATA

    userdata = session["userdata"]

    #just for testing
    if request.method == 'POST':
        #I am only here because soemthing was triggered!

        #buttons, so if triggered, will be not empty
        r1 = request.form.getlist('imSize')
        r2 = request.form.getlist('displayMode')

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

    return render_template('lul.html', DATA=userdata)

#clears cache in browser
# @app.after_request
# def add_header(response):
#     response.cache_control.max_age = 0
#     return response

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)
    #app.run()
