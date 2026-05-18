class BankAccount:
    def __init__(self, balance):
        self._balance = balance
    
    
    def deposit(self, amount):
        if amount > 0:
            self._balance += amount
    
    def get_balance(self):
        return self._balance
    
    
bank = BankAccount(1000)

# ._ - нужен для того чтобы блокировать изменения. Также .__ - при попытке изменения выводит ошибку.
print(bank.__dict__)
print(bank._balance)

bank._BankAccount__balance = 100000

print(bank._balance)