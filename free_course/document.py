
# s = 'Это строка. \
# Это строка продолжается.'  # \ - Для продолжения строки
# print(s) #Это строка. Это строка продолжается. 


# -*- coding: utf-8 -*-

# simple_string = 'Spam'
# len(simple_string)
# # 4
# simple_string[0]
# # 'S'
# simple_string[1]
# # 'p'


def user_numbers(num):
    if num < 0:
        return 'Положительное число'
    elif num > 0:
        return 'Отрицательное число'
    else:
        return 'Ноль'

user_numbers(1)
