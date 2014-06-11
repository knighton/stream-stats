#!/usr/bin/python
#
# efficiently compute statistics of a stream of scalar values.

import cmath
import collections
import heapq
import numbers
import random

# ------------------------------------------------------------------------------
# streams.


class ScalarStream(object):
  def __iter__(self):
    return self

  def next(self):
    raise NotImplementedError


class ScalarListStream(ScalarStream):
  def __init__(self, nn):
    self.nn = nn
    self.x = 0

  def next(self):
    if not (self.x < len(self.nn)):
      raise StopIteration

    n = self.nn[self.x]
    assert isinstance(n, numbers.Real)
    self.x += 1
    return n


class RandomIntStream(ScalarStream):
  def __init__(self, n, z_incl):
    self.n = n
    self.z_incl = z_incl
    assert self.n <= self.z_incl

  def next(self):
    return random.randint(self.n, self.z_incl)


# ------------------------------------------------------------------------------
# stream stats.


class StreamStatter(object):
  def __init__(self, stream):
    self.stream = stream
    assert isinstance(self.stream, ScalarStream)

    self._count = 0

    # min.
    self._min = None

    # max.
    self._max = None

    # stddev.
    self._sum_squared = 0.0

    # arithmetic mean.
    self._sum = 0.0

    # geometric mean.
    self._product = 1.0

    # harmonic mean.
    self._seen_zero = False
    self._sum_of_inv = 0.0

    # mode.
    self._n2count = collections.defaultdict(int)
    self._max_n_count = None
    self._modes = []

    # median.
    self._neg_lt_maxheap = []
    self._gt_minheap = []

  def __iter__(self):
    return self

  def count(self):
    return self._count

  def min(self):
    return self._min

  def max(self):
    return self._max

  def stddev(self):
    if self._count <= 1:
      return None
    n = self._count
    r = (n * self._sum_squared - self._sum ** 2) / (n * (n - 1))
    return r ** 0.5

  def sum(self):
    return self._sum

  def arithmetic_mean(self):
    if not self._count:
      return None
    return self._sum / self._count

  def geometric_mean(self):
    if not self._count:
      return None

    exp = 1.0 / self._count
    if 0 <= self._product:
      return self._product ** exp

    return self._product ** (exp + 0j)

  def harmonic_mean(self):
    if not self._count:
      return None
    if self._seen_zero:
      return 0.0
    return self._count * self._sum_of_inv ** -1

  def modes(self):
    return self._modes

  def median(self):
    n = len(self._neg_lt_maxheap)
    z = len(self._gt_minheap)
    if n == z:
      n = -self._neg_lt_maxheap[0]
      b = self._gt_minheap[0]
      return (n + b) / 2.0
    elif n < z:
      return self._gt_minheap[0]
    else:
      return -self._neg_lt_maxheap[0]

  def next(self):
    n = self.stream.next()
    self._count += 1
    self.note_min(n)
    self.note_max(n)
    self.note_stddev(n)
    self.note_arithmetic_mean(n)
    self.note_geometric_mean(n)
    self.note_harmonic_mean(n)
    self.note_mode(n)
    self.note_median(n)
    return n

  def note_min(self, n):
    if self._min == None:
      self._min = n
      return

    self._min = min(n, self._min)

  def note_max(self, n):
    if self._max == None:
      self._max = n
      return

    self._max = max(n, self._max)

  def note_stddev(self, n):
    self._sum_squared += n ** 2

  def note_arithmetic_mean(self, n):
    self._sum += n

  def note_geometric_mean(self, n):
    self._product *= n

  def note_harmonic_mean(self, n):
    if n == 0:
      self._seen_zero = True
    if not self._seen_zero:
      self._sum_of_inv += n ** -1

  def note_mode(self, n):
    self._n2count[n] += 1
    a_count = self._n2count[n]
    if a_count > self._max_n_count:
      self._max_n_count = a_count
      self._modes = [n]
    elif a_count == self._max_n_count:
      self._modes.append(n)

  def note_median(self, n):
    if len(self._neg_lt_maxheap) == len(self._gt_minheap):
      # stacks same size: get the largest of (left, me) and put it on right.
      if self._neg_lt_maxheap and n < -self._neg_lt_maxheap[0]:
        heapq.heappush(self._neg_lt_maxheap, -n)
        n = -heapq.heappop(self._neg_lt_maxheap)
      heapq.heappush(self._gt_minheap, n)
    else:
      # unbalanced stacks (right has one more than left): get the smallest of
      # (me, right) and put it on left.
      if self._gt_minheap and self._gt_minheap[0] < n:
        heapq.heappush(self._gt_minheap, n)
        n = heapq.heappop(self._gt_minheap)
      heapq.heappush(self._neg_lt_maxheap, -n)

  def stats(self):
    return {
      'count':           self.count(),
      'min':             self.min(),
      'max':             self.max(),
      'sum':             self.sum(),
      'stddev':          self.stddev(),
      'arithmetic_mean': self.arithmetic_mean(),
      'geometric_mean':  self.geometric_mean(),
      'harmonic_mean':   self.harmonic_mean(),
      'modes':           self.modes(),
      'median':          self.median(),
    }


def demo_api():
  stream = RandomIntStream(-1000, 1000)
  stat = StreamStatter(stream)
  nn = []
  for n in stat:
    nn.append(n)
    print sorted(nn), stat.stats()
    _ = raw_input()


def demo_perf():
  stream = RandomIntStream(-1000, 1000)
  stat = StreamStatter(stream)
  i = 0
  for n in stat:
    if not i % 10000:
      print i
    i += 1
    if i == 1000000:
      break


if __name__ == '__main__':
  demo_api()
  #demo_perf()
