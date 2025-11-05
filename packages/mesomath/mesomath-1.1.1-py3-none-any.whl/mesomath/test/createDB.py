"""This script generates a SQLite3 database of regular numbers up to 20 sexagesimal digits for use with the `mesomath.babn` module.

Use:
    $ python3 createDB.py -h
for options.

jccsvq fecit, 2025. Public domain.
"""
from sqlite3 import connect
from mesomath.babn import BabN
from mesomath.hamming import hamming
import argparse

sqlhead = """
CREATE TABLE regulars (
id INTEGER PRIMARY KEY,
regular    TEXT,
len     INTEGER
);
"""

sqltail = """CREATE UNIQUE INDEX regs ON regulars (regular);
"""

DESC = """Generates SQLite3 database of regular numbers until 20 max sexagesimal
 digits for use in MesoMath."""
EPIL = "jccsvq fecit, 2025. Public domain."


def genDB(dbname):
    """Generates sqlite3 database of regular numbers
    | dbname: database path and name"""
    rlist = hamming(1, 80000)
    i = 0
    BabN.fill = True

    con = connect(dbname)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS regulars;")
    cur.execute(sqlhead)

    for x in rlist:
        if x % 60 != 0:
            i += 1
            n = BabN(x)
            nlen = n.len()
            cur.execute(f"INSERT INTO regulars VALUES({i},'{n}',{nlen});")
    cur.execute(sqltail)
    con.commit()
    con.close()
    print(
        f"""Database: {dbname} created.\n use:\n
    BabN.database = "{dbname}"\n\nprior to use it in your computations\n"""
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=DESC,
        epilog=EPIL,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="path/filename to generated database",
        default="regular.db3",
    )

    args = parser.parse_args()

    genDB(args.output)
