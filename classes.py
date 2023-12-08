import pickle
import re
from collections import UserDict
from datetime import datetime, timedelta
from pathlib import Path
from rich.table import Table

PAGINATION = 4
DATA_PATH = "./phonebook.bin"

class Field:
    def __init__(self, value: str) -> None:
        self.__value = None
        self.value = value
    def __str__(self) -> str:
        return self.value

class Name(Field):
    pass

class PhoneError(Exception):
    pass

class Phone(Field):
    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, value):
        if self.is_correct_phone(value):
            self.__value = value
        else:
            raise PhoneError()
        
    def is_correct_phone(self, value) -> bool:
        result = re.findall(r"(\+\d{1,3}\d{2}\d{6,8})", value)
        return result != list()

class BirthdayError(Exception):
    pass

class Birthday(Field):
    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, value):
        if value.find("-") > 0:
            self.__value = datetime.strptime(value, "%d-%m-%Y")
        elif value.find(".") > 0:
            self.__value = datetime.strptime(value, "%d.%m.%Y")
        elif value.find("/") > 0:
            self.__value = datetime.strptime(value, "%d/%m/%Y")
        else:
            raise BirthdayError()
    
    def is_empty_date(self) -> bool:
        return self.__value == datetime(1, 1, 1)
        
    def __str__(self):
        return self.__value.strftime("%d-%m-%Y") if not self.is_empty_date() else ""
        
class Record:
    def __init__(self, name:Name, phone:Phone=None, birthday:Birthday=None) -> None:
        self.name = name
        self.phones = []
        self.birthday = birthday if birthday else Birthday("1-1-0001") 

        if phone:
            self.phones.append(phone)

    def add_phone(self, phone:Phone):
        if str(phone) not in [str(p) for p in self.phones]:
            self.phones.append(phone)
            return f"Succesfully added phone '{phone}' to name '{self.name}'"
        else:
            return f"Phone '{phone}' is already in record '{self}'"
        
    def change_phone(self, old_phone:Phone, new_phone:Phone):
        phones_list = [str(p) for p in self.phones]

        if str(old_phone) not in phones_list:
            return f"There is no phone '{old_phone}' in record '{self}'"
        if str(new_phone) in phones_list:
            return f"Phone '{new_phone}' is already in record '{self}'"
        
        index = phones_list.index(old_phone.value)
        self.phones[index] = new_phone
        return f"Succesfully changed phone '{old_phone}' to '{new_phone}'"
        
    def show_phones(self, separeter:str=', ') -> str:
        return separeter.join(str(p) for p in self.phones)

    def days_to_birthday(self) -> int|None:
        if self.birthday.is_empty_date():
            return None
        
        date_now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_birth = self.birthday.value.replace(hour=0, minute=0, second=0, microsecond=0)
        
        date_birth_current = date_birth.replace(year=date_now.year)
        date_birth_next = date_birth.replace(year=date_now.year+1)
        if date_birth_current > date_now:
            result = date_birth_current - date_now
            return result.days
        elif date_birth_current < date_now:
            result = date_birth_next - date_now
            return result.days - 1
        else:
            return 0

    def __str__(self) -> str:
        return f"{self.name} {self.show_phones()} {self.birthday}".strip()

class AdressBook(UserDict):
    def add_record(self, record:Record) -> str:
        self.data[record.name.value] = record
        return f"Succesfully added record '{record}'"
        
    def delete_record(self, name) -> str:
        current_record = self.data.pop(name.value)
        
        if current_record:
            return f"Succesfully deleted record '{current_record}'"
        else:
            return f"Can't find name '{name}'"
    
    def show_phones(self, name:Name) -> Phone:
        record:Record = self.get(name.value)

        if record:
            return f"Successfully finded numbers '{record.show_phones()}' with name '{name}'"
        else:
            return f"Can't find number with name '{name}'"
            
    def iterator(self, pagination:int=4):
        count = 0
        
        def get_new_table():
            table = Table(title="Contacts list")
            table.add_column("Name", justify="center", width=25)
            table.add_column("Phone Number", justify="center", width=25)
            table.add_column("Birthday Date", justify="center", width=25)
            table.add_column("Days till birthday", justify="center", width=25)

            return table

        result = get_new_table()
        for name, record in self.data.items():
            count += 1
            
            days = record.days_to_birthday()
            days_str = ""
            
            if days == 0:
                days_str = "Today"
            elif days:
                days_str = str(days)
            else:
                days_str = ""

            result.add_row(str(name), record.show_phones("\n"), str(record.birthday), days_str)
            
            if not count % pagination or len(self.data.keys()) == count:
                yield result
                result = get_new_table()

    def show_all(self) -> list[Table]|str:
        result = []
        generator = self.iterator(PAGINATION)
        for i in generator:
            result.append(i)
        
        if len(result):
            return result
        else:
            return "Can't find records in adressbook!"
    
    def write_data(self):
        data = {}

        for key, value in self.items():
            data[key] = {"phones": [str(p) for p in value.phones], "birthday": "" if value.birthday.is_empty_date() else str(value.birthday)}

        with open(DATA_PATH, "wb") as fh:
            pickle.dump(data, fh)

    def read_data(self):
        if Path(DATA_PATH).exists():
            self.clear()
            
            with open(DATA_PATH, "rb") as fh:
                unpacked = pickle.load(fh)

            for key, value in unpacked.items():
                birthday = value["birthday"]
                
                if birthday:
                    record = Record(name=Name(key), birthday=Birthday(birthday))
                else:
                    record = Record(name=Name(key))

                for phone in value["phones"]:
                    record.add_phone(phone)

                self.add_record(record)

    def find(self, search:str) -> list[Table]|str:
        ab = AdressBook()
        for record in self.data.values():
            if search in str(record.name) or search in str(record.phones):
                ab.add_record(record)
        
        return ab.show_all()


class SerializingError(pickle.PicklingError):
    pass


class DataError(pickle.PickleError):
    pass