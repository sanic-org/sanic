import asyncpg
import sys
import os
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir + '/../../../')

import timeit

from sanic.response import json

print(json({"test": True}).output())

print("Running New 100,000 times")
times = 0
total_time = 0
for n in range(6):
    time = timeit.timeit('json({ "test":True }).output()', setup='from sanic.response import json', number=100000)
    print("Took {} seconds".format(time))
    total_time += time
    times += 1
print("Average: {}".format(total_time / times))

print("Running Old 100,000 times")
times = 0
total_time = 0
for n in range(6):
    time = timeit.timeit('json({ "test":True }).output_old()', setup='from sanic.response import json', number=100000)
    print("Took {} seconds".format(time))
    total_time += time
    times += 1
print("Average: {}".format(total_time / times))
