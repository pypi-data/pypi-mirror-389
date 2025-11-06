import pkgutil

__version__ = "0.1.7"

def show_message():
    data = pkgutil.get_data(__name__, "message.txt").decode("utf-8")
    print(data)

# Automatically show message on import
show_message()
