"""
Unit tests for stk.coroutines

Created on Wed Jan  4 11:37:45 2017

@author: ekroeger
"""

import time

import pytest

import stk.coroutines

TEST_KEY = "TestAsync/TestMemKey"

# PROMISE:
['future', 'isCancelRequested', 'setCanceled', 'setError', 'setValue']

# Parts of the future API
TESTED = ['value', 'then', 'andThen', 'hasError', 'wait', 'isRunning',
          'hasValue', 'isFinished', 'error', 'cancel', 'isCancelable',
          'isCanceled', 'addCallback', ]

# Not tested:
UNWANTED = ['unwrap']

def test_memory(services):
    "The code in the generator is executed."
    services.ALMemory.raiseEvent(TEST_KEY, 0)
    @stk.coroutines.async_generator
    def run_mem():
        yield services.ALMemory.raiseEvent(TEST_KEY, 1, _async=True)
    run_mem().wait()
    assert services.ALMemory.getData(TEST_KEY) == 1

def test_memory_value(services):
    "The code in the generator is executed."
    services.ALMemory.raiseEvent(TEST_KEY, 0)
    @stk.coroutines.async_generator
    def run_mem():
        yield services.ALMemory.raiseEvent(TEST_KEY, 1, _async=True)
    assert run_mem().value() == None
    assert services.ALMemory.getData(TEST_KEY) == 1

def test_then(services):
    "The callback is called when it's over."
    services.ALMemory.raiseEvent(TEST_KEY, 0)
    @stk.coroutines.async_generator
    def run_mem():
        yield services.ALMemory.raiseEvent(TEST_KEY, 1, _async=True)
    future = run_mem()
    cb_called = [False]
    def on_done(cb_future):
        assert not cb_future.hasError(False)
        cb_called[0] = True
    future.then(on_done)
    future.value()
    time.sleep(0.01) # Make sure everything is done
    assert cb_called[0]

def test_callback(services):
    "The callback is called when it's over."
    services.ALMemory.raiseEvent(TEST_KEY, 0)
    @stk.coroutines.async_generator
    def run_mem():
        yield services.ALMemory.raiseEvent(TEST_KEY, 1, _async=True)
    future = run_mem()
    cb_called = [False]
    def on_done(cb_future):
        assert not cb_future.hasError(False)
        cb_called[0] = True
    assert future.addCallback(on_done) == None
    future.value()
    time.sleep(0.01) # Make sure everything is done
    assert cb_called[0]

def test_and_then(services):
    "The callback is called when it's over."
    services.ALMemory.raiseEvent(TEST_KEY, 0)
    @stk.coroutines.async_generator
    def run_mem():
        yield services.ALMemory.raiseEvent(TEST_KEY, 1, _async=True)
    future = run_mem()
    cb_called = [False]
    def on_done(value):
        assert value == None
        cb_called[0] = True
    future.andThen(on_done)
    future.value()
    time.sleep(0.01) # Make sure everything is done
    assert cb_called[0]

def test_memory2(services):
    "The code in the generator is executed asynchronously."
    services.ALMemory.raiseEvent(TEST_KEY, 0)
    @stk.coroutines.async_generator
    def run_mem():
        yield services.ALMemory.raiseEvent(TEST_KEY, 1, _async=True)
        time.sleep(0.2)
        yield services.ALMemory.raiseEvent(TEST_KEY, 2, _async=True)
    future = run_mem()
    assert services.ALMemory.getData(TEST_KEY) == 1
    assert future.isRunning()
    assert not future.hasValue()
    assert not future.isFinished()
    future.wait() # wait
    assert future.isFinished()
    assert not future.isRunning()
    assert future.hasValue()
    assert services.ALMemory.getData(TEST_KEY) == 2

def test_exception(qiapp):
    "Exceptions raised in the generator are propagated."
    services = stk.services.ServiceCache(qiapp.session)
    @stk.coroutines.async_generator
    def func():
        assert False, "Nope"
        yield services.ALMemory.raiseEvent(TEST_KEY, 0, _async=True)
    with pytest.raises(AssertionError):
        func().value()

