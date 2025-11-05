class Trigdeg:
  pi = 3.141592653589793
  def __init__(self):
    pass

  @staticmethod
  def deg_to_radian(degree):
    radian = degree * Trigdeg.pi/180
    return radian


  @staticmethod
  def factorial(n):
    product = 1
    if n == 0:
      return 1
    else:
      for i in range(1,n+1):
        product *=i
      return product

  @staticmethod
  def power(base,exponent):        
    power_result = 1
    for i in range(exponent):
      power_result *= base
    return power_result


  @staticmethod
  def sin_deg(degree_angle):
    sin_radian = Trigdeg.deg_to_radian(degree_angle)
    result = 0
    for term_index in range(15):
      exponent = 2*term_index+1
      term_value = Trigdeg.power(sin_radian,exponent)/Trigdeg.factorial(exponent)
      if term_index%2!=0:
        term_value = -term_value
      result += term_value
    result = round(result,6)
    return result

  @staticmethod
  def cos_deg(degree_angle):
    cos_radian = Trigdeg.deg_to_radian(degree_angle)
    result = 0
    for term_index in range(15):
      exponent = 2*term_index
      term_value = Trigdeg.power(cos_radian,exponent)/Trigdeg.factorial(exponent)
      if term_index %2 !=0:
        term_value = -term_value
      result+=term_value
    result = round(result,6)
    return result

  @staticmethod
  def tan_deg(degree_angle):
    tan_radian = Trigdeg.deg_to_radian(degree_angle)
    if Trigdeg.cos_deg(degree_angle) == 0:
      return "Undefined"
    result = Trigdeg.sin_deg(degree_angle)/Trigdeg.cos_deg(degree_angle)
    result = round(result,6)
    return result

  @staticmethod
  def cot_deg(degree_angle):
    cot_radian = Trigdeg.deg_to_radian(degree_angle)
    if Trigdeg.sin_deg(degree_angle) == 0:
      return "Undefined"
    result = Trigdeg.cos_deg(degree_angle)/Trigdeg.sin_deg(degree_angle)
    result = round(result,6)
    return result
  
  @staticmethod
  def sec_deg(degree_angle):
    sec_radian = Trigdeg.deg_to_radian(degree_angle)
    if Trigdeg.cos_deg(degree_angle) == 0:
      return "Undefined"
    result = 1/Trigdeg.cos_deg(degree_angle)
    result = round(result,6)
    return result

  @staticmethod
  def cosec_deg(degree_angle):
    cosec_radian = Trigdeg.deg_to_radian(degree_angle)
    if Trigdeg.sin_deg(degree_angle) == 0:
      return "Undefined"
    result = 1/Trigdeg.sin_deg(degree_angle)
    result = round(result,6)
    return result

