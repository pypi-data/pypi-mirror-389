import numpy as np
import matplotlib.pyplot as plt   
from .thermoanalysis import KineticAnalysis
class FittingPlot:
    """
A class for plotting scatter data and fitted regression curves 
based on kinetic analysis results.
﻿
Parameters
----------
alpha_list : list[float]
List of conversion fractions (α values).
data_objects : list[DataList]
List of `DataList` instances, each containing temperature, 
heating rate (β), and reaction rate (dα/dt) data for a specific α.
analysis : KineticAnalysis
An instance of `KineticAnalysis` used to perform the fitting 
and provide the regression results.
"""
    def __init__(self, alpha_list, data_objects, analysis: KineticAnalysis):
        self.alpha_list = list(alpha_list)
        self.objects_data = list(data_objects)
        self.analysis = analysis
    
    def fwoplot(self):
        results = self.analysis.fwo_ea()
        xmin = []
        xmax = []
        figure = plt.figure(figsize= (8,6))
        axes = plt.subplot(1,1,1)
        plt.subplots_adjust(left=0.15, right=0.95, bottom=0.15, top=0.9)
        axes.set_xlabel("1/T",fontsize = 22, fontname = 'arial')
        axes.set_ylabel('ln(β)',fontsize = 22, fontname = 'arial')
        for data in self.objects_data:
            log_beta = [np.log(beta) for beta in data.beta]
            data_temp = [1 / temp for temp in data.temperature]
            xmin.append(np.min(data_temp))
            xmax.append(np.max(data_temp))
            axes.scatter(data_temp,log_beta)
            plt.draw()   # 刷新绘图
            plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        slope = [results[i].get('k = ') for i in results]
        intercept = [results[i].get('b = ') for i in results]
        for k, b, i, j  in zip(slope, intercept, xmin, xmax):
            x = np.linspace(i, j, 100)
            axes.plot(x, k * x + b)           
            plt.draw()   # 刷新绘图
            plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        plt.ioff()  # 关闭交互模式
        plt.show()

    def kasplot(self):
        results = self.analysis.kas_ea()
        xmin = []
        xmax = []
        figure = plt.figure(figsize= (8,6))
        axes = plt.subplot(1,1,1)
        axes.set_xlabel("1/T",fontsize = 22, fontname = 'arial')
        axes.set_ylabel('ln(β/T$^{2}$)',fontsize = 22, fontname = 'arial')
        plt.subplots_adjust(left=0.15, right=0.95, bottom=0.15, top=0.9)
        for data in self.objects_data:
            log_beta = [np.log(beta / temp ** 2) for beta, temp\
                         in zip(data.beta, data.temperature)]
            data_temp = [1 / temp for temp in data.temperature]
            xmin.append(np.min(data_temp))
            xmax.append(np.max(data_temp))
            axes.scatter(data_temp,log_beta)
        plt.draw()   # 刷新绘图
        plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        slope = [results[i].get('k = ') for i in results]
        intercept = [results[i].get('b = ') for i in results]
        for k, b, i, j  in zip(slope, intercept, xmin, xmax):
            x = np.linspace(i, j, 100)
            axes.plot(x, k * x + b)           
            plt.draw()   # 刷新绘图
            plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        plt.ioff()  # 关闭交互模式
        plt.show()
    
    def starinkplot(self):
        results = self.analysis.starink_ea()
        xmin = []
        xmax = []
        figure = plt.figure(figsize= (8,6))
        axes = plt.subplot(1,1,1)
        plt.subplots_adjust(left=0.15, right=0.95, bottom=0.15, top=0.9)
        axes.set_xlabel("1/T",fontsize = 22, fontname = 'arial')
        axes.set_ylabel('ln(β/T$^{1.92}$)',fontsize = 22, fontname = 'arial')
        for data in self.objects_data:
            log_beta = [np.log(beta / temp ** 1.92) for beta, temp\
                         in zip(data.beta, data.temperature)]
            data_temp = [1 / temp for temp in data.temperature]
            xmin.append(np.min(data_temp))
            xmax.append(np.max(data_temp))
            axes.scatter(data_temp,log_beta)
            plt.draw()   # 刷新绘图
            plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        slope = [results[i].get('k = ') for i in results]
        intercept = [results[i].get('b = ') for i in results]
        for k, b, i, j  in zip(slope, intercept, xmin, xmax):
            x = np.linspace(i, j, 100)
            axes.plot(x, k * x + b)           
            plt.draw()   # 刷新绘图
            plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        plt.ioff()  # 关闭交互模式
        plt.show()

    def friedmanplot(self):
        results = self.analysis.friedman_ea()
        xmin = []
        xmax = []
        figure = plt.figure(figsize= (8,6))
        axes = plt.subplot(1,1,1)
        plt.subplots_adjust(left=0.15, right=0.95, bottom=0.15, top=0.9)
        axes.set_xlabel("1/T",fontsize = 22, fontname = 'arial')
        axes.set_ylabel('ln(dα/dt)',fontsize = 22, fontname = 'arial')
        for data in self.objects_data:
            log_beta = [np.log(beta * dadT) for beta, dadT \
                         in zip(data.beta, data.dadT)]
            data_temp = [1 / temp for temp in data.temperature]
            xmin.append(np.min(data_temp))
            xmax.append(np.max(data_temp))
            axes.scatter(data_temp,log_beta)
            plt.draw()   # 刷新绘图
            plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        slope = [results[i].get('k = ') for i in results]
        intercept = [results[i].get('b = ') for i in results]
        for k, b, i, j  in zip(slope, intercept, xmin, xmax):
            x = np.linspace(i, j, 100)
            axes.plot(x, k * x + b)           
            plt.draw()   # 刷新绘图
            plt.pause(0.2)  # 暂停 0.3 秒，看清楚每条线
        plt.ioff()  # 关闭交互模式
        plt.show()