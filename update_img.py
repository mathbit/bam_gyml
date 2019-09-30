'''Creates the images from the pulled overleaf-latex file.

Takes the pulled overleaf latex file, produces a new latex
file with different formatting (in particular it produces a
page for the answer and a page for the answer).

This new latex file is then compiled to produce a
pdf-file. Each page of this pdf file is then converted
into a jpeg file. Theses images are used for the web-app.

Flags:
    -overleaf   The new latex file has same formatting
                as the overleaf file.
    -user       The new latex file is user-defined
                (at the moment hardcoded).
    -bb         Use automatically determined bounding box.
                In conjunction with the flag -overleaf,
                The bounding box is hardcoded.
'''


import pandas as pd
import numpy as np
import re, inspect, pypandoc, os.path, sys, subprocess
from shutil import copyfile
from PIL import Image, ImageOps
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from projconfig import Projconfig #load project variables and stuff
PC = Projconfig() #initialse variables

# LOCALPATHS = {
#     'static'        : './static/',
#     'latexFile_orig': 'latex/main.tex',
#     'latexFile_new' : 'latex/main_new.tex',
#     'latexPdfFile'  : 'latex/main_new.pdf',
#     'imageDir'      : 'latex/page_images/',
#     'DF_file'       : 'latex/df.pkl'
# }

def overleaflatex2df( fn, prefix='lul', imageDir='' ):
    """
    Extract problems from overlaf latex-file and stores them in dataframe.
    Thus it has a special formatting.
    It is assumed, that the file names have the following format:
    page numbers 1,3,5,... are the questions,
    page numbers 2,4,6,... are the answers
    If imageDir is an empty string, no attempt is made to find the image paths.
    """

    #read latex file from file fn into a string
    f = open(fn, 'r')
    lstr = f.read()
    f.close()

    #read image file names and place them into an dict for better access
    qdirDict = {}
    adirDict = {}
    if len(imageDir)>0:
        dirs = os.listdir(imageDir) #might be empty
        for item in dirs:
            #find page number
            s = item.split('.')
            s = s[0].split('-')
            pageNum = int(s[-1])
            if s[0] == prefix:
                #sort into correct dictionary
                if (pageNum % 2 == 0): #even
                    adirDict.update({int(pageNum/2):PC.staticDir+PC.imageDir+'/'+item})
                else: #odd
                    qdirDict.update({int((pageNum+1)/2):PC.staticDir+PC.imageDir+'/'+item})

    #initiate dataframe
    df = pd.DataFrame(columns=['kurzel', 'basal', 'topic', 'diff', 'question', 'answer','qImage_path','aImage_path'])

    #extract the problems from latex-str and add them to the dataframe
    searchStr=r'\\begin{Add}(.*?)\\question(.*?)\\solution(.*?)\\end{Add}'
    tupel = re.findall(searchStr,lstr,re.DOTALL)

    id=0
    for line in tupel:
        #question
        quesStr = line[1].strip() #get rid of trailing/leading whitespaces
        quesStr = quesStr[:-1] #remove }
        quesStr = quesStr[1:] #remove {
        quesStr = quesStr.strip()
        #solution
        solStr = line[2].strip()
        solStr = solStr[:-1] #remove }
        solStr = solStr[1:] #remove {
        solStr = solStr.strip()
        #keys
        keyStr = re.search(r'{(.*?)}{(.*?)}{(.*?)}{(.*?)}',line[0],re.DOTALL)
        #find corresponding image paths (if they exist)
        aImp = ''
        qImp = ''
        if len(qdirDict)>0:
            aImp = adirDict[id+1]
            qImp = qdirDict[id+1]
        #insert in table
        df.loc[id]=[keyStr.group(1), keyStr.group(2), keyStr.group(3), keyStr.group(4), quesStr, solStr, qImp,aImp]
        id = id + 1

    print('Found ', id, ' questions')
    return df;

