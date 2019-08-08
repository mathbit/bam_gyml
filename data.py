from collections import Counter

class Data:
    def __init__(self, df):
        if df.empty:

            self.SHOWFLAG = False
            self.FROMWHOM = ''
            self.totalNum = 0
            self.sortMode = {}
            self.displayMode = {}
            self.imSize = {}
            self.kurzel = {}
            self.topic = {}
            self.basal = {}
            self.diff = {}
            self.qpics = []
            self.apics = []
        else:
            kurzellist = self.df_getUniqueColItems(df,'kurzel')
            topiclist = self.df_getUniqueColItems(df,'topic')
            basallist = self.df_getUniqueColItems(df,'basal')
            difflist = self.df_getUniqueColItems(df,'diff')

            self.SHOWFLAG = False # drop down menu up
            self.totalNum = len(df)
            self.FROMWHOM = '' #string describing who triggered the POST, updates by update_isSel

            self.sortMode = {
                'text'  : ['shuffle'],
                'label' : ['shuffle'],
                'isSel' : [False],
                'num'   : -1,
                'filterList': [] #contains all labels which are true in isSel
                }

            self.displayMode = {
                'text'  : ['Grid','Stapel'],
                'label' : ['grid','stack'],
                'isSel' : [True, False],
                'num'   : -1,
                'filterList': []
                }

            self.imSize = {
                'text'  : ['1','2','3', '4'],
                'label' : ['200px','400px','600px','800px'],
                'isSel' : [False, True, False, False],
                'num'   : -1,
                'filterList': []
                }

            self.kurzel = {
                'label': kurzellist,
                'isSel': [False for item in kurzellist],
                'num'  : -1,
                'filterList' : []
                }

            self.topic = {
                'label': topiclist,
                'isSel': [False for item in topiclist],
                'num'  : -1,

                'filterList' : []
                }

            self.basal = {
                'label': basallist,
                'isSel': [False for item in basallist],
                'num'  : -1,
                'filterList' : []
                }

            self.diff = {
                'label': difflist,
                'isSel': [False for item in difflist],
                'num'  : -1,
                'filterList' : []
                }

            self.qpics = []
            self.apics = []

        self.update_filterList()
        self.update_num( df )
        self.update_pics ( df )

    def findCurrent(self,lis,logicLis):
        "find the value in list lis given by boolean list"
        item = 0
        for i in range(0,len(lis)):
            if logicLis[i]:
                item = lis[i]

        return item

    def df_getUniqueColItems(self, df, colStr ):
        '''
        Get the unique elements of the column COLSTR from df.
        Komma-separated items are taken as several items.
        List is alphabetically sorted.
        Also added is for each element the number of occurrences.
        '''
        if df.empty:
            lis = []
        else:
            s = ','.join(df[colStr].tolist()) #create comma-sepeated string
            LIS = s.split(',') #split at commas, list of all keywords
            lis = list(set(LIS)) #make items unique

        return sorted(lis) #return sorted list

    def df_compareWithList(self, df, colStr, lis):
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

    def update_isSel(self,lis):
        '''
        Updates the isSel field in the dict colStr (kurzel, topics, ...).
        List contains a list of colStr elements.
        lis can be empty [], in which case nothing is done.
        If lis is not empty, it always starts with the column name colStr, e.g.
        ['topic','BiT','WiD']
        In case of ['topic'], the last checkmark was unchecked, so set all values to False.
        '''
        if len(lis)>0:
            colStr = lis.pop(0) #colStr is column name in df
            self.FROMWHOM = colStr #update who triggered event
            if len(lis)>0:
                if colStr == 'kurzel':
                    self.kurzel['isSel'] = self.find_isSel(lis, self.kurzel['label'])
                elif colStr == 'topic':
                    self.topic['isSel'] = self.find_isSel(lis, self.topic['label'])
                elif colStr == 'basal':
                    self.basal['isSel'] = self.find_isSel(lis, self.basal['label'])
                elif colStr == 'diff':
                    self.diff['isSel'] = self.find_isSel(lis, self.diff['label'])
                elif colStr == 'imSize':
                    self.imSize['isSel'] = self.find_isSel(lis, self.imSize['label'])
                elif colStr == 'displayMode':
                    self.displayMode['isSel'] = self.find_isSel(lis, self.displayMode['label'])
                elif colStr == 'sortMode':
                    self.sortMode['isSel'] = self.find_isSel(lis, self.sortMode['label'])


            else:
                if colStr == 'kurzel':
                    self.kurzel['isSel'] = [False for item in self.kurzel['label']]
                elif colStr == 'topic':
                    self.topic['isSel'] = [False for item in self.topic['label']]
                elif colStr == 'basal':
                    self.basal['isSel'] = [False for item in self.basal['label']]
                elif colStr == 'diff':
                    self.diff['isSel'] = [False for item in self.diff['label']]

    def find_isSel(self,lis,LIS):
        A = [False for item in LIS]
        for item in lis:
                A[LIS.index(item)] = True

        return A

    def update_filterList(self):
        '''
        Creates a list of all labels in 'labels' which a truth-value given in 'isSel'
        Filterlists are empty if 'isSel' contains only False.
        '''
        R = self.kurzel['isSel']
        self.kurzel['filterList'] = [ self.kurzel['label'][i] for i in range(0,len(R)) if R[i]==True ]
        R = self.topic['isSel']
        self.topic['filterList'] = [ self.topic['label'][i] for i in range(0,len(R)) if R[i]==True ]
        R = self.basal['isSel']
        self.basal['filterList'] = [ self.basal['label'][i] for i in range(0,len(R)) if R[i]==True ]
        R = self.diff['isSel']
        self.diff['filterList'] = [ self.diff['label'][i] for i in range(0,len(R)) if R[i]==True ]
        R = self.imSize['isSel']
        self.imSize['filterList'] = [ self.imSize['label'][i] for i in range(0,len(R)) if R[i]==True ]
        R = self.displayMode['isSel']
        self.displayMode['filterList'] = [ self.displayMode['label'][i] for i in range(0,len(R)) if R[i]==True ]
        R = self.sortMode['isSel']
        self.sortMode['filterList'] = [ self.sortMode['label'][i] for i in range(0,len(R)) if R[i]==True ]


    def update_num(self,df):
        '''
        Updates all num fields in the dict based on (a filtered) df.
        If df is empty, the returned values are 0.
        '''
        self.kurzel['num'] = self.df_compareWithList( df, 'kurzel', self.kurzel['label'] )
        self.topic['num'] = self.df_compareWithList( df, 'topic', self.topic['label'] )
        self.basal['num'] = self.df_compareWithList( df, 'basal', self.basal['label'] )
        self.diff['num'] = self.df_compareWithList( df, 'diff', self.diff['label'] )

    def update_pics(self,df):
        '''
        Updates the paths to the pictures based on (a filtered) df.
        If df is empty, empty lists are returned.
        '''

        if ~df.empty:
            self.qpics = df['qImage_path'].to_list()
            self.apics = df['aImage_path'].to_list()
        else:
            self.qpics = []
            self.apics = []
