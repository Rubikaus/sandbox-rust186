from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    make_response
)
from marshmallow import ValidationError
from app.service.main import RustService
from app.schema import (
    DebugSchema,
    TestsSchema,
    ServiceExceptionSchema
)
from app.service.exceptions import ServiceException


def create_app():
    app = Flask(__name__)

    @app.errorhandler(ValidationError)
    def validation_error_handler(ex: ValidationError):
        return jsonify(error="Validation error", details=ex.messages), 400

    @app.errorhandler(ServiceException)
    def service_exception_handler(ex: ServiceException):
        return jsonify({'error': ex.message, 'details': ex.details}), 500

    @app.errorhandler(Exception)
    def handle_all_exceptions(ex):
        return jsonify({'error': str(ex), 'details': 'Internal Server Error'}), 500

    @app.route('/', methods=['get'])
    def index():
        return render_template("index.html")

    @app.route('/debug/', methods=['post'])
    def debug():
        schema = DebugSchema()
        try:
            data = RustService.debug(schema.load(request.get_json()))
        except ValidationError as ex:
            raise ex
        except ServiceException as ex:
            return make_response(jsonify({'error': ex.message, 'details': ex.details}), 500)
        else:
            return schema.dump(data)

    @app.route('/testing/', methods=['post'])
    def testing():
        schema = TestsSchema()
        try:
            data = RustService.testing(schema.load(request.get_json()))
        except ValidationError as ex:
            raise ex
        except ServiceException as ex:
            return make_response(jsonify({'error': ex.message, 'details': ex.details}), 500)
        else:
            return schema.dump(data)

    return app

app = create_app()
