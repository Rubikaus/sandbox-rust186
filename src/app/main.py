from typing import Union
from flask import (
    Flask,
    request,
    render_template,
    abort
)
from marshmallow import ValidationError
from app.service.main import RustService
from app.schema import (
    DebugSchema,
    TestsSchema,
    BadRequestSchema,
    ServiceExceptionSchema,
)
from app.service.exceptions import ServiceException


def create_app():

    app = Flask(__name__)

    @app.errorhandler(400)
    def bad_request_handler(ex: ValidationError):
        return BadRequestSchema().dump(ex), 400

    @app.errorhandler(500)
    def bad_request_handler(ex: ServiceException):
        return ServiceExceptionSchema().dump(ex), 500

    @app.route('/', methods=['get'])
    def index():
        return render_template("index.html")

    @app.route('/debug/', methods=['post'])
    def debug():
        schema = DebugSchema()
        try:
            data = RustService.debug(
                schema.load(request.get_json())
            )
        except ValidationError as ex:
            abort(400, ex)
        except ServiceException as ex:
            abort(500, ex)
        else:
            return schema.dump(data)

    @app.route('/testing/', methods=['post'])
    def testing():
        schema = TestsSchema()
        try:
            data = RustService.testing(
                schema.load(request.get_json())
            )
        except ValidationError as ex:
            abort(400, ex)
        except ServiceException as ex:
            abort(500, ex)
        else:
            return schema.dump(data)
    return app


app = create_app()