def test_wrong_key(qiapp):
    "An exception is raised when the ALMemory key doesn't exist."
    services = stk.services.ServiceCache(qiapp.session)
    @stk.coroutines.async_generator
    def func():
        yield services.ALMemory.getData("TestAsync/MemKeyThatDoesntExist",
                                        _async=True)
    with pytest.raises(RuntimeError):
        func().value()

def test_wrong_function(qiapp):
    "An exception is raised when the function doesn't exist."
    services = stk.services.ServiceCache(qiapp.session)
    @stk.coroutines.async_generator
    def func():
        yield services.ALMemory.doesntExist(_async=True)
    with pytest.raises(AttributeError):
        func().value()


def test_exception_in_future(qiapp):
    "Exceptions raised in the generator are propagated."
    services = stk.services.ServiceCache(qiapp.session)
    @stk.coroutines.async_generator
    def func():
        assert False, "Nope"
        yield services.ALMemory.raiseEvent(TEST_KEY, 0, _async=True)
    future = func()
    cb_called = [False]
    def on_done(cb_future):
        assert cb_future.hasError()
        cb_called[0] = True
    future.then(on_done)
    try:
        future.value()
    except AssertionError:
        pass
    assert future.hasError()
    assert "assert" in future.error()
    assert future.isFinished()
    assert not future.hasValue()
    time.sleep(0.01)
    assert cb_called[0]

def test_cancel(services):
    "The code in the generator is executed asynchronously."
    services.ALMemory.raiseEvent(TEST_KEY, 0)
    @stk.coroutines.async_generator
    def run_mem():
        yield services.ALMemory.raiseEvent(TEST_KEY, 1, _async=True)
        time.sleep(0.3)
        # Dummy, unfortunately necessary.
        yield services.ALMemory.getData(TEST_KEY, _async=True)
        yield services.ALMemory.raiseEvent(TEST_KEY, 2, _async=True)
    future = run_mem()
    time.sleep(0.1)
    assert future.isCancelable()
    assert not future.isCanceled()
    future.cancel()
    assert future.isCanceled()
    assert not future.isRunning()
    assert services.ALMemory.getData(TEST_KEY) == 1
    time.sleep(0.3)
    assert services.ALMemory.getData(TEST_KEY) == 1

def test_return(services):
    "functions can return a value with coroutines.Return."
    @stk.coroutines.async_generator
    def run_return():
        yield stk.coroutines.Return(42)
    assert run_return().value() == 42

def test_return_stops_exec(services):
    "coroutines.Return acts like normal return, and stops execution."
    state = ["NOT_STARTED"]
    @stk.coroutines.async_generator
    def run_return():
        state[0] = "STARTED"
        yield stk.coroutines.Return(42)
        state[0] = "WENT_TOO_FAR"
    assert run_return().value() == 42
    assert state[0] == "STARTED"
    time.sleep(0.1)
    assert state[0] == "STARTED"

def test_yield_list(services):
    "A list of futures works like the future of a list."
    @stk.coroutines.async_generator
    def run_a():
        yield stk.coroutines.Return("A")
    @stk.coroutines.async_generator
    def run_b():
        yield stk.coroutines.Return("B")
    @stk.coroutines.async_generator
    def run_yield_list():
        values = yield [run_a(), run_b()]
        assert values == ["A", "B"]
        yield stk.coroutines.Return("OK")
    assert run_yield_list().value() == "OK"

def test_yield_tuple(services):
    "A tuple of futures works like the future of a tuple."
    @stk.coroutines.async_generator
    def run_a():
        yield stk.coroutines.Return("A")
    @stk.coroutines.async_generator
    def run_b():
        yield stk.coroutines.Return("B")
    @stk.coroutines.async_generator
    def run_yield_list():
        values = yield (run_a(), run_b())
        assert values == ("A", "B")
        yield stk.coroutines.Return("OK")
    assert run_yield_list().value() == "OK"

#if __name__ == "__main__":
#    pytest.main(['--qiurl', '10.0.204.46'])