def df2latex_user( df, latexFile_new ):
    '''
    Convert dataframe to Latex-text:
      page 1,3,5,... are the answers
      page 2,4,6,... are the solutions
    '''

    #preamble
    lStr = inspect.cleandoc(r'''
        \documentclass[12pt]{article}
        \usepackage[utf8]{inputenc}
        \usepackage[german]{babel}
        %\usepackage[a6paper,landscape]{geometry}
        \usepackage[margin=1mm, paperwidth=100mm, paperheight=70mm]{geometry}
        \usepackage{amssymb,amsmath,units,graphicx,pagecolor}
        \pagestyle{empty}
        \setlength{\parindent}{0in}

        \usepackage[sfdefault]{noto}
        \usepackage[T1]{fontenc}

        \newcommand{\question}[1]{#1}
        \newcommand{\solution}[1]{
            \vfill
            \noindent\rule{\textwidth}{0.5pt}% horizontal line
            \begin{center} #1 \end{center}
            \newpage
            }

        \begin{document}
        ''') + f'''\\pagecolor{{{PC.cardbgcolor}}}'''

    #add problems, use minipage to avoid page break, but will crop
    for i in range( len(df) ):
        QUES = df.loc[i,'question']
        ANSW = df.loc[i,'answer']
        lStr = lStr + '\n\n' + inspect.cleandoc(
            f'''
            \\begin{{minipage}}[t][\\textheight]{{\\textwidth}}
            \\question{{ {QUES} }}
            \\end{{minipage}}
            \\newpage
            \\begin{{minipage}}[t][\\textheight]{{\\textwidth}}
            \\question{{ {QUES} }}
            \\solution{{ {ANSW} }}
            \\end{{minipage}}
            '''
            )

    #add footer
    lStr = lStr + '\n\n' + r'\end{document}'

    #save
    f = open( latexFile_new, 'w')
    print( lStr, file=f)
    f.close()

    return lStr

def df2latex_overleaf( df, latexFile_new ):
    '''
    Convert dataframe to Latex-text:
      page 1,3,5,... are the answers
      page 2,4,6,... are the solutions
    Includes file 'preamble.tex' for later compiling.
    '''

    #preamble
    lStr = inspect.cleandoc(r'''
        \documentclass[12pt]{article}
        \input{preamble}
        \usepackage{pagecolor}
        \begin{document}
        ''') +  f'''\\pagecolor{{{PC.cardbgcolor}}}'''

    #add problems, use minipage to avoid page break, but will crop
    for i in range( len(df) ):
        QUES = df.loc[i,'question']
        ANSW = df.loc[i,'answer']
        basal = df.loc[i,'basal']
        topic = df.loc[i,'topic']
        diff = df.loc[i,'diff']
        kurzel = df.loc[i,'kurzel']
        lStr = lStr + '\n\n' + inspect.cleandoc(
            f'''
            \\begin{{Add}}{{{kurzel}}}{{{basal}}}{{{topic}}}{{{diff}}}
            \\question{{ {QUES} }}
            \\solution{{ }}
            \\end{{Add}}
            \\begin{{Add}}{{{kurzel}}}{{{basal}}}{{{topic}}}{{{diff}}}
            \\question{{ {QUES} }}
            \\solution{{ {ANSW} }}
            \\end{{Add}}
            '''
            )

    #add footer
    lStr = lStr + '\n\n' + r'\end{document}'

    #save
    f = open( latexFile_new, 'w')
    print( lStr, file=f)
    f.close()

    return lStr

def latex2pdf( latexFile ):
    "compile latex file using pdflatex to form a pdf-file"
    wdir, file = os.path.split(latexFile) #working directory where latex stuff sits

    #change to directory where latex resides, execute latex, and then jump back
    owd = os.getcwd() #current directory
    os.chdir(wdir) #go to new directory
    cmd = 'pdflatex -interaction=nonstopmode ' + file + ' >/dev/null'
    print('... compile latex using: '+cmd)
    p = subprocess.run(cmd,shell=True,check=True,universal_newlines=True, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr)
    else:
        print('DONE!')

    os.chdir(owd) #jump back

def deleteImages( imageDir ):
    "delete images in image directory"
    dirs = os.listdir(imageDir)
    counter = 0
    for item in dirs:
        fullpath = os.path.join(imageDir,item)
        os.remove(fullpath)
        counter = counter + 1

    if counter > 0:
        print('... deleted ' + str(counter) + ' files in directory ' + imageDir)

def copyImages( imageDir, prefix = 'q' ):
    "copy images in image directory"
    dirs = os.listdir(imageDir)
    counter = 0
    for item in dirs:
        s = item.split('-')
        fn = s[-1]
        dst = prefix + '-' + fn
        src = os.path.join(imageDir,item)
        dst = os.path.join(imageDir,dst)
        copyfile(src,dst)
        counter = counter + 1

    if counter > 0:
        print('... copied ' + str(counter) + ' files')

