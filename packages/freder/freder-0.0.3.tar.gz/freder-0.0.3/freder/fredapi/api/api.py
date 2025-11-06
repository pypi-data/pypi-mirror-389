import requests
import os
import time


from ..exceptions import (
  ApiErrorMessage,
  InvalidApikeyFormat,
  MissingApikey,
)
from dotenv import (
  load_dotenv,
  find_dotenv
)
from ..params import (
  Apikey,
  FileType,
  vars,
)
from typing import (
  Dict, Any
)


DOTENV = load_dotenv(find_dotenv())


def apicall(
  endpoint: str,
  params: Dict[str, Any] = {},
) -> Dict:
  time.sleep(0.51)
  if not vars.APIKEY:
    if DOTENV:
      apikey = os.getenv('FRED_APIKEY')

      if apikey:
        vars.APIKEY = Apikey(apikey)
  
  if not vars.APIKEY:
    raise MissingApikey()

  if len(str(vars.APIKEY)) != 32:
    raise InvalidApikeyFormat()

  url = '/'.join([vars.BASEURL, endpoint])
  params['api_key'] = str(vars.APIKEY)
  params['file_type'] = str(FileType())
  data = {}
  wait_time = 1.1
  max_wait_time = 180

  while wait_time < max_wait_time:
    response = requests.get(
      url,
      params=params)
    data = response.json()

    if (
      error_message := data.get('error_message', None)
    ) is not None:
      if 'Too Many Requests' in error_message:
        time.sleep(wait_time)
        wait_time *= wait_time
      else:
        raise ApiErrorMessage(
          data.get('error_code', ''),
          error_message)
    else:
      break

  return data