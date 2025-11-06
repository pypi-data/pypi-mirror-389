import pytest
from thermohi_hikari.datalistio import DataList
from thermohi_hikari.thermoanalysis import KineticAnalysis, r_square_xy
from thermohi_hikari.plotting import FittingPlot


# 验证温度转换功能
def test_cel_to_kelvin():
    data = DataList(temperature = [0, 100], beta = [5, 10],dadT = [0.01, 0.02],unit= 'c')
    assert pytest.approx(data.temperature) == [273.15, 373.15]

def test_fahrenheit_to_kelvin():
    data = DataList(temperature = [32, 212], beta = [5, 10],dadT = [0.01, 0.02],unit= 'f')
    assert pytest.approx(data.temperature) == [273.15, 373.15]

def test_kelvin_directly():
    data = DataList(temperature = [273.15, 373.15], beta = [5, 10],dadT = [0.01, 0.02],unit= 'k')
    assert pytest.approx(data.temperature) == [273.15, 373.15]

def test_invalid_unit_raises():
    with pytest.raises(ValueError):
        DataList(
            temperature=[100, 200],
            beta=[10, 20],
            dadT=[0.1, 0.2],
            unit="xyz"
        )
# 验证r^2计算程序
def test_r_square():
    x = [1, 2, 3, 4, 5]
    y_true = [2, 4, 6, 8, 10]
    y_pred1 = [2.2, 3.8, 6.1, 7.9, 10.2]
    y_pred2 = [3, 5, 5, 9, 7]
     # 完美线性
    k, b, r2 = r_square_xy(x, y_true)
    assert k == pytest.approx(2.0)
    assert b == pytest.approx(0.0)
    assert r2 == pytest.approx(1.0)

    # 轻微偏差
    k, b, r2 = r_square_xy(x, y_pred1)
    assert k == pytest.approx(2.01, rel=1e-2)
    assert b == pytest.approx(0.01, rel=1e-2)
    assert r2 == pytest.approx(0.9968, rel=1e-3)

    # 偏差较大
    k, b, r2 = r_square_xy(x, y_pred2)
    assert k == pytest.approx(1.2, rel=1e-1)
    assert b == pytest.approx(2.2, rel=1e-1)
    assert r2 == pytest.approx(0.6923, rel=1e-2)

# 测试活化能：
alpha = [0.1, 0.5, 0.9]
data_object = [DataList([241.9, 251.85, 263.5, 270.9], [5,10,20,30], 
                        [0.00366, 0.00358, 0.00353, 0.00348], unit='c'),
               DataList([291.25, 302.3, 314.3, 322.45], [5,10,20,30], 
                        [0.01318, 0.01297, 0.01292, 0.01274], unit='c'),
               DataList([321.9, 333.55, 345.6, 354.2], [5,10,20,30],
                        [0.00942, 0.00927, 0.00925, 0.00914], unit='c')]
def test_fwo():
    analysis = KineticAnalysis(alpha, data_object)
    result = analysis.fwo_ea(return_data = False)
    a, b, c= [result[i].get('Ea = ') for i in alpha] 
    assert a == pytest.approx(136.5535)
    assert b == pytest.approx(153.1332)
    assert c == pytest.approx(164.8637)

def test_kas():
    analysis = KineticAnalysis(alpha, data_object)
    result = analysis.kas_ea(return_data = False)
    a, b, c= [result[i].get('Ea = ') for i in alpha] 
    assert a == pytest.approx(134.8546)
    assert b == pytest.approx(151.4584)
    assert c == pytest.approx(163.2806)

def test_starink():
    analysis = KineticAnalysis(alpha, data_object)
    result = analysis.starink_ea(return_data = False)
    a, b, c= [result[i].get('Ea = ') for i in alpha] 
    assert a == pytest.approx(135.0985)
    assert b == pytest.approx(151.7226)
    assert c == pytest.approx(163.5560)

def test_friedman():
    analysis = KineticAnalysis(alpha, data_object)
    result = analysis.friedman_ea(return_data = False)
    a, b, c= [result[i].get('Ea = ') for i in alpha] 
    assert a == pytest.approx(139.7619)
    assert b == pytest.approx(158.3342)
    assert c == pytest.approx(170.8158)
