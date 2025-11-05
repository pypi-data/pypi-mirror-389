from typing import Annotated

from pydantic import AfterValidator

from br_docs import cnpj


CNPJ = Annotated[str, AfterValidator(cnpj.validate)]
