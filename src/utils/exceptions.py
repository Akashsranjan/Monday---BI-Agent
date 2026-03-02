import sys
import traceback


class CustomException(Exception):
    """
    Usage — always raise from inside an except block so exc_info() works:

        try:
            risky_operation()
        except Exception as e:
            raise CustomException("Something went wrong", sys) from e
    """

    def __init__(self, error_message, error_detail: sys):
        super().__init__(error_message)
        self.error_message = self._build_message(error_message, error_detail)

    @staticmethod
    def _build_message(error_message, error_detail: sys) -> str:
        _, _, exc_tb = error_detail.exc_info()

        # Guard: exc_tb is None if called outside an except block
        if exc_tb is None:
            return f"Error: {error_message}"

        file_name   = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        return f"Error in {file_name}, line {line_number}: {error_message}"

    def __str__(self):
        return self.error_message