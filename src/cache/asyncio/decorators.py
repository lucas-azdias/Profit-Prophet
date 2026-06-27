# Copyright (C) 2026 Lucas Dias
#
# Portions Copyright (C) 2026 James Ward
# Source: https://github.com/imnotjames/cachetools-async/blob/53d453441dac736b16ec549ee4dd50453c9669c9/src/cachetools_async/decorators.py
# License: MIT (See LICENSE file for details)

"""Asynchronous caching utilities for coroutines and methods.

This module provides async-compatible decorator patterns similar to
`cachetools`, designed to store and reuse `Future` instances to prevent
duplicate inflight executions (cache stampede) and cache completed
results.
"""

import asyncio
import contextlib
import functools
import inspect
import typing

import cachetools.keys

if typing.TYPE_CHECKING:
    import collections.abc


# IGNORE: The bigger amount of arguments is necessary
# for simpler structure of code.
def __async_cache_get[K, **P, R](  # noqa: PLR0913
    *,
    cache: collections.abc.MutableMapping[K, tuple[asyncio.Task[R], asyncio.Future[R]]],
    key: K,
    fn: collections.abc.Callable[P, collections.abc.Coroutine[typing.Any, typing.Any, R]],
    args: tuple[typing.Any, ...],
    kwargs: dict[str, typing.Any],
    cache_exceptions: bool,
) -> tuple[asyncio.Task[R], asyncio.Future[R]]:
    with contextlib.suppress(KeyError):
        # If alrady exists a cached version, return it
        return cache[key]

    # Creates a new task for this call
    loop = asyncio.get_event_loop()
    task = loop.create_task(fn(*args, **kwargs))
    future: asyncio.Future[R] = loop.create_future()

    # `done` callback for when future is concluded
    def done(t: asyncio.Task[R]) -> None:
        # Removes cancelled tasks from the cache
        if t.cancelled():
            cache.pop(key, None)
            future.cancel()
            return

        # Optionally discards failed tasks to allow future retries
        exception = t.exception()
        if exception is not None:
            if not cache_exceptions:
                cache.pop(key, None)

            # Propagates the exception
            future.set_exception(exception)
            return

        # Stores the successful result in the shared future
        future.set_result(t.result())

    # Adds `done` callback of future to task
    task.add_done_callback(done)

    # Returns the cached value
    with contextlib.suppress(ValueError):
        cache[key] = (task, future)

    return task, future


