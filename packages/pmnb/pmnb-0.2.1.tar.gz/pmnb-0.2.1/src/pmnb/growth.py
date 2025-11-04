#coding=utf-8
try:
    import sys
    from prettytable import PrettyTable
    import time
    from matplotlib import pyplot as plt
except ModuleNotFoundError as err:
    print("你还没有安装程序所依赖的包，请输入以下命令安装:pip install {0} ".format(err.name))
    
else:
    def DAU():
        """
        DAU预测
        :param dayx_retation: 第X天用户留存
        :param DNU: 每日新增用户数
        :param Days:天数
        :return: 第X天后的DAU，留存曲线预测
        """
        # 用户依次输入相关值
        print("*****注意事项：所有计算仅在你的电脑上进行，输入的信息不会有任何其他人获取******")
        time.sleep(2)
        print("请输入App的次日留存：_____(小数，比如 0.31)")
        day1_retation = float(input())
        print("请输入App的7日留存：_____(小数，比如 0.20)")
        day7_retation = float(input())
        print("请输入App的15日留存：_____(小数，比如 0.15)")
        day15_retation = float(input())
        print("请输入App的30日留存：_____(小数，比如 0.13)")
        day30_retation = float(input())
        print("请输入App的每日新增用户数：_____")
        DNU = int(input())
        print("请输入预测的时间，多少天以后的DAU：_____")
        Days = int(input())
        print("计算中……,计算结果如下")

        # 求留存函数 x/(a+y)+z
        y = round((90 * (day1_retation - day15_retation) - 98 * (day1_retation - day7_retation)) / (
                    14 * (day1_retation - day7_retation) - 6 * (day1_retation - day15_retation)), 2)
        x = round(((day1_retation - day15_retation) * (1 + y) * (15 + y)) / 14, 2)
        z = round((day1_retation - (x / (1 + y))), 2)

        # 计算LT
        ret = [1]
        if Days == 1:
            LT = 1
        else:
            LT = 1
            for i in range(1, Days + 1):
                re_pr = round((x / (i + y) + z), 3)
                if re_pr <= 0:
                    re_pr = 0
                ret.append(re_pr)
                LT = LT + re_pr
        # 画图
        time.sleep(3)
        td = [i for i in range(0, Days + 1)]
        plt.title('DAY_retation_predict')
        plt.plot(td, ret, color='blue')

        #校验DAY30
        re30_pre = (x / (30 + y) + z)
        if re30_pre <= 0:
            re30_pre = 0
        diff30 = day30_retation - re30_pre
        if abs(diff30) > 0.5:
            print('预测30日留存{0},实际30日留存{1},误差过大，无法预估DAU'.format(re30_pre, day30_retation))
            return ("模型无法预测，请联系作者")
        else:
            # 计算预估的DAU
            DAU_res = int((round(LT, 1)) * DNU)

            predict_title = "预测的第" + str(Days) + "天时DAU（一般偏高一点）"
            table = PrettyTable(['每日新增数DNU', '次日留存', '7日留存', '15日留存', '30日留存', '时间天数', 'LT', predict_title])
            table.add_row([DNU, day1_retation, day7_retation, day15_retation, day30_retation, Days, round(LT, 2), DAU_res])

            return table