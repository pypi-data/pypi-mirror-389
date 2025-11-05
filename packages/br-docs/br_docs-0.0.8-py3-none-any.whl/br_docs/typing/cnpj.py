from typing import Annotated

from pydantic import AfterValidator

from .. import cnpj


CNPJ = Annotated[str, AfterValidator(cnpj.validate)]
