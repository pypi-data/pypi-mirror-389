def find(n_term, first_term, common_difference):
   x = n_term - 1
   y = x * common_difference
   z = first_term + y
   
   return z
   
def find_sum(n_term, first_term, common_difference):
    devide = n_term / 2
    v = first_term * 2
    w = n_term - 1
    x = w * common_difference
    y = v + x
    z = devide * y
    
    return z