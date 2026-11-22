"""Global error handling: every error leaves the API as {"detail": "..."}.

FastAPI already returns {"detail": ...} for HTTPException (401, 404, 409, 503 ...) and for
validation errors (422), and those stay exactly as they are. This adds a safety net for
UNEXPECTED errors: the full error is logged on the server, and the client only gets a short,
generic message - never a stack trace, SQL, file paths or secrets.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("app.errors")

GENERIC_MESSAGE = "Something went wrong on our side. Please try again."
DATABASE_MESSAGE = "The database is temporarily unavailable. Please try again in a moment."


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logger.error("Database error on %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": DATABASE_MESSAGE})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": GENERIC_MESSAGE})
