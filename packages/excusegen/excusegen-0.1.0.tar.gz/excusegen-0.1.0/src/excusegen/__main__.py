from .main import get_excuse, get_excuses

if __name__ == "__main__":
    print(get_excuse())
    print()
    excuses = get_excuses(count = 2)
    for e in excuses:
        print(e)
    print()
    excuses = get_excuses()
    for e in excuses:
        print(e)
    print()
    excuses = get_excuses(count = 4)
    for e in excuses:
        print(e)
        