def main(
        arg1=1,
        arg2=2
):
    """Sort the array by using quicksort."""
    list_comp = [
        2 * i for i in range(3)
    ]
    set_comp = {
        i + 1
        for i
        in range(3)
    }

    generator = (x * 2 for x in range(3))
    for x in generator:
        y = x + 1

    for i in [1,2]:
        for j in [3,4]:
            z = (i, j)

    try:
        a = 2
    except KeyboardInterrupt:
        b = 3
    except SyntaxError:
        c = 4
    else:
        d = 5
    finally:
        e = 6

    def fun():
        for i in range(3):
            i += 1
