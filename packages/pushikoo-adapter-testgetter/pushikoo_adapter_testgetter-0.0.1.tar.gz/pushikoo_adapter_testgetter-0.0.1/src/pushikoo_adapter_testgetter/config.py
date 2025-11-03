from pushikoo_interface import GetterClassConfig, GetterInstanceConfig
from pydantic import BaseModel, Field

# GetterClassConfig and GetterInstanceConfig inherit from pydantic.BaseModel,
# so when defining your own ClassConfig / InstanceConfig,
# you are essentially defining a BaseModel and can fully use all BaseModel features.


class ClassConfig(GetterClassConfig):
    class GetListOption(BaseModel):
        count: int = Field(default=2, description="Number of items to get")

    get_list_option: GetListOption = Field(
        default_factory=GetListOption,
        description="Get list option",
    )
    mockapi_delay: float = Field(default=0.1, description="Mock API delay in seconds")


class InstanceConfig(GetterInstanceConfig):
    token: str = Field(default="7070707", description="Token for authentication")
    userid: str = Field(default="123456", description="User ID")
