class Projconfig:

    # local paths within the project root
    staticDir      = 'static/'
    latexDir       = 'latex/'
    imageDir       = latexDir+'page_images/'
    overleafgitDir = 'overleafgit/'
    latexFile_orig = latexDir+'main.tex'
    latexFile_new  = latexDir+'main_new.tex'
    latexPdfFile   = latexDir+'main_new.pdf'
    DF_file        = latexDir+'df.pkl'

    # bounding box for overleaf images
    overleafbb     = [165, 110, 1010, 700]

    # background color of cards (latex color)
    cardbgcolor    = 'lightgray!30'

    # resolution of images
    imres          = 200
