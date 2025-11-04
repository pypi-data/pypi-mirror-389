#coding=utf-8
try:
    import jieba
    import pandas as pd
    import collections
    import time
    import sys
except ModuleNotFoundError as err:
    print("你还没有安装程序所依赖的包，请输入以下命令安装:pip install {0} ".format(err.name))

else:
    def count_words():
        """
        词语词频统计
        :param file:需要统计的文件地址
        :param sheet：需要统计的文件的sheet
        :param title：需要统计的列的名字
        :param wordlength：需要统计的词的长度
        :return: wordsres 词以及出现的频次
        """
        # 用户依次输入相关值
        print("*****注意事项：所有计算仅在你的电脑上进行，输入的信息不会有任何其他人获取******")
        time.sleep(2)
        print("请输入你要处理的excel文件(.xlsx)的地址")
        file =input()
        print("请输入要处理的内容在第几个sheet")
        sheet = int(input())-1
        print("请输入要处理的列的名字")
        title =input()
        print("请输入需要统计的词的长度，输入0等于不区分长度")
        wordlength = int(input())


        # 读取文件内容
        data=pd.read_excel(file,sheet_name=sheet).astype(str)
        
        # 切出词语
        data['cut_word'] =data[title].apply(jieba.lcut,cut_all=True)
        
        res=list()
        for i in data['cut_word']:
                    res=res+i
        words_num=collections.Counter(res)
        if wordlength==0:
                    needwords={k:v for k,v in words_num.items()}
        else:
                    needwords={k:v for k,v in words_num.items() if len(k)==wordlength}
        wordsres=sorted(needwords.items(),key = lambda x:x[1],reverse = True)       
        return wordsres
        
    def xsd(text1,text2):
        """
         比较两个句子的相似度
         :param text1: 文本1
         :param text2: 文本2
         :return: 他们的相似度
        """
        #集合必须满足互斥性，所以去重
        text1=set(text1)
        text2=set(text2)
        sml=(len(text1&text2))/(len(text1|text2))
        print("两个句子的相似度为:{0}".format(sml))