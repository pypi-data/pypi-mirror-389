#coding=utf-8
try:
    import numpy as np
    import pandas as pd
    import time
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeRegressor
    from xgboost import XGBRegressor
except ModuleNotFoundError as err:
    print("你还没有安装程序所依赖的包，请输入以下命令安装:pip install {0}".format(err.name))
    
else:
    def lr_one_hot():
        #数据准备
        print('①请按照下面的格式，准备您的excel数据,格式要求见文档https://shimo.im/sheets/hPdQxXWCwP3chpDk/MODOC/')
        print("②输入你准备好的excel数据的地址，比如：/Users/xxx/Desktop/test1.xlsx")
        time.sleep(1)
        #获取数据
        print('请输入')
        file=str(input())
        data=pd.read_excel(file)
        #判断一下读取是否成功 todo
        #拆解编码
        labelList=data.iloc[:,-1]
        featurelist=pd.get_dummies(data.iloc[:,0:-1])
        
        #建模
        lr = LogisticRegression() 
        #训练
        lr.fit(featurelist, labelList) 
        
        #输出结果
        features=list(featurelist.head(0))
        importance=list(lr.coef_[0])
        print('数据录入成本，分析结果如下')
        res=pd.DataFrame({'特征':features,'重要程度':importance})
        res=res.sort_values(by='重要程度',ascending=False)
        return res
    
    def lr_factorize():
        #数据准备
        print('①请按照下面的格式，准备您的excel数据,格式要求见文档https://shimo.im/sheets/hPdQxXWCwP3chpDk/MODOC/')
        print("②输入你准备好的excel数据的地址，比如：/Users/xxx/Desktop/test1.xlsx")
        time.sleep(1)
        #获取数据
        print('请输入')
        file=str(input())
        data=pd.read_excel(file)
        #判断一下读取是否成功 todo
        #拆解编码
        #数据准备
        for i in data.columns.values[:-1]:
            if data[i].dtype != 'int64':
                data[i]=pd.factorize(data[i])[0]
        
        labelList=data.iloc[:,-1]
        featurelist=data.iloc[:,0:-1]
        
        #建模训练
        lr = LogisticRegression() 
        lr.fit(featurelist, labelList) 
        
        #输出结果
        features=list(featurelist.head(0))
        importance=list(lr.coef_[0])
        print('数据录入成本，分析结果如下')
        res=pd.DataFrame({'特征':features,'重要程度':importance})
        res=res.sort_values(by='重要程度',ascending=False)
        return res    
    
    
    
    
    
    def Tree_one_hot():
        #数据准备
        print('①请按照下面的格式，准备您的excel数据,格式要求见文档https://shimo.im/sheets/hPdQxXWCwP3chpDk/MODOC/')
        print("②输入你准备好的excel数据的地址，比如：/Users/xxx/Desktop/test1.xlsx")
        time.sleep(1)
        #获取数据
        print('请输入')
        file=str(input())
        data=pd.read_excel(file)
        #判断一下读取是否成功 todo
        #拆解编码
        labelList=data.iloc[:,-1]
        featurelist=pd.get_dummies(data.iloc[:,0:-1])
        
        #建模训练
        Tree = DecisionTreeRegressor(max_depth=5)
        Tree.fit(featurelist, labelList)

        features=list(featurelist.head(0))
        importance=Tree.feature_importances_

        res=pd.DataFrame({'特征':features,'重要程度':importance})
        res=res.sort_values(by='重要程度',ascending=False)

        return res
    def Tree_factorize():
        #数据准备
        print('①请按照下面的格式，准备您的excel数据,格式要求见文档https://shimo.im/sheets/hPdQxXWCwP3chpDk/MODOC/')
        print("②输入你准备好的excel数据的地址，比如：/Users/xxx/Desktop/test1.xlsx")
        time.sleep(1)
        #获取数据
        print('请输入')
        file=str(input())
        data=pd.read_excel(file)
        #判断一下读取是否成功 todo
        #拆解编码
        for i in data.columns.values[:-1]:
            if data[i].dtype != 'int64':
                data[i]=pd.factorize(data[i])[0]
        
        labelList=data.iloc[:,-1]
        featurelist=data.iloc[:,0:-1]
        #建模训练
        Tree = DecisionTreeRegressor(max_depth=5)
        Tree.fit(featurelist, labelList)

        features=list(featurelist.head(0))
        importance=Tree.feature_importances_

        res=pd.DataFrame({'特征':features,'重要程度':importance})
        res=res.sort_values(by='重要程度',ascending=False)
        return res
    
    
    def xgb_one_hot():
        #数据准备
        print('①请按照下面的格式，准备您的excel数据,格式要求见文档https://shimo.im/sheets/hPdQxXWCwP3chpDk/MODOC/')
        print("②输入你准备好的excel数据的地址，比如：/Users/xxx/Desktop/test1.xlsx")
        time.sleep(1)
        #获取数据
        print('请输入')
        file=str(input())
        data=pd.read_excel(file)
        #判断一下读取是否成功 todo

        #拆解编码
        labelList=data.iloc[:,-1]
        featurelist=pd.get_dummies(data.iloc[:,0:-1])
        #建模训练
        xgb =XGBRegressor()
        xgb.fit(featurelist, labelList)

        features=list(featurelist.head(0))
        importance=xgb.feature_importances_

        res=pd.DataFrame({'特征':features,'重要程度':importance})
        res=res.sort_values(by='重要程度',ascending=False)

        return res
    
    def xgb_factorize():
        #数据准备
        print('①请按照下面的格式，准备您的excel数据,格式要求见文档https://shimo.im/sheets/hPdQxXWCwP3chpDk/MODOC/')
        print("②输入你准备好的excel数据的地址，比如：/Users/xxx/Desktop/test1.xlsx")
        time.sleep(1)
        #获取数据
        print('请输入')
        file=str(input())
        data=pd.read_excel(file)
        #判断一下读取是否成功 todo
        #数据准备
        for i in data.columns.values[:-1]:
            if data[i].dtype != 'int64':
                data[i]=pd.factorize(data[i])[0]
        
        labelList=data.iloc[:,-1]
        featurelist=data.iloc[:,0:-1]
        #建模训练
        xgb =XGBRegressor()
        xgb.fit(featurelist, labelList)

        features=list(featurelist.head(0))
        importance=xgb.feature_importances_

        res=pd.DataFrame({'特征':features,'重要程度':importance})
        res=res.sort_values(by='重要程度',ascending=False)
        return res