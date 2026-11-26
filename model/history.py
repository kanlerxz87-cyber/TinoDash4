"""
history.py — annual return series used by the Black-Swan and phased-investing work.

Source: A. Damodaran, "Historical Returns on Stocks, Bonds and Bills: 1928-2024 (and 2025)",
NYU Stern, table updated 5 January 2026 (accessed 2026-11-25).
  * S&P 500 column = total return including dividends.
  * 3-month T-bill column = average bill rate during the year (the source states it replaced
    end-of-period rates for exactly that reason).
This is an academic dataset, not an official statistic: see Flagged for Review item F-9.
Tuple order: (year, S&P 500 total return %, 3-month T-bill %).
"""

RETURNS = [
    (1928, 43.81, 3.08), (1929, -8.30, 3.16), (1930, -25.12, 4.55), (1931, -43.84, 2.31),
    (1932, -8.64, 1.07), (1933, 49.98, 0.96), (1934, -1.19, 0.28), (1935, 46.74, 0.17),
    (1936, 31.94, 0.17), (1937, -35.34, 0.28), (1938, 29.28, 0.07), (1939, -1.10, 0.05),
    (1940, -10.67, 0.04), (1941, -12.77, 0.13), (1942, 19.17, 0.34), (1943, 25.06, 0.38),
    (1944, 19.03, 0.38), (1945, 35.82, 0.38), (1946, -8.43, 0.38), (1947, 5.20, 0.60),
    (1948, 5.70, 1.05), (1949, 18.30, 1.12), (1950, 30.81, 1.20), (1951, 23.68, 1.52),
    (1952, 18.15, 1.72), (1953, -1.21, 1.89), (1954, 52.56, 0.94), (1955, 32.60, 1.72),
    (1956, 7.44, 2.62), (1957, -10.46, 3.22), (1958, 43.72, 1.77), (1959, 12.06, 3.39),
    (1960, 0.34, 2.87), (1961, 26.64, 2.35), (1962, -8.81, 2.77), (1963, 22.61, 3.16),
    (1964, 16.42, 3.55), (1965, 12.40, 3.95), (1966, -9.97, 4.86), (1967, 23.80, 4.29),
    (1968, 10.81, 5.34), (1969, -8.24, 6.67), (1970, 3.56, 6.39), (1971, 14.22, 4.33),
    (1972, 18.76, 4.06), (1973, -14.31, 7.04), (1974, -25.90, 7.85), (1975, 37.00, 5.79),
    (1976, 23.83, 4.98), (1977, -6.98, 5.26), (1978, 6.51, 7.18), (1979, 18.52, 10.05),
    (1980, 31.74, 11.39), (1981, -4.70, 14.04), (1982, 20.42, 11.09), (1983, 22.34, 8.95),
    (1984, 6.15, 9.92), (1985, 31.24, 7.72), (1986, 18.49, 6.15), (1987, 5.81, 5.96),
    (1988, 16.54, 6.89), (1989, 31.48, 8.39), (1990 - 0, -3.06, 7.75), (1991, 30.23, 5.54),
    (1992, 7.49, 3.51), (1993, 9.97, 3.07), (1994, 1.33, 4.37), (1995, 37.20, 5.66),
    (1996, 22.68, 5.15), (1997, 33.10, 5.20), (1998, 28.34, 4.91), (1999, 20.89, 4.78),
    (2000, -9.03, 6.00), (2001, -11.85, 3.48), (2002, -21.97, 1.64), (2003, 28.36, 1.03),
    (2004, 10.74, 1.40), (2005, 4.83, 3.22), (2006, 15.61, 4.85), (2007, 5.48, 4.48),
    (2008, -36.55, 1.40), (2009, 25.94, 0.15), (2010, 14.82, 0.14), (2011, 2.10, 0.05),
    (2012, 15.89, 0.09), (2013, 32.15, 0.06), (2014, 13.52, 0.03), (2015, 1.38, 0.05),
    (2016, 11.77, 0.32), (2017, 21.61, 0.95), (2018, -4.23, 1.97), (2019, 31.21, 2.11),
    (2020, 18.02, 0.36), (2021, 28.47, 0.04), (2022, -18.04, 2.09), (2023, 26.06, 5.28),
    (2024, 24.88, 5.18), (2025, 17.78, 4.21),
]

YEARS = [r[0] for r in RETURNS]
SPX = {r[0]: r[1] / 100.0 for r in RETURNS}
BILL = {r[0]: r[2] / 100.0 for r in RETURNS}


def series(start, n, key):
    """Return list of annual rates for `key` starting at calendar year `start`."""
    out, y = [], start
    table = SPX if key == "spx" else BILL
    for _ in range(n):
        out.append(table.get(y, 0.0))
        y += 1
    return out


def stats():
    import math
    sp = [r[1] / 100.0 for r in RETURNS]
    bi = [r[2] / 100.0 for r in RETURNS]
    def geo(xs):
        p = 1.0
        for x in xs:
            p *= (1 + x)
        return p ** (1.0 / len(xs)) - 1
    def sd(xs, m):
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    return {
        "n_years": len(sp),
        "sp_geo": geo(sp), "sp_arith": sum(sp) / len(sp), "sp_sd": sd(sp, sum(sp) / len(sp)),
        "bill_geo": geo(bi), "bill_arith": sum(bi) / len(bi), "bill_sd": sd(bi, sum(bi) / len(bi)),
        "worst": min(sp), "best": max(sp),
        "worst_year": RETURNS[min(range(len(RETURNS)), key=lambda i: RETURNS[i][1])][0],
        "best_year": RETURNS[max(range(len(RETURNS)), key=lambda i: RETURNS[i][1])][0],
        "neg_years": sum(1 for x in sp if x < 0),
        "down20": sum(1 for x in sp if x < -0.20),
    }
