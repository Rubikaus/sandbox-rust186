import re
from typing import Optional
from app import messages


def clean_str(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        return value.replace('\r', '').rstrip('\n')
    return value


def clean_error(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        value = re.sub(
            pattern='\/(tmp|sandbox)\/\S*\.rs',  
            repl="main.rs",
            string=value
        )
        if 'panicked at' in value:
            value = messages.MSG_RUST_PANIC
        elif 'error[E' in value:
            value = messages.MSG_RUST_COMPILE_ERROR
        elif 'Terminated' in value:
            value = messages.MSG_1
        elif 'the monitored command dumped core' in value:
            value = messages.MSG_8
    return value