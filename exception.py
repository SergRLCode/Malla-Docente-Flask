list = []

try:
    if 3 in list[0]:
        print("Si pull")
except IndexError:
    print(IndexError.args)
except:
    print("error")