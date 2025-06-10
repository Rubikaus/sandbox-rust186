from app.entities import (
    DebugData,
    TestsData,
    TestData
)
from app.service.exceptions import ServiceException


def test_debug__ok(client, mocker):

    request_data = {
        'code': 'some code',
        'data_in': 'some input'
    }

    serialized_data = DebugData(
        code='some code',
        data_in='some input'
    )
    debug_result = DebugData(
        result='some result',
        error='some error'
    )
    debug_mock = mocker.patch(
        'app.service.main.RustService.debug',
        return_value=debug_result
    )

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 200
    assert response.json['result'] == debug_result.result
    assert response.json['error'] == debug_result.error
    debug_mock.assert_called_once_with(serialized_data)


def test_debug__not_error__ok(client, mocker):

    request_data = {
        'code': 'some code',
        'data_in': 'some input'
    }

    serialized_data = DebugData(
        code='some code',
        data_in='some input'
    )
    debug_result = DebugData(
        result='some result',
        error=None
    )
    debug_mock = mocker.patch(
        'app.service.main.RustService.debug',
        return_value=debug_result
    )

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 200
    assert response.json['result'] == debug_result.result
    assert response.json['error'] is None
    debug_mock.assert_called_once_with(serialized_data)


def test_debug__not_result__ok(client, mocker):

    request_data = {
        'code': 'some code',
        'data_in': 'some input'
    }

    serialized_data = DebugData(
        code='some code',
        data_in='some input'
    )
    debug_result = DebugData(
        result=None,
        error='some error'
    )
    debug_mock = mocker.patch(
        'app.service.main.RustService.debug',
        return_value=debug_result
    )

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 200
    assert response.json['result'] is None
    assert response.json['error'] == debug_result.error
    debug_mock.assert_called_once_with(serialized_data)


def test_debug__service_exception__internal_error(client, mocker):

    request_data = {
        'code': 'some code',
        'data_in': 'some input'
    }
    service_ex = ServiceException(
        message='some message',
        details='some details'
    )

    mocker.patch(
        'app.service.main.RustService.debug',
        side_effect=service_ex
    )

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 500
    assert response.json['error'] == service_ex.message
    assert response.json['details'] == service_ex.details


def test_debug__validation_error__bad_request(client, mocker):

    request_data = {
        'data_in': 'some input'
    }
    service_mock = mocker.patch('app.service.main.RustService.debug')

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 400
    assert response.json['error'] == 'Validation error'
    assert response.json['details'] == {
        'code': ['Missing data for required field.']
    }
    service_mock.assert_not_called()


def test_testing__ok(client, mocker):

    request_data = {
        'code': 'some code',
        'checker': 'some func',
        'tests': [
            {
                'data_in': 'some test 1 input',
                'data_out': 'some test 1 out'
            },
            {
                'data_in': 'some test 2 input',
                'data_out': 'some test 2 out'
            }
        ]
    }

    serialized_data = TestsData(
        code='some code',
        checker='some func',
        tests=[
            TestData(
                data_in='some test 1 input',
                data_out='some test 1 out'
            ),
            TestData(
                data_in='some test 2 input',
                data_out='some test 2 out'
            )
        ]
    )
    testing_result = TestsData(
        ok=True,
        num=2,
        num_ok=2,
        tests=[
            TestData(
                result='some result 1',
                error='some error 1',
                ok=True
            ),
            TestData(
                result='some result 2',
                error='some error 2',
                ok=False
            )
        ]
    )
    testing_mock = mocker.patch(
        'app.service.main.RustService.testing',
        return_value=testing_result
    )

    response = client.post('/testing/', json=request_data)

    assert response.status_code == 200
    assert response.json['ok'] == testing_result.ok
    assert response.json['num'] == testing_result.num
    assert response.json['num_ok'] == testing_result.num_ok
    assert response.json['tests'][0]['result'] == 'some result 1'
    assert response.json['tests'][0]['error'] == 'some error 1'
    assert response.json['tests'][0]['ok'] is True
    assert response.json['tests'][1]['result'] == 'some result 2'
    assert response.json['tests'][1]['error'] == 'some error 2'
    assert response.json['tests'][1]['ok'] is False
    testing_mock.assert_called_once_with(serialized_data)


