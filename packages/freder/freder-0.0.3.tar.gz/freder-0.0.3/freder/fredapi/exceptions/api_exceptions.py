class ApiErrorMessage(Exception):

  def __init__(
    self,
    error_code: int | str,
    error_message: str
  ):
    super().__init__(error_code, error_message)


class InvalidApikeyFormat(Exception):
  ''''''
  
  
class MissingApikey(Exception):
  ''''''