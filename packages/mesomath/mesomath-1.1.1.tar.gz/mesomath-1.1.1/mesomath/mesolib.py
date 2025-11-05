"""This module implements several functions for basic sexagesimal arithmetic operations related to Mesopotamian mathematics. Inpired by the arithmetic part of Baptiste Mélès' MesoCalc

    https://github.com/BapMel/mesocalc
    http://baptiste.meles.free.fr/site/mesocalc.html

jccvsq fecit 2025. Public domain"""

from math import log, sqrt
from sqlite3 import connect


def is_regular(x, divisors=False):
    """Check if x is regular for both decimal and sexagesimal numbers

    :x: may be decimal or sexagesimal
    :divisors: prints the divisors of x to stdout (default: False)

    """
    if type(x) is str:
        x = sex2dec(x)
    if x == 1:
        return True
    i = j = k = 0
    while x % 2 == 0:
        i += 1
        x //= 2
    while x % 3 == 0:
        j += 1
        x //= 3
    while x % 5 == 0:
        k += 1
        x //= 5
    if divisors:
        print(i, j, k, x)
    if x > 1:
        return False
    else:
        return True


def reciprocal(x):
    """Returns the reciprocal of regular number x or 0 if not regular
    x may be decimal or sexagesimal"""
    if type(x) is str:
        x = sex2dec(x)
    while x % 60 == 0:
        x //= 60
    #    print(x, dec2sex(x))
    #   Should use is_regular() !!!
    if x == 1:
        return 1
    i = j = k = 0
    while x % 2 == 0:
        i += 1
        x //= 2
    while x % 3 == 0:
        j += 1
        x //= 3
    while x % 5 == 0:
        k += 1
        x //= 5
    if x > 1:
        #        print(f'{x0} ({dec2sex(x0)}) is not a regular number!\n{x} Exiting')
        #        print(i,j,k)
        return 0
    else:
        #        print(i,j,k)
        i0 = j0 = k0 = 0
        if i % 2 == 1:
            i0 += 1
            i += 1
        if j > k:
            k0 += j - k
            k += j - k
        if k > j:
            j0 += k - j
            j += k - j
        if i < 2 * j:
            i0 += 2 * j - i
            i += 2 * j - i
        if i > 2 * j:
            t = (i - 2 * j) // 2
            j += t
            k += t
            j0 += t
            k0 += t
        #        print(i0,j0,k0)
        return pow(2, i0) * pow(3, j0) * pow(5, k0)


def dec2list(n):
    """Convert integer decimal n to list of int's (sexagesimal digits)"""
    if n < 60:
        return [n]
    else:
        rlist = []
        while n >= 60:
            rlist.append(n % 60)
            n = n // 60
        if n > 0:
            rlist.append(n)
        rlist.reverse()
    return rlist


def dec2sex(n, fill=False, sep=":"):
    """Convert decimal n to sexagesimal

    :fill: pad with left 0 sexagesimal digits <= 9 (default: False)
    :sep: sexagesimal digit separator (default: ":")

    """
    if n < 60:
        return f"{n:02d}"
    else:
        rlist = dec2list(n)
        if fill:
            tt = list(map(str, rlist))
            for i in range(len(tt)):
                if len(tt[i]) == 1:
                    tt[i] = "0" + tt[i]
            return sep.join(tt)
        else:
            return sep.join(map(str, rlist))


def sex2list(st):
    '''Convert sexagesimal st to list of int's
    Sexagesimal separator may be ":" or "."'''
    if st.find(":") > 0:
        lt = [int(j) for j in st.split(":")]
    elif st.find(".") > 0:
        lt = [int(j) for j in st.split(".")]
    else:
        lt = [int(st)]
    return lt


def sex2dec(st):
    '''Convert sexagesimal n to decimal
    Sexagesimal separator may be ":" or "."'''
    lt = sex2list(st)
    rs = 0
    for i in lt:
        rs = rs * 60 + i
    return rs


def sexmult(a, b, fill=False, sfloat=False):
    '''Sexagesimal multiplication
    Sexagesimal separator may be ":" or "."'''
    if type(a) is str:
        a = sex2dec(a)
    if type(b) is str:
        b = sex2dec(b)
    p = a * b
    if sfloat:
        p = sexfloat(p)
    return dec2sex(p, fill)


def sexadd(a, b, fill=False):
    '''Sexagesimal addition
    Sexagesimal separator may be ":" or "."'''
    if type(a) is str:
        a = sex2dec(a)
    if type(b) is str:
        b = sex2dec(b)
    p = a + b
    return dec2sex(p, fill)


def sexsub(a, b, fill=False):
    """Sexagesimal subtraction

    :a and b: Sexagesimal separator may be ":" or "."
    :fill: add left zero to sexagesimal digits <= 9 (default: False)

    """
    if type(a) is str:
        a = sex2dec(a)
    if type(b) is str:
        b = sex2dec(b)
    p = abs(a - b)
    return dec2sex(p, fill)


def regular(i, j, k):
    """Returns regular number: 2^i × 3^j × 5^k as decimal"""
    return pow(2, i) * pow(3, j) * pow(5, k)


