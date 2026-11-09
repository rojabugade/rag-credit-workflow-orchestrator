from typing import Annotated

from fastapi import Depends

from creditflow.auth.dependencies import get_principal
from creditflow.auth.principal import Principal

PrincipalDep = Annotated[Principal, Depends(get_principal)]
