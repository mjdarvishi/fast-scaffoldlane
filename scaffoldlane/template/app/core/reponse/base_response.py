from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


class CustomResponse:
    @staticmethod
    def success(message, status_code=200, body=None):
        response_body = {"message": message}
        if body is not None:
            response_body["body"] = body
        return JSONResponse(status_code=status_code, content=jsonable_encoder(response_body))

    @staticmethod
    def success_paginated(
        message, body, total_pages, page, page_size, total_count=None, status_code=200
    ):
        response_body = {"message": message}
        response_body["body"] = body
        response_body["total_pages"] = total_pages
        response_body["page"] = page
        response_body["page_size"] = page_size
        response_body["total_count"] = total_count
        return JSONResponse(status_code=status_code, content=jsonable_encoder(response_body))

    @staticmethod
    def failed(message, status_code=400, body=None):
        response_body = {"message": message}
        if body:
            response_body["body"] = body
        return JSONResponse(status_code=status_code, content=jsonable_encoder(response_body))

    @staticmethod
    def internal_server_error(status_code=503, body=None):
        response_body = {"message": "internal server error"}
        if body:
            response_body["body"] = body
        return JSONResponse(status_code=status_code, content=jsonable_encoder(response_body))
