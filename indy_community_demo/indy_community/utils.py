import asyncio
import random
import string


######################################################################
# a few random utilities
######################################################################

def random_int(low, high):
    return random.randint(low, high)

def random_alpha_string(length, contains_spaces=False):
    if contains_spaces:
        chars = string.ascii_uppercase + ' '
    else:
        chars = string.ascii_uppercase
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

def random_numeric_string(length):
    chars = string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

def random_an_string(length, contains_spaces=False):
    if contains_spaces:
        chars = string.ascii_uppercase + string.digits + ' '
    else:
        chars = string.ascii_uppercase + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

def random_schema_version():
    version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
    return version


######################################################################
# coroutine utilities
######################################################################

def run_coroutine(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine())
    finally:
        loop.close()

def run_coroutine_with_args(coroutine, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine(*args))
    finally:
        loop.close()

def run_coroutine_with_kwargs(coroutine, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine(*args, **kwargs))
    finally:
        loop.close()

