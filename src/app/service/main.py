import os
import re
import subprocess
from typing import Optional

from app import config, messages
from app.entities import DebugData, TestsData
from app.service import exceptions
from app.service.entities import ExecuteResult, RustFile
from app.utils import clean_str, clean_error


class RustService:
    @classmethod
    def _preexec_fn(cls):
        def change_process_user():
            # Drop privileges inside the sandbox
            os.setgid(config.SANDBOX_USER_UID)
            os.setuid(config.SANDBOX_USER_UID)
        return change_process_user

    @classmethod
    def _compile(cls, file: RustFile) -> Optional[str]:
        proc = subprocess.Popen(
            ['cargo', 'build', '--release', '--quiet'],
            cwd=file.project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            _, error = proc.communicate(timeout=config.TIMEOUT)
        except subprocess.TimeoutExpired:
            error = messages.MSG_RUST_COMPILE_TIMEOUT
        except Exception as ex:
            raise exceptions.CompileException(details=str(ex))
        finally:
            proc.kill()

        if proc.returncode == 0:
            return None
        return clean_error(error)

    @classmethod
    def _execute(
        cls,
        file: RustFile,
        data_in: Optional[str] = None
    ) -> ExecuteResult:
        env = os.environ.copy()
        env["RUST_BACKTRACE"] = "0"

        proc = subprocess.Popen(
            [file.filepath_out],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=cls._preexec_fn,
            env=env,
            text=True
        )
        try:
            result, error = proc.communicate(
                input=data_in,
                timeout=config.TIMEOUT
            )
        except subprocess.TimeoutExpired:
            result, error = None, messages.MSG_1
        except Exception as ex:
            raise exceptions.ExecutionException(details=str(ex))
        finally:
            proc.kill()

        error_clean = cls._strip_backtrace(error)
        combined = (result or '') + (error_clean or '')

        return ExecuteResult(
            result=clean_str(combined or None),
            error=clean_error(error_clean or None)
        )

    @staticmethod
    def _strip_backtrace(error: Optional[str]) -> Optional[str]:
        if not error:
            return error

        cleaned_lines = []
        skip = False
        for ln in error.splitlines():
            if ln.startswith('stack backtrace:'):
                skip = True
                continue

            if skip:
                if re.match(r'\s*\d+:\s', ln) or ln.strip() == '':
                    continue
                skip = False

            if ln.startswith('note:') and 'RUST_BACKTRACE' in ln:
                continue

            cleaned_lines.append(ln)

        return '\n'.join(cleaned_lines)

    @classmethod
    def _validate_checker_func(cls, checker_func: str):
        ...

    @classmethod
    def _check(cls, checker_func: str, **checker_func_vars) -> bool:
        ...

    @classmethod
    def debug(cls, data: DebugData) -> DebugData:
        file = RustFile(data.code)

        error = cls._compile(file)
        if error:
            data.error = error
        else:
            exec_result = cls._execute(file=file, data_in=data.data_in)
            data.result = exec_result.result
            data.error = exec_result.error

        file.remove()
        return data

    @classmethod
    def testing(cls, data: TestsData) -> TestsData:
        file = RustFile(data.code)
        error = cls._compile(file)

        for test in data.tests:
            if error:
                test.error = error
                test.ok = False
            else:
                exec_result = cls._execute(file=file, data_in=test.data_in)
                test.result = exec_result.result
                test.error = exec_result.error
                test.ok = cls._check(
                    checker_func=data.checker,
                    right_value=test.data_out,
                    value=test.result
                )

        file.remove()
        return data
