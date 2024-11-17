import logging
import threading
from functools import wraps
from typing import Callable, Any


def safe_operation(method: Callable) -> Callable:

    @wraps(method)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            error_msg = f"{method.__name__}でエラーが発生しました: {str(e)}"
            logging.error(error_msg, exc_info=True)
            if threading.current_thread() is not threading.main_thread():
                self.master.after(0, lambda: self._handle_error(error_msg))
            else:
                self._handle_error(error_msg)
            return None

    return wrapper
