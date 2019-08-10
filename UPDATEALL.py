'''Pulls latex-file from Overleaf githup-repository.

Pulls latex-file from Overleaf githup-repository,
and puts it (and the preamble and pics) into the
latex-folder.

It is assumed that in the download directory:
1) git is installed and configured. Do a 'git config -l' to see
   if username and email are set.
2) the overleaf latex project is cloned. To do so:
    a) Find the link for your latex project on overleaf
      (Under the SHARE link, replace www with git)
    b) Go to the latex directory and clone
    > git init
    > git remote add overleaf https://git.overleaf.com/5ccf01163239d30f95bfd999
    > git config credential.helper store
    > git pull overleaf master
3) Setup .gitignore
    .DS_store
    *.pyc
    .env
Note that we will only pull, but we could also push with:
> git add .
> git commit -m 'some comment'
> git push overleaf master

Also, Heroku must be deployed. If not, do the following:
Heroku account:
    email: tbinzegger ...
    pw: the usual, framed in two !!
Install heroku cli:
> sudo snap install heroku --classic
> heroku login
> heroku create bam-lerbermatt #website is https://bam-lerbermatt.herokuapp.com
> git add .
> git commit -m 'Initial app boilerplate'
> git push heroku master #deploy code to heroku
> heroku ps:scale web=1  # run the app with a 1 heroku "dyno"

To push, use
> pip freeze | grep -v "pkg-resources" > requirements.txt
> git status
> git add .
> git commit -m 'update controls'
> git push heroku master
'''

import os, subprocess
from projconfig import Projconfig
PC = Projconfig() # load paths

if __name__ == '__main__':
    if PC.staticDir.strip('/') not in os.listdir('./'):
        sys.exit(print('You are not in the root directory of the project.'))

    #change to download directory, execute pull script, and then jump back
    owd = os.getcwd() #current directory
    os.chdir(PC.overleafgitDir) #go to new directory
    cmd = './pullOverleaf.sh'
    print('... pull latex from overleaf git-repository: '+cmd)
    p = subprocess.run(cmd,shell=True,check=True,universal_newlines=True, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr)
    else:
        print('DONE!')

    os.chdir(owd) #jump back

    #update images
    print('... update images')
    cmd = 'python update_img.py -overleaf -bb'
    p = subprocess.run(cmd,shell=True,check=True,universal_newlines=True, stderr=subprocess.PIPE)

    #deploy to heroku
    
