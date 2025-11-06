class DataList:
    #class 2 数据列表化，将单一的温度，升温速率和dadT生成列表
    def __init__(self,temperature, beta, dadT, unit = "c"):
        """
A class for storing thermal analysis data at a specific conversion level (α).

Parameters
----------
temperature : list[float]
    Temperature list corresponding to each heating rate point.
beta : list[float]
    Heating rate list (β), typically in K/min.
dadt : list[float]
    Reaction rate list (dα/dt), corresponding to the same temperatures.
unit : str, optional    
    Temperature unit indicator:
        - 'c' : data collected in Celsius
        - 'f' : data collected in Fahrenheit
        - 'k' : data already in Kelvin
    Default is 'c'.
    
Notes
-----
If the temperature is in Celsius or Fahrenheit, it will be converted to Kelvin automatically.
"""
        self.temperature = list(temperature)    # 对应温度列表
        if unit is not None and unit.lower() == "c":
            self.temperature= [ t + 273.15 for t in self.temperature]
        if unit is not None and unit.lower() == "f":
            self.temperature= [ (t - 32) / 1.8 + 273.15 for t in self.temperature]
        elif unit not in (None, "c", "C", "k", "K",'f','F'):
            raise ValueError("unit 参数只能是 'c' 或 'k'")
        self.beta = list(beta)  #对应升温速率列表
        self.dadT = list(dadT)  #对应da/dT列表
