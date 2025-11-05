from typing import Union

from pydantic import Field, TypeAdapter
from typing_extensions import Annotated

from galileo_core.schemas.logging.session import BaseSession
from galileo_core.schemas.logging.span import Span
from galileo_core.schemas.logging.trace import Trace

Step = Annotated[Union[BaseSession, Trace, Span], Field(discriminator="type")]

StepAdapter: TypeAdapter[Step] = TypeAdapter(Step)