def test_testing__not_test_result__ok(client, mocker):

    request_data = {
        'code': 'some code',
        'checker': 'some func',
        'tests': [
            {
                'data_in': 'some test 1 input',
                'data_out': 'some test 1 out'
            }
        ]
    }

    serialized_data = TestsData(
        code='some code',
        checker='some func',
        tests=[
            TestData(
                data_in='some test 1 input',
                data_out='some test 1 out'
            )
        ]
    )
    testing_result = TestsData(
        ok=True,
        num=1,
        num_ok=0,
        tests=[
            TestData(
                result=None,
                error='some error 1',
                ok=False
            )
        ]
    )
    testing_mock = mocker.patch(
        'app.service.main.RustService.testing',
        return_value=testing_result
    )

    response = client.post('/testing/', json=request_data)

    assert response.status_code == 200
    assert response.json['ok'] == testing_result.ok
    assert response.json['num'] == testing_result.num
    assert response.json['num_ok'] == testing_result.num_ok
    assert response.json['tests'][0]['result'] is None
    assert response.json['tests'][0]['error'] == 'some error 1'
    assert response.json['tests'][0]['ok'] is False
    testing_mock.assert_called_once_with(serialized_data)


def test_testing__not_test_error__ok(client, mocker):

    request_data = {
        'code': 'some code',
        'checker': 'some func',
        'tests': [
            {
                'data_in': 'some test 1 input',
                'data_out': 'some test 1 out'
            }
        ]
    }

    serialized_data = TestsData(
        code='some code',
        checker='some func',
        tests=[
            TestData(
                data_in='some test 1 input',
                data_out='some test 1 out'
            )
        ]
    )
    testing_result = TestsData(
        ok=True,
        num=1,
        num_ok=1,
        tests=[
            TestData(
                result='some result',
                error=None,
                ok=True
            )
        ]
    )
    testing_mock = mocker.patch(
        'app.service.main.RustService.testing',
        return_value=testing_result
    )

    response = client.post('/testing/', json=request_data)

    assert response.status_code == 200
    assert response.json['ok'] == testing_result.ok
    assert response.json['num'] == testing_result.num
    assert response.json['num_ok'] == testing_result.num_ok
    assert response.json['tests'][0]['result'] == 'some result'
    assert response.json['tests'][0]['error'] is None
    assert response.json['tests'][0]['ok'] is True
    testing_mock.assert_called_once_with(serialized_data)


def test_testing__service_exception__internal_error(client, mocker):

    request_data = {
        'code': 'some code',
        'checker': 'some func',
        'tests': [
            {
                'data_in': 'some test 1 input',
                'data_out': 'some test 1 out'
            },
            {
                'data_in': 'some test 2 input',
                'data_out': 'some test 2 out'
            }
        ]
    }
    service_ex = ServiceException(
        message='some message',
        details='some details'
    )

    mocker.patch(
        'app.service.main.RustService.testing',
        side_effect=service_ex
    )

    response = client.post('/testing/', json=request_data)

    assert response.status_code == 500
    assert response.json['error'] == service_ex.message
    assert response.json['details'] == service_ex.details


def test_testing__validation_error__bad_request(client, mocker):

    request_data = {
        'code': 'some code',
        'tests': [
            {
                'data_in': 'some test input',
                'data_out': 'some test out'
            }
        ]
    }

    service_mock = mocker.patch('app.service.main.RustService.testing')

    response = client.post('/testing/', json=request_data)

    assert response.status_code == 400
    assert response.json['error'] == 'Validation error'
    assert response.json['details'] == {
        'checker': ['Missing data for required field.']
    }
    service_mock.assert_not_called()

