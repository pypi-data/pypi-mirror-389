import numpy as np
def r_square_xy(x,y):
    # function 1 
    # r_square 用于输出k, b, r^2
    """
Calculate the correlation coefficient (R²) of the regression line
for arrays x and y.

Formula:
    R² = SSR / SST = 1 - SSE / SST
where:
    SSR — Regression Sum of Squares
    SST — Total Sum of Squares
    SSE — Error Sum of Squares

The regression line is expressed as:
    ŷ = k * x + b

Returns
-------
k : float
    Slope of the regression line.
b : float
    Intercept of the regression line.
r2 : float
    Coefficient of determination (R²).
"""
    x = np.array(x)
    y = np.array(y)
    k,b  = np.polyfit(x, y, deg = 1)    # 一阶线性拟合
    y_hat = k * np.array(x) + b
    y_bar = sum(y) / len(y)
    ss_residual = np.sum((y - y_hat) ** 2)    # 总平方和
    ss_total = np.sum((y - y_bar) ** 2) # 残差平方和
    r_2 = 1 - ss_residual / ss_total
    return k, b, r_2

class KineticAnalysis():
    """
A class for performing kinetic analysis.

Parameters
----------
alpha_list : list of float
    Conversion degrees, e.g. [α1, α2, α3, ...].

data_objects : list of DataList
    Each DataList contains corresponding temperature, heating rate, 
    and dα/dT data for a given experimental condition.

Details
-------
temperature : list of tuple(float)
    Temperature datasets for each heating rate, e.g. 
    [(T11, T12, T13, ... T1n), (T21, T22, T23, ... T2n), ...].

beta : list of float
    Heating rate list, e.g. [b1, b2, b3, ..., bn].

dadT : list of tuple(float)
    dα/dT datasets corresponding to temperature, e.g. 
    [(dadT11, dadT12, dadT13, ... dadT1n), 
     (dadT21, dadT22, dadT23, ... dadT2n), ...].
"""
    #class3 热动力学分析        
    # 数据结构：alpha = [a1,a2,a3],     
    # temperatrue = [(T11, T12, T13),(T21, T22, T23),(T31, T32, T33)] 
    # beta = [(b11, b12, b13),(b21, b22, b23),(b31, b32, b33)]
    # dadT = for friedman method only
    # 温度，升温速率和dadT是通过class DataList生成的小列表再热分析中嵌入大列表
    R = 8.314 # gas constant 8.314 J/mol·K
    def __init__(self, alpha_list, data_objects):
        self.alpha_list = list(alpha_list)
        self.objects_data = list(data_objects)
    
    def fwo_ea(self, return_data = False):
        self.results = {}   # 计算的结果为一个字典
        self.raw_data = {}
        #ln(beta) = const - 1.052*Ea/RT
        for alpha, data in zip(self.alpha_list,self.objects_data):
            log_beta = [np.log(beta) for beta in data.beta]
            data_temp = [1 / temp for temp in data.temperature]
            k, b, r2 = r_square_xy(data_temp,log_beta)
            ea = - self.R / 1000 * k / 1.052
            self.results[alpha] = {'Ea = ': ea,
                            'k = ': k,
                            'b = ': b,
                            'r^2 = ': r2}
            # e.g., results(0.1: {'Ea = ': 114.514,'k = ': 1919, 'b = ': 810, 'r^2 = ': 0.9527})
            # e.g., unit of Ea is kJ/mol
            self.raw_data[alpha] = {
               'x': [float(temp) for temp in data_temp],
                'y': [float(beta) for beta in log_beta]
                }
        if return_data:
            return self.results, self.raw_data
        else:
            return self.results
    
    def kas_ea(self, return_data = False):
        self.results = {}   # 计算的结果为一个字典
        self.raw_data = {}
        for alpha, data in zip(self.alpha_list,self.objects_data):
            log_beta = [np.log(beta / temp ** 2) for beta, temp\
                         in zip(data.beta, data.temperature)]
            data_temp = [1 / temp for temp in data.temperature]
            k, b, r2 = r_square_xy(data_temp,log_beta)
            ea = - self.R / 1000 * k
            self.results[alpha] = {'Ea = ': ea,
                            'k = ': k,
                            'b = ': b,
                            'r^2 = ': r2}
            # e.g., results(0.2: {'Ea = ': 114.514,'k = ': 1919, 'b = ': 810, 'r^2 = ': 0.9527})
            # e.g., unit of Ea is kJ/mol
            self.raw_data[alpha] = {
               'x': [float(temp) for temp in data_temp],
                'y': [float(beta) for beta in log_beta]
                }
        if return_data:
            return self.results, self.raw_data
        else:
            return self.results
    
    def starink_ea(self, return_data = False):
        self.results = {}   # 计算的结果为一个字典
        self.raw_data = {}
        for alpha, data in zip(self.alpha_list, self.objects_data):
            log_beta = [np.log(beta / temperature ** 1.92 ) for beta, temperature \
                         in zip(data.beta,data.temperature)]
            data_temp = [1 / temp for temp in data.temperature]
            k, b, r2 = r_square_xy(data_temp,log_beta)
            ea = - self.R / 1000 * k / 1.0008
            self.results[alpha] = {'Ea = ': ea,
                            'k = ': k,
                            'b = ': b,
                            'r^2 = ': r2}
            self.raw_data[alpha] = {
            'x': [float(temp) for temp in data_temp],
            'y': [float(beta) for beta in log_beta]
            }
        if return_data:
            return self.results, self.raw_data
        else:
            return self.results
    
    def friedman_ea(self, return_data = False):
        self.results = {}   # 计算的结果为一个字典
        self.raw_data = {}
        for alpha, data in zip(self.alpha_list, self.objects_data):
            log_beta = [np.log(beta * dadT) for beta, dadT \
                         in zip(data.beta, data.dadT)]
            data_temp = [1 / temp for temp in data.temperature]
            k, b, r2 = r_square_xy(data_temp, log_beta)
            ea = - self.R / 1000 * k
            self.results[alpha] = {'Ea = ': ea,
                            'k = ': k,
                            'b = ': b,
                            'r^2 = ': r2}
            # e.g., results(0.7 :{'Ea = ': 114.514,'k = ': 1919, 'b = ': 810, 'r^2 = ': 0.9527})
            # e.g., unit of Ea is kJ/mol
            self.raw_data[alpha] = {
            'x': [float(temp) for temp in data_temp],
            'y': [float(beta) for beta in log_beta]
            }
        if return_data:
            return self.results, self.raw_data
        else:
            return self.results