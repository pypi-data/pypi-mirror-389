"""
From Duncan J. Melville Reciprocals and Reciprocal algorithms in Mesopotamian Mathematics (2005)

https://www.researchgate.net/publication/237309438_RECIPROCALS_AND_RECIPROCAL_ALGORITHMS_IN_MESOPOTAMIAN_MATHEMATICS

Example 1: from Table 2. Simple Reciprocal algorithm
Example 2: from Table 3. using "The Technique"
"""

from mesomath.babn import BabN

print("\nSearching the reciprocal of 2:5  according to D. J. Melville (2005)\n")

print("Example 1: from Table 2. Simple Reciprocal algorithm\n")


print(
    """d1 = BabN('2:5')
r1 = d1.tail()
r2 = r1.rec()
r3 = d1 * r2
r4 = r3.rec()
r5 = r4 * r2"""
)

d1 = BabN("2:5")
r1 = d1.tail()
r2 = r1.rec()
r3 = d1 * r2
r4 = r3.rec()
r5 = r4 * r2

print("\nResult r5 = ", r5)

print('\nExample 2: from Table 3. using "The Technique"\n')

print(
    """r1 = d1.tail()
r2 = r1.rec()
r3 = d1.head() * r2
r4 = r3+BabN(1)
r5 = r4.rec()
r6 = r5 * r2"""
)


r1 = d1.tail()
r2 = r1.rec()
r3 = d1.head() * r2
r4 = r3 + BabN(1)
r5 = r4.rec()
r6 = r5 * r2

print("\nResult r6 = ", r6)