def sexinv(x, digits=3):
    """Returns the floating approximate inverse of x or its reciprocal if regular

    :x: may be decimal or sexagesimal
    :digits: Number of digits to return (default: 3)

    """
    if type(x) is str:
        x = sex2dec(x)
    nsd = int(log(x) / log(60))
    inv = (pow(60, nsd + digits)) / x
    inv = int(round(inv, 0))
    inv = sexfloat(inv)
    return dec2sex(inv)


def sexdiv(a, b, digits=3):
    """Returns approximate floating division a/b

    :a and b: may be decimal or sexagesimal
    :digits: desired number of digits in the sexagesimal quotient (the actual result may differ by 1)

    """
    if type(a) is str:
        a = sex2dec(a)
    if type(b) is str:
        b = sex2dec(b)
    q = a / b
    nsd = int(log(q) / log(60))
    print(nsd)
    inv = pow(60, digits - nsd) * q
    inv = int(round(inv, 0))
    inv = sexfloat(inv)
    return dec2sex(inv)


def sexfloat(x):
    """Returns floating version of number x

    :x: may be decimal or sexagesimal

    """
    if type(x) is str:
        x = sex2dec(x)
    while x % 60 == 0:
        x //= 60
    return x


def sexlen(x, sep=":"):
    """returns the number of sexagesimal digits of x"""
    return len(x.split(sep))


def multable(n, pral=True, sep=":", fill=False):
    """Returns the n multiplication table for principal numbers or for all

    :n: decimal integer < 60
    :pral: if True writes the table for principal numbers:

     |       [i+1 for i in range(20)]+[30,40,50]
     |   if False writes the table for:
     |       [i+1 for i in range(59)]
     |   (default: True)

    :sep: sexagesimal digits separator (default: ":")
    :fill: add left zero to sexagesimal digits <= 9 (default: False)

    """
    if pral:
        pnum = [i + 1 for i in range(20)] + [30, 40, 50]
    else:
        pnum = [i + 1 for i in range(59)]
    for i in pnum:
        print(i, dec2sex(n * i, sep=sep, fill=fill))


def searchreg(database, minn, maxn, limdigits=6, prt=False):
    """Search database for regulars between sexagesimals minn y maxn

    :minn and maxn: must be sexagesimals using ":" separator
    :limdigits: max regular digits number (default: 6)
    :prt: Dump to stdout (default: False)

    """
    conn = connect(database)
    cursor = conn.cursor()
    sql_line = """
SELECT regular
  FROM regulars
 WHERE len <= ? AND 
       regular BETWEEN ? AND ?
 ORDER BY regular
;
"""
    #    print(sql_line)
    cursor.execute(sql_line, (limdigits, minn, maxn))
    output = cursor.fetchall()
    if prt:
        print(
            f"\nRegular numbers between {minn} and {maxn}"
            + f" with {limdigits} digits or less:\n"
        )
        for row in output:
            (a,) = row
            print(f" Reg.:  {a}")
        print("\n")
    conn.commit()
    conn.close()
    return output


def sexsqrt(x, digits=3, prt=False):
    """Returns approximate square root of x"""
    digits -= 1
    if type(x) is str:
        x0 = x
        x = sex2dec(x)
    else:
        x0 = dec2sex(x)
    sqr = (pow(60, digits)) * sqrt(x)
    sqr = sexfloat(int(round(sqr, 0)))
    sexsqr = dec2sex(sqr)
    if prt:
        sq = dec2sex(sqr * sqr)
        print(f"Number: {x0}, square root: {sexsqr}, square of root: {sq}")
    return sexsqr


def sexcbrt(x, digits=3, prt=False):
    """Returns approximate cube root of x"""
    digits -= 1
    if type(x) is str:
        x0 = x
        x = sex2dec(x)
    else:
        x0 = dec2sex(x)
    cbr = (pow(60, digits)) * x ** (1.0 / 3)
    cbr = sexfloat(int(round(cbr, 0)))
    sexsqr = dec2sex(cbr)
    if prt:
        cb = dec2sex(cbr * cbr * cbr)
        print(f"Number: {x0}, cube root: {sexsqr}, cube of root: {cb}")
    return sexsqr


def sexsquare(x, prt=False):
    """Returns square of x"""
    if type(x) is str:
        x0 = x
        x = sex2dec(x)
    else:
        x0 = dec2sex(x)
    sqr = sexfloat(x * x)
    sexsqr = dec2sex(sqr)
    if prt:
        print(f"Number: {x0}, square: {sexsqr}")
    return sexsqr


def sexcube(x, prt=False):
    """Returns square of x"""
    if type(x) is str:
        x0 = x
        x = sex2dec(x)
    else:
        x0 = dec2sex(x)
    sqr = sexfloat(x * x * x)
    sexsqr = dec2sex(sqr)
    if prt:
        print(f"Number: {x0}, cube: {sexsqr}")
    return sexsqr


if __name__ == "__main__":
    #    gencsvtable(79405)
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
