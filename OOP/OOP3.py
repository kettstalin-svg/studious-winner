
# class Employee:
#      def __init__(self, name, salary):
#         self.name = name
#         self.salary = salary
    
#      def work(self):
#         print(f'{self.name} работает')
    
    
    
# class TesterQA(Employee):
#     def work(self):
#         print(f'{self.name} тестирует код.')
    
# tester = TesterQA('pidor', '1488k')
# tester.work()


# class Developer(Employee):
#     def __init__(self, name, salary, lange: str):
#         super().__init__(name, salary)
#         self.lange = lange
    
#     def work(self):
#         print(f'{self.name} пишет код')
    
    
# class Designer(Employee):
#     def work(self):
#         print(f'{self.name} рисует интерфейсы')
    
    

# developer = Developer('Kira', 19, 'Python')
# developer.work()

# designer = Designer('IUDA', 30)
# designer.work()

input('Что делаешь??')

class Developer:
    def work(self):
        print('Пишу код.')
        

class Desinger:
    def work(self):
        print('Рисую кнопки')


team = [Developer(), Desinger()]

for member in team:
    member.work()