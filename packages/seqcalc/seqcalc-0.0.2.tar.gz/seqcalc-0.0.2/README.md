A Python package for calculating arithmetic sequences.

*Features:*

- Calculate the nth term of an arithmetic sequence
- Calculate the sum of the first n terms of an arithmetic sequence

*Installation:*

    pip install seqcalc

*Usage:*

Find the nth term

    seqcalc.find(nth, first_term, common_difference)

Find the sum

    seqcalc.find_sum(nth, first_term, common_difference)

Example:

    import seqcalc

    nth = 16
    first_term = 3
    d = 2

    seq = seqcalc.find(nth, first_term, d)
    print(seq)

    # output: 33