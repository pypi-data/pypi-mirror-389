import inspect
from fastapi import APIRouter, UploadFile, Query, File
from instaui.handlers import upload_file_handler


def create_router(router: APIRouter):
    _async_handler(router)
    _sync_handler(router)


def _async_handler(router: APIRouter):
    @router.post(upload_file_handler.ASYNC_URL)
    async def _(hkey: str = Query(...), file: UploadFile = File(...)):
        handler = _get_handler(hkey)
        if handler is None:
            raise ValueError("event handler not found")

        assert inspect.iscoroutinefunction(handler.fn), (
            "handler must be a coroutine function"
        )

        return await handler.fn(file)


def _sync_handler(router: APIRouter):
    @router.post(upload_file_handler.SYNC_URL)
    def _(hkey: str = Query(...), file: UploadFile = File(...)):
        handler = _get_handler(hkey)
        if handler is None:
            raise ValueError("event handler not found")

        return handler.fn(file)


def _get_handler(hkey: str):
    return upload_file_handler.get_handler(hkey)
