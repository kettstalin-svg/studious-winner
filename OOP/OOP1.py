# user = {
#     'name': 'Kirill',
#     'age': 18.
#     # 'say_hello': def say_hell(): print(f'Привет, меня зовут {name}')
# }


# # user.say_hello()

# class User:
#     def __init__(self, name, age):
#         self.name = name
#         self.age = age
#         self.is_human = True
#         print('ERRor')
# user1 = User('Kirill', 18) # Экзеспляр (= self в шаблоне)

# def say_hello(self, to_name):
#     self.age += 1
#     print(f'Привет меня зовут, {to_name}. Мне {self.age} лет')



# user1 = User('КИрилл, ', 19)


# print(user1.name)

# user1.say_hello(to_name ="Вася")

# user2 = User('Alex', 101)
# print(user2.name)





class GameCharacter:
    def __init__(self, name, damage, heart):
        self.name = name
        self.damage = damage
        self.heart = heart
    
    def attack(self):
        print(f"{self.name} наносит {self.damage} урона!")

