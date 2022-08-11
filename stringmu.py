#!/usr/bin/env python3
import argparse
import json
import math
import sys
import re

# simple binary minimum heap class for storing tuple data
class MinBinHeapTuple(object):
  def __init__(self):
      self._heap = []

  def _swap(self, idx1, idx2):
      self._heap[idx1], self._heap[idx2] = self._heap[idx2], self._heap[idx1]

  def _getpidx(self, idx):
      return math.floor((idx - 1)/2)

  def _siftup(self):
      idx = len(self._heap)-1

      while idx > 0:
          pidx = self._getpidx(idx)
          heap_data_idx = self._heap[idx]
          heap_data_pidx = self._heap[pidx]

          if heap_data_idx[0] < heap_data_pidx[0]:
              self._swap(idx, pidx)
          else:
              break
          idx = pidx

  def insert(self, thing):
      if isinstance(thing, tuple):
        self._heap.append(thing)
        self._siftup()

  def peek(self):
      return self._heap[0]

  def pop(self):
      popval = self._heap[0]
      del self._heap[0]

      self.heapify(self._heap)
      return popval

  def heapify(self, thingl):
      self._heap = []
      for thing in thingl:
          self.insert(thing)


def cli_args():
  p = argparse.ArgumentParser(
        prog="stringmu.py",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
      )

  p.add_argument(
    '-m',
    '--mode',
    type=str,
    required=False,
    default="unmix",
    choices=["mix", "unmix"],
    help="mode to operate in: mix or unmix"
  )

  p.add_argument(
    '-f',
    '--file',
    type=str,
    required=True,
    help="source file to operate stringmu on"
  )

  p.add_argument(
    '-n',
    '--newlines',
    type=bool,
    default=False,
    help="interpret / interpolate newlines from source file"
  )

  p.add_argument(
    '-d',
    '--dashes',
    type=bool,
    default=False,
    help="interpret / interpolate dashes from source file"
  )

  p.add_argument(
    '-c',
    '--chars',
    nargs='+',
    default=[],
    help="other characters of import for stringmu to interpret / interpolate on source file"
  )

  return p.parse_args()

def nextmu(fh, mu):
  try:
    pos = fh.tell()
    mu_index = fh.buffer.peek().index(mu.encode())
    return mu_index + pos
  except Exception as err:
    return None

def seekmu(fh, mu_list):
  mus_heap = MinBinHeapTuple()

  for mu in mu_list:
    fh.seek(0)
    mu_pos = nextmu(fh, mu)

    while mu_pos is not None:
      fh.seek(mu_pos+1)
      mus_heap.insert((mu_pos, mu))
      mu_pos = nextmu(fh, mu)

  return mus_heap._heap

def dumpmap(mus_list):
  try:
    with open('stringmu.json', 'w') as fh:
      json.dump(mus_list, fh)
  except Exception as err:
    sys.stderr.write("dumpmap failed: {}\n".format(err))
    sys.exit(1)

def loadmap():
  mus_heap = MinBinHeapTuple()

  try:
    with open('stringmu.json', 'r') as fh:
      data = json.load(fh)

      for dtuple in data:
        mus_heap.insert(tuple(dtuple))
  except Exception as err:
    sys.stderr.write("loading failed: {}\n".format(err))
    sys.exit(1)

  return mus_heap

def emitmu_unmix(fh, mu_list):
  fh.seek(0)
  strbuff = fh.buffer.peek().decode()
  mu_escaped = '|'.join(mu_list)
  return re.sub(mu_escaped, '', str(strbuff))

def emitmu_mix(fh, mus_heap, total_pos):
  fh.seek(0)
  mixed = ''

  for x in range(0, total_pos-1):
    if mus_heap.peek()[0] == x:
      mus_val = mus_heap.pop()[1]
      mixed = "{}{}".format(mixed, mus_val)
    else:
      mixed = "{}{}".format(mixed, fh.read(1))

  return mixed


if __name__ == '__main__':
  args = cli_args()

  mode = args.mode
  fname = args.file
  chars = args.chars
  newlines = args.newlines
  dashes = args.dashes

  # because argparse is not imaginative enough
  if newlines is True:
    chars.append('\n')

  # because argparse is not imaginative enough
  if dashes is True:
    chars.append('-')

  if mode == "unmix":
    with open(fname, 'r') as fh:
      posl = seekmu(fh, chars)
      dumpmap(posl)
      sys.stdout.write("{}\n".format(emitmu_unmix(fh, chars)))
  elif mode == "mix":
    mus_heap = loadmap()
    total_pos = len(mus_heap._heap)

    with open(fname, 'a') as fh:
      total_pos += fh.tell()

    with open(fname, 'r') as fh:
      sys.stdout.write("{}".format(emitmu_mix(fh, mus_heap, total_pos)))
