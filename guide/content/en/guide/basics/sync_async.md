# Sync and Async in Sanic

Sanic is an **asynchronous** framework - it is designed to be responsive to requests, which allows it to theoretically serve more requests, more quickly, than a synchronous framework. It shares this functionality with other asynchronous frameworks like [starlette](https://www.starlette.io/) and a more full-featured, batteries included framework that is in the public spotlight, [FastAPI](https://fastapi.tiangolo.com/) (which uses starlette under the hood).

There are preventable situations where this is not the case. Using synchronous functions in asynchronous code is the biggest hurdle for many Sanic adopters.

## Introduction
Understanding asynchronicity is sometimes baffling even to experienced developers. The point of this mini-guide is to help understand what happens in Sanic, why certain things might not work the way you expect, and will help walk you through some of the impact of synchronous and asynchronous code may have on your Sanic application.

There are many guides to async/await available as of this writing (Dec 2023) so we will not cover everything specifically, instead exploring and reviewing what happens inside Sanic when you use non-blocking (asynchronous) and blocking (synchronous) code.

## Synchronous Execution
Let’s start with as simple an explanation as we can produce and an example. Most python code is synchronous, that is to say when something happens, it must be done in order and must complete before the python interpreter can move on. This is called **blocking** because the process is **blocked** while it waits for each statement to finish.

Our first example, below, is a standard program. The ***execution flow*** can be understood by simply reading the code.

```py test1.py
#!/usr/bin/env python3.11
import time
from random import randrange

def sync_print(text: str) -> None:
    rand_wait: int = randrange(0,5)
    time.sleep(rand_wait)
    print(f'{text} ({rand_wait}s)')

def main() -> None:
    my_name: str = 'Sanic'
    sync_print('I go first')
    sync_print(f'Hello {my_name}, I run second')
    sync_print('I go third')

main()
```

In the above example, we assign a variable (*my_name*), then we print three lines of text by calling a function. The function, *sync_print* waits 0-5 seconds, then prints the text along with how long the wait was.

The python interpreter runs all four statements in order, and will do so every single time. To change the order of the output simply change the order of the statements.

It produces the following example output:
```sh
I go first (0s)
Hello Sanic, I run second (4s)
I go third (2s)
```

So changing the order of the statements as is done below changes the output:

```py test2.py
#!/usr/bin/env python3.11
import time
from random import randrange

def sync_print(text: str) -> None:
    rand_wait: int = randrange(0,5)
    time.sleep(rand_wait)
    print(f{text} ({rand_wait}s))

def main() -> None:
    sync_print('I go first')
    sync_print(f'Hello {my_name}, I run second')
    my_name: str = 'Sanic'
    sync_print('I go third')

main()
```

The above example is a good one because it illustrates what happens when something is run before the interpreter has had a chance to execute the statements to make it fully functional. The output is below:

```sh
I go first (4s)
Traceback (most recent call last):
  File "/Users/ssadowski/tmp/test2.py", line 16, in <module>
    main()
  File "/Users/ssadowski/tmp/test2.py", line 12, in main
    sync_print(f'Hello {my_name}, I run second')
                        ^^^^^^^
UnboundLocalError: cannot access local variable 'my_name' where it is not associated with a value
```
In this case, the variable *my_name* is defined ***after*** python wants to use it, and an exception - a *UnboundLocalError* - occurs. In the first example, there was no exception because the variable *my_name* was defined before the statement that referenced it.

## Asynchronous Execution

Asynchronous elements must be scheduled. To manage this, python creates a constantly running background loop called an event loop. This works very well for things that need to keep running while other parts of a program are also running.

To achieve this in python, we define a ***coroutine***, ***task***, or a ***future***, which are referred to as ***awaitables*** For this guide, we will only focus on coroutines.

Scheduled code is considered **non-blocking**, because the process should not wait for an awaitable to finish executing.

To illustrate this, the simplest possible example is used below:

```py test3.py
#!/usr/bin/env python3.11
import asyncio
from random import randrange

async def async_print(text: str) -> None:
    rand_wait: int = randrange(0,5)
    await asyncio.sleep(rand_wait)
    print(text)

async def main() -> None:
    my_name: str = 'Sanic'
    await async_print('I go first')
    await async_print(f'Hello {my_name}, I run second')
    await async_print('I go third')

asyncio.run(main())
```

.. tip:: Note

    💡 Like the use of *async* and *await*, some of the complexity here is deliberately avoided for the sake of a higher level understanding.

Immediately there's much more going on here - we are importing the **asyncio** standard library and there are two new keywords in play, **async** and **await**. It should be noted that asynchronous execution has come quite far since it was first introduced, and much more is done under the hood for the sake of readability and reusability, but in my opinion it masks the inner workings of asynchronous code and prevents people from understanding why it works as well as it does.

In the example, instead of calling print directly, we use the async keyword to create a *coroutine* called **async_print** that takes a single text argument.

Also in the example **main** is now a coroutine as well. This is because coroutines can easily schedule other coroutines and call regular functions, but regular functions cannot easily schedule coroutines.

.. tip:: Note

    💡 It is not impossible for regular functions to schedule coroutines, but it is beyond the scope of this guide.


