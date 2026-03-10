class FileProcessingError(Exception):
    def __init__(self, file_name=None, message=" FAILED during processing of file", code="FileProcessingError:"):
        self.file_name = file_name
        self.code = code
        self.message = self.combine_parameters_to_message(message)
        super().__init__(self)

    def combine_parameters_to_message(self, _passed_message):
        _original_message = self.message
        _new_message = (
                f"{_original_message}: " +
                f"{self.file_name}\n: " if self.file_name else " " +
                f"{self.code}"
        )
        return _new_message