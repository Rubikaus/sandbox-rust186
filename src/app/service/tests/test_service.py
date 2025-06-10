# Тесты запускать только в контейнере!
import pytest
import subprocess
from unittest.mock import call
from app.service.main import RustService 
from app import config, messages
from app.entities import (
    DebugData,
    TestsData,
    TestData
)
from app.service.entities import ExecuteResult
from app.service.entities import RustFile  
from app.service.exceptions import CheckerException
from app.service import exceptions


def test_execute__float_result__ok():
    """Тест для Rust: Дробная часть"""
    # arrange
    data_in = '9.08'
    code = '''
    use std::io;
    fn main() {
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let x: f64 = input.trim().parse().unwrap();
        println!("{}", x - x.floor());
    }'''
    file = RustFile(code)
    RustService._compile(file)

    # act
    exec_result = RustService._execute(
        data_in=data_in,
        file=file
    )

    # assert
    assert round(float(exec_result.result), 2) == 0.08
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_integer__ok():
    """Тест для Rust: Делёж яблок"""
    # arrange
    data_in = '6\n50'
    code = '''
    use std::io;
    fn main() {
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let nums: Vec<i32> = input.split_whitespace()
            .map(|s| s.parse().unwrap())
            .collect();
        println!("{}\n{}", nums[1]/nums[0], nums[1]%nums[0]);
    }'''
    file = RustFile(code)
    RustService._compile(file)

    # act
    exec_result = RustService._execute(
        file=file,
        data_in=data_in
    )

    # assert
    assert exec_result.result == '8\n2'
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_string__ok():
    """Тест для Rust: Удаление фрагмента"""
    # arrange
    data_in = 'In the hole in the ground there lived a hobbit'
    code = '''
    use std::io;
    fn main() {
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let s = input.trim();
        if let Some(first) = s.find('h') {
            if let Some(last) = s.rfind('h') {
                println!("{}{}", 
                    &s[..first], 
                    &s[last+1..]);
                return;
            }
        }
        println!("{}", s);
    }'''
    file = RustFile(code)
    RustService._compile(file)

    # act
    exec_result = RustService._execute(
        data_in=data_in,
        file=file
    )

    # assert
    assert exec_result.result == 'In tobbit'
    assert exec_result.error is None
    file.remove()


def test_execute__empty_result__return_none():

    # arrange
    code = 'main(){}'
    file = RustFile(code)
    RustService._compile(file)

    # act
    exec_result = RustService._execute(
        file=file
    )

    # assert
    assert exec_result.result is None
    assert exec_result.error is None
    file.remove()


def test_execute__timeout__return_error(mocker):

    # arrange
    code = (
        'main(){\n'
        '  while(1){}\n'
        '  return 0;\n'
        '}'
    )
    file = RustFile(code)
    RustService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    # act
    execute_result = RustService._execute(file=file)

    # assert
    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__deep_recursive__error(mocker):

    """ Числа Фибоначчи """

    # arrange
    code = (
        '#include<iostream>\n'
        'using namespace std;\n'
        'int fibonacci(int N){\n'
        '  if ( N == 0 ) return 0;\n'
        '  else if ( N == 1 ) return 1;\n'
        '  else\n'
        'return (fibonacci(N-1) + fibonacci(N-2));\n'
        '}\n'
        'int main(){\n'
        '  cout<<fibonacci(50)<<endl;\n'
        '  return 0;\n'
        '}\n'
    )
    file = RustFile(code)
    RustService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    # act
    execute_result = RustService._execute(file=file)

    # assert
    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__write_access__error():

    """ Тест работает только в контейнере
        т.к. там ограничены права на запись в файловую систему """

    # arrange
    code = (
        '#include <stdio.h>\n'
        '#include <unistd.h>\n'
        '#include <errno.h>\n'
        '#include<iostream>\n'
        'using namespace std;\n'
        'main(){\n'
        '  int returnval;\n'
        '  returnval = access("/app/src/", W_OK);\n'
        '  if (returnval == 0){\n'
        '    cout<<"Write allowed."<<endl;\n'
        '  } else {\n'
        '    if (errno == EACCES){\n'
        '      cout<<"Write Permission denied."<<endl;\n'
        '    } else if (errno == ENOENT){\n'
        '      cout<<"No such file or directory."<<endl;\n'
        '    } else {\n'
        '      cout<<"Write allowed."<<endl;\n'
        '    }\n'
        '  }\n'
        '  return 0;\n'
        '}'
    )
    file = RustFile(code)
    RustService._compile(file)

    # act
    exec_result = RustService._execute(file=file)

    # assert
    assert 'Write Permission denied.' in exec_result.result
    assert exec_result.error is None
    file.remove()


