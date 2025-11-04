from .fire_ascii import fire
from .rules import rules

def resolve(*args, **kwargs):
    global onfire
    onfire = False

    for key, condition in rules:
        value = kwargs.get(key)

        if value is not None:
            try:
                onfire = condition(value)
            except:
                pass

def check(*args, **kwargs):
    resolve(*args, **kwargs)

    if onfire:
        print(fire)
    else:
        print("No.")