def createImagesFromPdf( imageDir, latexPdfFile, prefix = 'p'):
    "takes the pdf-file and converts each page into an image"
    images_from_path = convert_from_path(
        latexPdfFile,
        output_folder=imageDir,
        fmt='jpeg',
        dpi=PC.imres,
        )

    print('... converted ' + latexPdfFile + ' to images in ' + imageDir)

    #rename images
    print('... rename images')
    dirs = os.listdir(imageDir)
    for item in dirs:
        s = item.split('-')
        fn = s[-1]
        dst = prefix + '-' + fn
        #print('{} --> {}'.format(item, dst))
        item = os.path.join(imageDir,item)
        dst = os.path.join(imageDir,dst)
        os.rename(item, dst)

def getBoundingBox( im ):
    "finds the bounding box of an image"
    #getbox() works only for black background, so let us convert the image to black
    r2, g2, b2 = 0, 0, 0 # value that we want to replace it with
    r1, g1, b1 = im.getpixel((1, 1)) #estimate of actual background color

    if r1==0 & g1==0 & b1==0: #black background
        bb=im.getbox()
    elif r1==255 and g1==255 and b1==255: #white background, flip colors
        bb = invert_im.convert('RGB').getbbox()
        invert_im = ImageOps.invert(im)
        bb = invert_im.convert('RGB').getbbox() #convert to RGB first, otherwise getbox does not work
    else: #any other color
        data = np.array(im)
        red, green, blue = data[:,:,0], data[:,:,1], data[:,:,2]
        mask = (red == r1) & (green == g1) & (blue == b1)
        data[:,:,:3][mask] = [r2, g2, b2]
        bb = Image.fromarray(data.astype('uint8')).getbbox()

    return bb

def cropImages( imageDir, prefix = 'lul', bb = []):
    '''Crop the files in the image directory.
    Format: bb=(xlow,ylow,xhigh,yhigh).
    If overleaf=True, use the boundingbox
    bb=(165,110,1010,700)
    '''

    dirs = os.listdir(imageDir)
    counter = 0
    for item in dirs:
        s = item.split('-')
        if s[0] == prefix:
            fullpath = os.path.join(imageDir,item)
            if os.path.isfile(fullpath):
                f, e = os.path.splitext(fullpath)
                im = Image.open(fullpath).convert('RGB')
                if len(bb) == 0:
                    bb = getBoundingBox(im)

                im = im.crop( bb ) #corrected
                im.save(f + '.jpg', "JPEG", quality=80)
                counter = counter + 1

    if counter > 0:
        print('... cropped ' + str(counter) + ' files in directory ' + imageDir)


if __name__ == '__main__':

    if PC.staticDir.strip('/') not in os.listdir('./'):
        sys.exit(print('You are not in the root directory of the project.'))

    DF = overleaflatex2df( PC.staticDir+PC.latexFile_orig)

    OVERLEAF = False
    BB = False

    if len(sys.argv)>1 and sys.argv[1] == '-overleaf':
        OVERLEAF = True

    if len(sys.argv)>2 and sys.argv[2] == '-bb':
        BB = True

    if OVERLEAF:
        #new latex file is same as orig overleaf file
        print('... produce new similar overleaf latex for images')
        df2latex_overleaf( DF, PC.staticDir+PC.latexFile_new )
    else:
        #take user defined
        print('... produce new user defined latex for images')
        df2latex_user( DF, PC.staticDir+PC.latexFile_new )

    #create lul-images
    latex2pdf( PC.staticDir+PC.latexFile_new ) #create new pdf file
    deleteImages( PC.staticDir+PC.imageDir ) #delete all existing images
    createImagesFromPdf( PC.staticDir+PC.imageDir, PC.staticDir+PC.latexPdfFile, prefix='lul' ) #each page in pdf file transaltes into an images

    #create sus-images
    copyImages(PC.staticDir+PC.imageDir, prefix = 'sus')

    if BB:
        cropImages( PC.staticDir+PC.imageDir, prefix='lul', bb=PC.overleafbb_lul ) #removes empty white space of images
        cropImages( PC.staticDir+PC.imageDir, prefix='sus', bb=PC.overleafbb_sus )

    DF_lul = overleaflatex2df( PC.staticDir+PC.latexFile_orig, imageDir = PC.staticDir+PC.imageDir, prefix='lul') #update DF with links to images
    DF_lul.to_pickle( PC.staticDir+PC.DF_file_lul ) #save dataframe
    DF_sus = overleaflatex2df( PC.staticDir+PC.latexFile_orig, imageDir = PC.staticDir+PC.imageDir, prefix='sus') #update DF with links to images
    DF_sus.to_pickle( PC.staticDir+PC.DF_file_sus ) #save dataframe
