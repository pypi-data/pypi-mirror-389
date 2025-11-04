#coding=utf-8
try:
    import numpy as np
    import time
    from scipy import stats
    from math import sqrt
    from statsmodels.stats.power import NormalIndPower

except ModuleNotFoundError as err:
    print("你还没有安装程序所依赖的包，请输入以下命令安装:pip install {0} ".format(err.name))
    
else:

    def ipr(old_num,new_num):
        """
        提升量计算
        :param old_num: 对比数据
        :param new_num: 新数据
        :return: 提升的绝对值，相对值
        """
        print ('{0} 相比{1}:  提升绝对值{2},  相对值{3}%'.format(new_num,old_num,round((new_num-old_num),2),round((new_num-old_num)/old_num*100,2)))

    #AB样本量计算ABSample
    def ABSample():
        """
        AB实验样本量计算
        :param target: 目标指标
        :param promote: 提升相对值
        :return: 实验组单个组所需要的人数
        """
        print("请输入实验主要指标当前值 __ （点击率，留存率等，小数，比如 0.31)")
        target=float(input())
        print("请输入最小可以观测的提升比例__ （提升的最少相对值，小数，比如 0.01)")
        promote=abs(float(input()))
        zpower = NormalIndPower()
        effect_size =target*promote/np.sqrt(target*(1-target))
        res=(zpower.solve_power(
           effect_size=effect_size,
           nobs1=None,
           alpha=0.05,
           power=0.8,
           ratio=1.0,
           alternative='two-sided'
                ))
        print("\n计算中……,计算结果如下:")
        time.sleep(3)
        print('******* 您的AB实验，"实验组"需要的用户量为：{0}人 ******'.format(int(res)))
        
    def rank_wilson_score(pos, total, p_z=1.96):
        """
        威尔逊得分计算
        :param pos: 正例数
        :param total: 总数
        :param p_z: 正太分布的分位数
        :return: 威尔逊得分
        """
        pos_rat = pos/ total  # 正例比率
        score = (pos_rat + (np.square(p_z) / (2* total)) - ((p_z / (2* total)) * np.sqrt(4 * total * (1 - pos_rat) * pos_rat + np.square(p_z)))) / \
        (1 + np.square(p_z) / total)
        return score
            
    #二项分布置信度计算
    def confidence():
        """
        实验置信度计算
        #分布类型
        :param distribution_type:z or t 分布类型，支持比例Z检验和两样本t检验
        
        #都需要的参数
        :param n_shiyan: 实验组人数
        :param n_duizhao: 对照组人数
        
        #比例Z检验情况下
        :param p_shiyan: 实验组概率
        :param p_duizhao: 对照组概率
        
        #两样本t检验
        :param s_shiyan: 实验组标准差
        :param s_duizhao: 对照组标准差
        :param m_shiyan: 实验组均值
        :param m_duizhao: 对照组均值
        :return: 置信度
        """
        while True:
            #获取相关信息
            print("二项分布（比如点击率）：请输入1，其他情况：输入2，退出：输入3")
            print("（专业解释：比例Z检验选1，两样本t检验选2）")
            distribution_type=int(input())
            if distribution_type==1:
                print("请输入实验组人数")
                n_shiyan=int(input())
                print("请输入对照组组人数")
                n_duizhao=int(input())
                print("请输入实验组二项分布事件发生的概率")
                p_shiyan=float(input())
                print("请输入对照组二项分布事件发生的概率")
                p_duizhao=float(input())
                #计算z-soce,二项分布
                fenzi=p_shiyan-p_duizhao
                fenmu=((p_shiyan*(1-p_shiyan)/n_shiyan)+(p_duizhao*(1-p_duizhao)/n_duizhao))**0.5
                Confidence_interval_top=(p_shiyan-p_duizhao)+1.96*fenmu
                Confidence_interval_down=(p_shiyan-p_duizhao)-1.96*fenmu
                z_score=abs((p_shiyan-p_duizhao)/fenmu)

                #计算相对和绝对涨幅
                absoluteIncrease= "{:.2%}".format((p_shiyan-p_duizhao))
                relativeIncrease="{:.2%}".format(((p_shiyan-p_duizhao)/p_duizhao))
                #根据z-score计算P值
                if z_score<1.96:
                    result='不显著'   
                if 1.96 <= z_score<2.58:
                    result='一般显著'
                if 2.58<=z_score:
                    result='非常显著'

                print("-------\n实验结果:{0},\n绝对涨幅:{3},相对涨幅：{4},\n置信区间为:[{1},{2}]".format(result,Confidence_interval_down,Confidence_interval_top,absoluteIncrease,relativeIncrease))
                break
            elif distribution_type==2:
                print("请输入实验组人数")
                n_shiyan=int(input())
                print("请输入对照组组人数")
                n_duizhao=int(input())
                print("请输入实验组标准差")
                s_shiyan=float(input())
                print("请输入对照组标准差")
                s_duizhao=float(input())
                print("请输入实验组均值")
                m_shiyan=float(input())
                print("请输入对照组均值")
                m_duizhao=float(input())

                #计算两个组的标准误差
                se_shiyan = s_shiyan / (n_shiyan ** 0.5)
                se_duizhao = s_duizhao / (n_duizhao ** 0.5)
                se_diff = (se_shiyan ** 2 + se_duizhao ** 2) ** 0.5
                # t检验
                t_stat = (m_shiyan - m_duizhao) / se_diff
                # p值
                df = n_shiyan + n_duizhao - 2 #自由度
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=df))
                
                #判断是否显著
                if p_value > 0.05:
                    result = "不显著"
                elif p_value <= 0.05 and p_value > 0.01:
                    result = "一般显著"
                else:  # p_value <= 0.01
                    result = "非常显著"
                    
                # 计算 t-值的临界值，对应于 95% 的置信区间
                alpha = 0.05 # 对于 95% 的置信区间，α = 0.05
                t_critical = stats.t.ppf(1 - alpha/2, df) # 两侧检验，所以 α/2

                # 计算置信区间
                Confidence_interval_down = (m_shiyan - m_duizhao) - t_critical * se_diff
                Confidence_interval_top = (m_shiyan - m_duizhao) + t_critical * se_diff
                
                #计算相对和绝对涨幅
                absoluteIncrease= "{:.2%}".format((m_shiyan-m_duizhao))
                relativeIncrease="{:.2%}".format(((m_shiyan-m_duizhao)/m_duizhao))
                print("-------\n实验结果:{0},\n绝对涨幅:{3},相对涨幅：{4},\n置信区间为:[{1},{2}]".format(result,Confidence_interval_down,Confidence_interval_top,absoluteIncrease,relativeIncrease))
                break
            elif distribution_type==3:
                break
            else:
                 print("输入错误，请输入： 1或者2或者3")