def test_execute__clear_error_message__ok(mocker):

    # arrange
    code = "abnabra"
    raw_error_message = (
        "/sandbox/1aab26a5-980c-4aae-9c8d-75cc78394aff.cpp:"
        " In function ‘int main()’:\n"
        "/sandbox/1aab26a5-980c-4aae-9c8d-75cc78394aff.cpp:2:5:"
        " error: ‘adqeqwd’ was not declared in this scope\n"
        "     adqeqwd\n"
        "     ^~~~~~~\n"
    )
    clear_error_message = (
        "main.cpp:"
        " In function ‘int main()’:\n"
        "main.cpp:2:5:"
        " error: ‘adqeqwd’ was not declared in this scope\n"
        "     adqeqwd\n"
        "     ^~~~~~~\n"
    )
    file = RustFile(code)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, raw_error_message)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    exec_result = RustService._execute(file=file)

    # assert
    communicate_mock.assert_called_once_with(
        input=None,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    assert exec_result.result is None
    assert exec_result.error == clear_error_message
    file.remove()


def test_execute__proc_exception__raise_exception(mocker):

    # arrange
    code = 'Some code'
    data_in = 'Some data in'
    file = RustFile(code)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception()
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    with pytest.raises(exceptions.ExecutionException) as ex:
        RustService._execute(file=file, data_in=data_in)

    # assert
    assert ex.value.message == messages.MSG_6
    communicate_mock.assert_called_once_with(
        input=data_in,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    file.remove()


def test_compile__timeout__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=subprocess.TimeoutExpired(cmd='', timeout=config.TIMEOUT)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = RustService._compile(file_mock)

    # assert
    assert error == messages.MSG_1
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__exception__raise_exception(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    with pytest.raises(exceptions.CompileException) as ex:
        RustService._compile(file_mock)

    # assert
    assert ex.value.message == messages.MSG_7
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__error__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)
    compile_error = 'some error'
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, compile_error)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = RustService._compile(file_mock)

    # assert
    assert error == compile_error
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, None)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    RustService._compile(file_mock)

    # assert
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_check__true__ok():

    # arrange
    value = 'some value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    check_result = RustService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is True


def test_check__false__ok():

    # arrange
    value = 'invalid value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    check_result = RustService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is False


def test_check__invalid_checker_func__raise_exception():

    # arrange
    checker_func = (
        'def my_checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        RustService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_2


def test_check__checker_func_no_return_instruction__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  result = right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        RustService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_3


def test_check__checker_func_return_not_bool__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return None'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        RustService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_4


def test_check__checker_func__invalid_syntax__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  include(invalid syntax here)'
        '  return True'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        RustService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_5
    assert ex.value.details == 'invalid syntax (<string>, line 1)'


def test_debug__compile_is_success__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.RustService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.RustService._execute',
        return_value=execute_result
    )
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    # act
    debug_result = RustService.debug(data)

    # assert
    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_called_once_with(
        file=file_mock,
        data_in=data.data_in
    )
    assert debug_result.result == execute_result.result
    assert debug_result.error == execute_result.error


def test_debug__compile_return_error__ok(mocker):

    # arrange
    compile_error = 'some error'
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.RustService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.RustService._execute')
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    # act
    debug_result = RustService.debug(data)

    # assert
    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    assert debug_result.result is None
    assert debug_result.error == compile_error


def test_testing__compile_is_success__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.RustService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.RustService._execute',
        return_value=execute_result
    )
    check_result = mocker.Mock()
    check_mock = mocker.patch(
        'app.service.main.RustService._check',
        return_value=check_result
    )
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = RustService.testing(data)

    # assert
    compile_mock.assert_called_once_with(file_mock)
    assert execute_mock.call_args_list == [
        call(
            file=file_mock,
            data_in=test_1.data_in
        ),
        call(
            file=file_mock,
            data_in=test_2.data_in
        )
    ]
    assert check_mock.call_args_list == [
        call(
            checker_func=data.checker,
            right_value=test_1.data_out,
            value=execute_result.result
        ),
        call(
            checker_func=data.checker,
            right_value=test_2.data_out,
            value=execute_result.result
        )
    ]
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result == execute_result.result
    assert tests_result[0].error == execute_result.error
    assert tests_result[0].ok == check_result
    assert tests_result[1].result == execute_result.result
    assert tests_result[1].error == execute_result.error
    assert tests_result[1].ok == check_result


def test_testing__compile_return_error__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(RustFile, '__new__', return_value=file_mock)
    compile_error = 'some error'
    compile_mock = mocker.patch(
        'app.service.main.RustService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.RustService._execute')
    check_mock = mocker.patch('app.service.main.RustService._check')
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = RustService.testing(data)

    # assert
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    check_mock.assert_not_called()
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result is None
    assert tests_result[0].error == compile_error
    assert tests_result[0].ok is False
    assert tests_result[1].result is None
    assert tests_result[1].error == compile_error
    assert tests_result[1].ok is False