class __AsyncCacheCallable[**P, R](typing.Protocol):
    """Async callable with cache metadata attached."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> collections.abc.Awaitable[R]:
        """Invoke the wrapped asynchronous callable.

        Args:
            *args (P.args):
                Positional arguments forwarded to the wrapped callable.

            **kwargs (P.kwargs):
                Keyword arguments forwarded to the wrapped callable.

        Returns:
            Awaitable[R]:
                An awaitable that resolves to the wrapped callable's result.

        """
        raise NotImplementedError


class __AsyncCachedCallable[K, **P, R](__AsyncCacheCallable[P, R]):
    """Async callable with cache metadata attached for functions."""

    cache: collections.abc.MutableMapping[K, tuple[asyncio.Task[R], asyncio.Future[R]]] | None
    cache_key: collections.abc.Callable[..., K]
    cache_lock: contextlib.AbstractContextManager[typing.Any] | None
    cache_clear: collections.abc.Callable[[], None]
    cache_info: bool | None


class __AsyncCachedMethodCallable[K, **P, R](__AsyncCacheCallable[P, R]):
    """Async callable with cache metadata attached for methods."""

    cache: collections.abc.Callable[
        [typing.Any],
        collections.abc.MutableMapping[K, tuple[asyncio.Task[R], asyncio.Future[R]]] | None,
    ]
    cache_key: collections.abc.Callable[..., K]
    cache_lock: contextlib.AbstractContextManager[typing.Any] | None
    cache_clear: collections.abc.Callable[[typing.Any], None]

    @typing.overload
    def __get__(self, instance: None, owner: type | None) -> typing.Self: ...

    @typing.overload
    def __get__[**P_New](
        self,
        # IGNORE: Type `Any` was used as it must The descriptor
        # is accessed from an instance of the class containing
        # the decorated method which must be any arbitrary
        # user-defined type.
        instance: typing.Any,  # noqa: ANN401
        owner: type | None,
    ) -> __AsyncCacheCallable[P_New, R]: ...

    def __get__(self, instance: typing.Any, owner: type | None) -> typing.Any:
        if instance is None:
            return self
        # Binds the method to the instance at runtime
        bound = typing.cast(
            "__AsyncCachedMethodCallable[K, P, R]",
            functools.partial(self.__call__, instance),
        )

        # Mirrors the cache attributes to the bound wrapper
        bound.cache = self.cache
        bound.cache_key = self.cache_key
        bound.cache_lock = self.cache_lock
        bound.cache_clear = self.cache_clear

        return bound


def async_cached[K, **P, R](
    cache: collections.abc.MutableMapping[K, tuple[asyncio.Task[R], asyncio.Future[R]]] | None,
    key: collections.abc.Callable[..., K] = cachetools.keys.hashkey,
    lock: contextlib.AbstractContextManager[typing.Any] | None = None,
    *,
    info: bool = False,
    cache_exceptions: bool = True,
) -> collections.abc.Callable[
    [collections.abc.Callable[P, collections.abc.Awaitable[R]]],
    __AsyncCachedCallable[K, P, R],
]:
    """Decorate caching async function results using asyncio `Future`.

    This decorator stores `Future` objects in a shared mapping keyed by
    a deterministic key function. It ensures that concurrent callers
    awaiting the same computation will reuse the same in-progress `Future`,
    preventing duplicate execution (cache stampede protection).

    Args:
        cache (MutableMapping[K, tuple[Task[R], Future[R]]] | None):
            Mutable mapping used to store tasks and futures. If None, caching is disabled.

        key (Callable[..., K]):
            Callable used to compute cache key from function arguments.
            Defaults to `hashkey`.

        lock (AbstractContextManager[Any] | None):
            Optional lock context manager. Not supported in this implementation.

        info (bool):
            If True, raises NotImplementedError (not supported).

        cache_exceptions (bool):
            Whether futures that complete with an exception should remain
            cached. If False, failed futures are removed from the cache,
            allowing subsequent calls with the same key to retry the
            computation. Defaults to True.

    Returns:
        Callable[[Callable[P, Awaitable[R]]], __AsyncCachedCallable[K, P, R]]:
            A decorator that wraps an async function with caching behavior.

    Raises:
        NotImplementedError:
            If `info` or `lock` are provided.

    """
    if info:
        msg = "`info` is not supported"
        raise NotImplementedError(msg)

    if lock is not None:
        msg = "`lock` is not supported"
        raise NotImplementedError(msg)

    def decorator(
        fn: collections.abc.Callable[P, collections.abc.Awaitable[R]],
    ) -> __AsyncCachedCallable[K, P, R]:
        if not inspect.iscoroutinefunction(fn):
            msg = f"Expected 'Coroutine' function, got {fn}"
            raise TypeError(msg)

        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if cache is None:
                return await fn(*args, **kwargs)

            # Generates key
            generated_key = key(*args, **kwargs)

            task, future = __async_cache_get(
                cache=cache,
                key=generated_key,
                fn=fn,
                args=args,
                kwargs=kwargs,
                cache_exceptions=cache_exceptions,
            )

            try:
                return await future
            except asyncio.CancelledError:
                # Evicts from cache instantly
                cache.pop(generated_key, None)

                # Directly terminates the underlying task loop execution
                if not task.done():
                    task.cancel()

                raise

        wrapped = typing.cast(
            "__AsyncCachedCallable[K, P, R]",
            functools.update_wrapper(wrapper, fn),
        )

        wrapped.cache = cache
        wrapped.cache_key = key
        wrapped.cache_lock = None
        wrapped.cache_clear = lambda: cache.clear() if cache is not None else None
        wrapped.cache_info = None

        return wrapped

    return decorator


def async_cachedmethod[K, **P, R](
    cache: collections.abc.Callable[
        [typing.Any],
        collections.abc.MutableMapping[K, tuple[asyncio.Task[R], asyncio.Future[R]]] | None,
    ],
    key: collections.abc.Callable[..., K] = cachetools.keys.methodkey,
    lock: collections.abc.Callable[[typing.Any], contextlib.AbstractContextManager[typing.Any]]
    | None = None,
    *,
    cache_exceptions: bool = True,
) -> collections.abc.Callable[
    [collections.abc.Callable[P, collections.abc.Awaitable[R]]],
    __AsyncCachedMethodCallable[K, P, R],
]:
    """Decorate caching async instance/class methods.

    This is similar to `cached`, but the cache is resolved dynamically
    per instance (or class) via the provided cache function.

    It is primarily used for memoizing async methods where cache storage
    is attached to `self` or another runtime context.

    Args:
        cache (Callable[[Any], MutableMapping[K, tuple[Task[R], Future[R]]] | None]):
            Callable that returns a `MutableMapping` for the given instance,
            or None to disable caching for that instance.

        key (Callable[..., K]):
            Function used to compute cache keys. Defaults to `methodkey`.

        lock (Callable[[Any], AbstractContextManager[Any]] | None):
            Optional lock context manager factory. Not supported.

        cache_exceptions (bool):
            Whether futures that complete with an exception should remain
            cached. If False, failed futures are removed from the cache,
            allowing subsequent calls with the same key to retry the
            computation. Defaults to True.

    Returns:
        Callable[[Callable[P, Awaitable[R]]], __AsyncCachedMethodCallable[K, P, R]]:
            A decorator that wraps an async method with caching behavior.

    Raises:
        NotImplementedError:
            If `lock` is provided.

    """
    if lock is not None:
        msg = "`lock` is not supported"
        raise NotImplementedError(msg)

    def decorator(
        fn: collections.abc.Callable[P, collections.abc.Awaitable[R]],
    ) -> __AsyncCachedMethodCallable[K, P, R]:
        if not inspect.iscoroutinefunction(fn):
            msg = f"Expected Coroutine function, got {fn}"
            raise TypeError(msg)

        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Safely capture 'self' if args are passed
            self_obj = args[0] if args else None
            self_cache = cache(self_obj)

            if self_cache is None:
                return await fn(*args, **kwargs)

            # Generates key
            generated_key = key(*args, **kwargs)

            task, future = __async_cache_get(
                cache=self_cache,
                key=generated_key,
                fn=fn,
                args=args,
                kwargs=kwargs,
                cache_exceptions=cache_exceptions,
            )

            try:
                return await future
            except asyncio.CancelledError:
                # Evicts from cache instantly
                self_cache.pop(generated_key, None)

                # Directly terminates the underlying task loop execution
                if not task.done():
                    task.cancel()

                raise

        wrapped = typing.cast(
            "__AsyncCachedMethodCallable[K, P, R]",
            functools.update_wrapper(wrapper, fn),
        )

        wrapped.cache = cache
        wrapped.cache_key = key
        wrapped.cache_lock = None
        wrapped.cache_clear = lambda self_obj: (
            self_cache.clear() if (self_cache := cache(self_obj)) is not None else None
        )

        return wrapped

    return decorator
