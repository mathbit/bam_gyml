class Projconfig:

    # local paths within the project root
    staticDir      = 'static/'
    latexDir       = 'latex/'
    imageDir       = latexDir+'page_images'
    overleafgitDir = 'overleafgit/'
    latexFile_orig = latexDir+'main.tex'
    latexFile_new  = latexDir+'main_new.tex'
    latexPdfFile   = latexDir+'main_new.pdf'
    DF_file_lul    = latexDir+'df_lul.pkl'
    DF_file_sus    = latexDir+'df_sus.pkl'

    # bounding box for overleaf images
    overleafbb_lul     = [165, 110, 1010, 700]
    overleafbb_sus     = [165, 210, 1010, 700]

    # background color of cards (latex color)
    cardbgcolor    = 'lightgray!30'

    # resolution of images
    imres          = 200
