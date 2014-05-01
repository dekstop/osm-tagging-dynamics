
from decimal import Decimal

import numpy as np

# ========================
# = Percentile selection =
# ========================

# Maps a percentile value to an overall length.
# Returns None if perc is None.
def get_percentile_index(length, perc):
  if perc==None:
    return None
  return int(length * perc / Decimal(100))

# What is the sum of a percentile segment of entries?
#
# The process:
# - order all values by size (by default: in ascending order)
# - identify the index positions for the given percentages (rounding down)
# - return the values between these positions
#
# values: array of numbers
# from_pc: [0..100], or None
# to_pc: [0..100], or None
# descending: rank in descending order? This can be used to select top percentiles.
# 
# Constraints: 
# - from_pc < to_pc
# - at least one of [from_pc, to_pc] needs to be non-null
def percentile_range(values, from_pc, to_pc, descending=False):
  if from_pc==None and to_pc==None:
    raise Exception("No range was provided: both [from_pc, to_pc] are None")
  if from_pc!=None and to_pc!=None and from_pc>=to_pc:
    raise Exception("Illegal range: from_pc >= to_pc (%s >= %s)" % (from_pc, to_pc))
  values = sorted(values, reverse=descending)
  length = len(values)
  from_idx = get_percentile_index(length, from_pc)
  to_idx = get_percentile_index(length, to_pc)
  return values[from_idx:to_idx]

# What is the sum of a percentile segment of entries?
#
# values: array of numbers
# from_pc: [0..100], or None
# to_pc: [0..100], or None
# descending: rank in descending order? This can be used to select top percentiles.
# 
# Constraints: 
# - from_pc < to_pc
# - at least one of [from_pc, to_pc] needs to be non-null
def percentile_range_sum(values, from_pc, to_pc, descending=False):
  return sum(percentile_range(values, from_pc, to_pc, descending=descending))

# What is the share (workload, income, ...) of a percentile segment of entries?
#
# values: array of numbers
# from_pc: [0..100], or None
# to_pc: [0..100], or None
# descending: rank in descending order? 
def percentile_range_share(values, from_pc, to_pc, descending=False):
  return Decimal(percentile_range_sum(values, from_pc, to_pc, descending=descending)) / sum(values)

# What is the sum of the lowest-ranking x% number of entries?
#
# values: array of numbers
# perc: [0..100]
# top: sum of top percentile? (vs bottom percentile)
def ranked_percentile_sum(values, perc, top=False):
  return percentile_range_sum(values, None, perc, descending=top)

# What is the share (workload, income, ...) of the lowest-ranking x% number of entries (contributors)?
#
# values: array of numbers
# perc: [0..100]
# top: share of top percentile? (vs bottom percentile)
def ranked_percentile_share(values, perc, top=False):
  return Decimal(ranked_percentile_sum(values, perc, top=top)) / sum(values)
