"""User credential DTO."""

from axmp_openapi_helper import AuthConfig, AuthenticationType
from pydantic import BaseModel, Field, model_validator

from axmp_ai_agent_core.entity.user_credential import AWS_BEDROCK, UserCredentialType


class UserCredentialCreateRequest(BaseModel):
    """User credential create request."""

    display_name: str = Field(
        ...,
        description="The display name of the user credential.",
        min_length=1,
        max_length=255,
    )
    provider: str | None = Field(
        None,
        description="The provider of the user credential.",
        min_length=1,
        max_length=255,
    )
    credential_type: UserCredentialType = Field(
        ...,
        description="The type of the user credential.",
    )
    llm_api_key: str | None = Field(
        None,
        description="If the credential type is LLM_PROVIDER, this field is required.",
        min_length=1,
        max_length=1000,
    )
    aws_access_key_id: str | None = Field(
        None,
        description="If the credential type is AWS, this field is required.",
        min_length=1,
        max_length=255,
    )
    aws_secret_access_key: str | None = Field(
        None,
        description="If the credential type is AWS, this field is required.",
        min_length=1,
        max_length=255,
    )
    region_name: str | None = Field(
        "ap-northeast-2",
        description="If the credential type is AWS, this field is required.",
        min_length=1,
        max_length=50,
    )
    auth_config: AuthConfig | None = Field(
        None,
        description="If the credential type is BACKEND_SERVER or MCP_SERVER, this field is required.",
    )

    @model_validator(mode="after")
    def validate_credential_fields(self) -> "UserCredentialCreateRequest":
        """Validate credential fields based on credential type."""
        if self.credential_type == UserCredentialType.LLM_PROVIDER:
            if self.provider == AWS_BEDROCK:
                if (
                    self.aws_access_key_id is None
                    or self.aws_secret_access_key is None
                    or self.region_name is None
                ):
                    raise ValueError(
                        "The AWS access key ID, secret access key, and region name are required for AWS Bedrock type."
                    )
            else:
                if self.llm_api_key is None:
                    raise ValueError(
                        "The LLM API key is required for LLM_PROVIDER type."
                    )

            if self.auth_config is not None:
                raise ValueError(
                    "Auth config should not be provided for LLM_PROVIDER type."
                )
        elif self.credential_type in [
            UserCredentialType.BACKEND_SERVER,
            UserCredentialType.MCP_SERVER,
        ]:
            if self.auth_config is None:
                raise ValueError(
                    "The authentication configuration is required for BACKEND_SERVER or MCP_SERVER type."
                )
            else:
                if self.auth_config.type == AuthenticationType.BEARER:
                    if self.auth_config.bearer_token is None:
                        raise ValueError("The bearer token is required.")
                elif self.auth_config.type == AuthenticationType.API_KEY:
                    if self.auth_config.api_key_value is None:
                        raise ValueError("The API key is required.")
                elif self.auth_config.type == AuthenticationType.BASIC:
                    if (
                        self.auth_config.username is None
                        or self.auth_config.password is None
                    ):
                        raise ValueError("The username and password are required.")
                elif self.auth_config.type == AuthenticationType.NONE:
                    raise ValueError(
                        "Invalid authentication type. (NONE is not allowed)"
                    )
                else:
                    raise ValueError(
                        f"Invalid authentication type. ({self.auth_config.type})"
                    )

            if self.llm_api_key is not None:
                raise ValueError(
                    "LLM API key should not be provided for BACKEND_SERVER or MCP_SERVER type."
                )
        return self


class UserCredentialUpdateRequest(UserCredentialCreateRequest):
    """User credential update request."""

    pass
