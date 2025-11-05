from typing import Annotated

from pydantic import AfterValidator

from .. import cpf


CPF = Annotated[str, AfterValidator(cpf.validate)]
