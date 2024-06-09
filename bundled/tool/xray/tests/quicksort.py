def unused_fn1(arg1):
    ...

def sort(array, z=5):
    """Sort the array by using quicksort."""

    less = []
    equal = []; greater =\
          []
    if (
        y := 5
    ) or False: ...
    if len(array) > 1:
        pivot = array[0]
        for x in array:
            if x < pivot:
                less.append(x)
            elif x == pivot:
                equal.append(x)
            elif x > pivot:
                greater.append(x)
        return (
            sort(less) + equal + sort(greater)
        )
    else:
        return array

def unused_fn2(*args):
    ...
