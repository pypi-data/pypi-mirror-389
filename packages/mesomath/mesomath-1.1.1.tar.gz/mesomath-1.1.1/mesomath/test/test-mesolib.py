from mesomath.mesolib import *

multable(37)

b = searchreg("regular.db3", "06:50", "07:10", 6, True)
for i in b:
    print(i[0])
print("\n")
x = "2"
a = sexsqrt(x, prt=True, digits=4)
print(a, "\n")
a = sexcbrt(x, prt=True, digits=4)
print(a, "\n")
a = sexsquare("5:05", 1)
print(a, "\n")
a = sexcube("5:05", 1)
print(a, "\n")
a = sexcube("5", 1)
print(a, "\n")
