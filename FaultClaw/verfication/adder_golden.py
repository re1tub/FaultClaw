def golden_adder(a, b):
    total = a + b

    sum_ = total & 0b1111
    cout = (total >> 4) & 0b1

    return sum_, cout


print(golden_adder(15, 1))