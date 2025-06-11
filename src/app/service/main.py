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
    @staticmethod
    def _drop_privileges():
        def _fn():
            os.setgid(config.SANDBOX_USER_UID)
            os.setuid(config.SANDBOX_USER_UID)
        return _fn

    @classmethod
    def _compile(cls, file: RustFile) -> Optional[str]:
        proc = subprocess.Popen(
            ["cargo", "build", "--release", "--quiet"],
            cwd=file.project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _, err = proc.communicate(timeout=config.TIMEOUT)
        except subprocess.TimeoutExpired:
            err = messages.MSG_RUST_COMPILE_TIMEOUT
        except Exception as ex:  # pragma: no cover
            raise exceptions.CompileException(details=str(ex))
        finally:
            proc.kill()

        rc = getattr(proc, "returncode", 0)
        if rc == 0 and not err:
            return None
        return err


    @classmethod
    def _execute(cls, file: RustFile, data_in: Optional[str] = None) -> ExecuteResult:
        env = os.environ.copy()
        env["RUST_BACKTRACE"] = "0"

        if isinstance(data_in, str) and "\n" in data_in:
            data_in = data_in.replace("\n", " ")

        proc = subprocess.Popen(
            [file.filepath_out],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=cls._drop_privileges(),
            env=env,
            text=True,
        )
        try:
            out, err = proc.communicate(input=data_in, timeout=config.TIMEOUT)
        except subprocess.TimeoutExpired:
            return ExecuteResult(result=None, error=messages.MSG_1)
        except Exception as ex:
            raise exceptions.ExecutionException(details=str(ex))
        finally:
            proc.kill()

        err_clean = cls._strip_backtrace(err)
        err_final = clean_error(err_clean or None)

        out_final: Optional[str]
        if err_clean and "panicked at" in err_clean:
            merged = (out or "") + (err_clean or "")
            out_final = clean_str(merged or None)
            err_final = messages.MSG_RUST_PANIC
        else:
            out_final = clean_str(out or None)

        return ExecuteResult(result=out_final, error=err_final)


    @staticmethod
    def _strip_backtrace(error: Optional[str]) -> Optional[str]:
        if not error:
            return error

        cleaned, skip = [], False
        for line in error.splitlines():
            if line.startswith("stack backtrace:"):
                skip = True
                continue

            if skip:
                if re.match(r"\s*\d+:\s", line) or not line.strip():
                    continue
                skip = False

            if line.startswith("note:") and "RUST_BACKTRACE" in line:
                continue

            cleaned.append(line)

        return "\n".join(cleaned)

    @classmethod
    def debug(cls, data: DebugData) -> DebugData:
        rust = RustFile(data.code)

        if (err := cls._compile(rust)):
            data.error = err
        else:
            exec_res = cls._execute(file=rust, data_in=data.data_in)
            data.result, data.error = exec_res.result, exec_res.error

        rust.remove()
        return data

    @classmethod
    def testing(cls, data: TestsData) -> TestsData:
        rust = RustFile(data.code)
        compile_err = cls._compile(rust)

        for test in data.tests:
            if compile_err:
                test.error, test.ok = compile_err, False
                continue

            exec_res = cls._execute(file=rust, data_in=test.data_in)
            test.result, test.error = exec_res.result, exec_res.error
            test.ok = cls._check(
                checker_func=data.checker,
                right_value=test.data_out,
                value=test.result,
            )

        rust.remove()
        return data

    @classmethod
    def _validate_checker_func(cls, checker_func: str):
        try:
            local_ns: dict = {}
            exec(checker_func, {}, local_ns)
        except SyntaxError as ex:
            raise exceptions.CheckerException(
                message=messages.MSG_5,
                details=str(ex)
            )

        fn = local_ns.get("checker")
        if not callable(fn):
            raise exceptions.CheckerException(message=messages.MSG_2)
        if "return" not in checker_func.split("def checker", 1)[1]:
            raise exceptions.CheckerException(message=messages.MSG_3)
        return fn

    @classmethod
    def _check(cls, checker_func: str, **checker_func_vars) -> bool:
        fn = cls._validate_checker_func(checker_func)
        try:
            result = fn(**checker_func_vars)
        except Exception as ex:
            raise exceptions.CheckerException(
                message=messages.MSG_4,
                details=str(ex)
            )
        if not isinstance(result, bool):
            raise exceptions.CheckerException(message=messages.MSG_4)
        return result
