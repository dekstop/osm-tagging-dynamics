from decimal import Decimal

import numpy as np

from .percentiles import *

# ====================
# = Gini coefficient =
# ====================

# From http://planspace.org/2013/06/21/how-to-calculate-gini-coefficient-from-raw-data-in-python/

# values: a list of positive integers
def gini(values):
  sorted_list = sorted(values)
  height, area = 0, 0
  for value in sorted_list:
    height += value
    area += height - value / Decimal(2)
  fair_area = height * len(values) / Decimal(2)
  return (fair_area - area) / fair_area

# ===============
# = Palma ratio =
# ===============

# Palma ratio: top 10% vs bottom 40% income
def palma(values):
  top_10 = ranked_percentile_sum(values, Decimal(10), top=True)
  bottom_40 = ranked_percentile_sum(values, Decimal(40), top=False)
  if bottom_40==0:
    return None
  else:
    return Decimal(top_10) / bottom_40

# ===============
# = Theil index =
# ===============

# From http://stackoverflow.com/questions/20279458/implementation-of-theil-inequality-index-in-python

def error_if_not_in_range01(value):
  if (value < 0) or (value > 1):
    raise Exception, str(value) + ' is not in [0,1]!'

def Group_negentropy(x_i):
  if x_i == 0:
    return 0.0
  else:
    return x_i * np.log(x_i)

def H(x):
  n = len(x)
  entropy = 0.0
  sum = 0.0
  for x_i in x: # work on all x[i]
    # print x_i
    error_if_not_in_range01(x_i)
    sum += x_i
    group_negentropy = Group_negentropy(x_i)
    entropy += group_negentropy
  # error_if_not_1(sum)
  return -entropy

# x is a list of percentages in the range [0,1]
# NOTE: sum(x) must be 1.0
def theil(x):
  # print x
  n = len(x)
  maximum_entropy = np.log(n)
  actual_entropy = H(x)
  redundancy = maximum_entropy - actual_entropy
  inequality = 1 - np.exp(-redundancy)
  return redundancy,inequality
