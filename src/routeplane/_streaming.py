"""Thin wrappers that pair an OpenAI stream with its gateway metadata.

The OpenAI SDK's ``Stream`` exposes chunks but not the response headers, and the
``x-routeplane-*`` headers arrive on the response *before* the first chunk. These
wrappers capture that header snapshot as a :class:`RouteplaneMeta` while
delegating iteration straight through to the underlying stream.
"""

from __future__ import annotations

from typing import AsyncIterator, Generic, Iterator, Mapping, TypeVar

from .meta import RouteplaneMeta

__all__ = ["RouteplaneStream", "AsyncRouteplaneStream"]

_T = TypeVar("_T")


class RouteplaneStream(Generic[_T]):
    """Iterable wrapper over a sync OpenAI ``Stream`` that also carries ``meta``.

    Use it exactly like the underlying stream::

        stream = client.stream_with_meta(model="gpt-4o", messages=[...])
        print(stream.meta.provider)  # available before the first chunk
        for chunk in stream:
            ...
    """

    meta: RouteplaneMeta

    def __init__(self, stream: Iterator[_T], headers: Mapping[str, str]) -> None:
        self._stream = stream
        self.meta = RouteplaneMeta.from_headers(headers)

    def __iter__(self) -> Iterator[_T]:
        return self._stream

    def __next__(self) -> _T:
        return next(self._stream)

    def __enter__(self) -> "RouteplaneStream[_T]":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        close = getattr(self._stream, "close", None)
        if callable(close):
            close()


class AsyncRouteplaneStream(Generic[_T]):
    """Async twin of :class:`RouteplaneStream` for ``AsyncRouteplane``.

    ::

        stream = await client.stream_with_meta(model="gpt-4o", messages=[...])
        print(stream.meta.provider)
        async for chunk in stream:
            ...
    """

    meta: RouteplaneMeta

    def __init__(self, stream: AsyncIterator[_T], headers: Mapping[str, str]) -> None:
        self._stream = stream
        self.meta = RouteplaneMeta.from_headers(headers)

    def __aiter__(self) -> AsyncIterator[_T]:
        return self._stream

    async def __anext__(self) -> _T:
        return await self._stream.__anext__()

    async def __aenter__(self) -> "AsyncRouteplaneStream[_T]":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        close = getattr(self._stream, "close", None)
        if callable(close):
            await close()
