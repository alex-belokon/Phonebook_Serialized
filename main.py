from classes import Name, PhoneError, Phone, BirthdayError, Birthday, Record, AdressBook, SerializingError, DataError, Table
from rich import print

def parcing_data(value:str) -> dict:
    result = {}
    value_list = value.split(" ")
    
    if len(value_list) >= 2:
        command = " ".join(value_list[0:2])
        if command in tuple(COMMANDS.keys()):
            result["command"] = command
            value_list = value_list[1:]

    count = 1
    for item in value_list:
        if count == 1 and not result.get("command") and item in tuple(COMMANDS.keys()):
            result["command"] = item
        if count == 2:
            result["name"] = item
        if count == 3:
            result["phone"] = item
        if count == 4:
            if result["command"] == "change":
                result["new_phone"] = item
            else:
                result["birthday"] = item
        if count == 5 and result["command"] == "change":
            result["birthday"] = item
        count += 1
    return result

def input_error(handler_func):
    def inner_func(**kwargs):
        try:
            result = handler_func(**kwargs)
            if kwargs["command"] in ("add", "change", "delete"):
                adressbook.write_data()
        except KeyError as key:
            result = f"Name {key} is not found" if not str(key) in ("'name'", "'phone'") else f"You must enter {key}"
        except BirthdayError:
            result = "Date of birth must be one of the formats: '%d-%m-%Y', '%d.%m.%Y', '%d/%m/%Y'"
        except PhoneError:
            result = "Phone number must be in format '+\[country]\[town]\[number]'. Examples: '+380661234567' or '+442012345678'"
        except SerializingError:
            result = "Can't serializing data! Something go wrong!"
        except DataError:
            result = "Can't write data file! Something go wrong!"
        
        return result
    return inner_func

def command_hello(**kwargs) -> str:
    return "How can I help you?"

@input_error
def command_add(**kwargs) -> str:
    name = Name(kwargs["name"])
    phone = Phone(kwargs["phone"])
    record:Record = adressbook.get(name.value)
    if record:
        return record.add_phone(phone)
    else:
        birthday_value = kwargs.get("birthday")
        if birthday_value:
            birthday = Birthday(birthday_value)
            record = Record(name, phone, birthday)
        else:
            record = Record(name, phone)
        
        return adressbook.add_record(record)

@input_error
def command_change(**kwargs) -> str:
    name = Name(kwargs["name"])
    phone = Phone(kwargs["phone"])
    new_phone = Phone(kwargs["new_phone"])
    record:Record = adressbook.get(name.value)
    if record:
        return record.change_phone(phone, new_phone)
    else:
        return f"Can't find name '{name}'"

@input_error
def command_delete(**kwargs) -> str:
    name = Name(kwargs["name"])
    return adressbook.delete_record(name)

@input_error
def command_phone(**kwargs) -> str:
    name = Name(kwargs["name"])
    return adressbook.show_phones(name)

def command_show_all(**kwargs) -> Table:
    return adressbook.show_all()

@input_error
def command_find(**kwargs) -> str:
    search = kwargs["name"]
    return adressbook.find(search)

def command_exit(**kwargs) -> str:
    return "Good bye!"

COMMANDS = {"hello": command_hello,
            "add": command_add,
            "change": command_change,
            "delete": command_delete,
            "phone": command_phone,
            "show all": command_show_all,
            "find": command_find,
            "good bye": command_exit,
            "close": command_exit,
            "exit": command_exit}

def get_handler(command:str):
    return COMMANDS[command.lower()]

def main():
    adressbook.read_data()
    while True:
        user_input = input("Enter command: ")
        command_dict = parcing_data(user_input)
        command = command_dict.get("command", "")
        if command:
            handler = get_handler(command)        
            result = handler(**command_dict)
            if command in ("exit", "good bye", "close"):
                print(result, "\n")
                break
            if isinstance(result, (list, tuple)):
                print(*result, "\n")
            else:
                print(result, "\n")
        else:
            print("Can not recognize a command! Please, try again.", "\n")     

if __name__ == "__main__":
    adressbook = AdressBook()
    main()
    