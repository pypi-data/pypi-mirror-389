from enum import Enum


class ObservableObjectTypeEnum(str, Enum):
    COURSE_ACCOUNT = "course_account"
    IMPORTABLE_RESOURCES = "importable_resources"
    OFFERING_USER = "offering_user"
    ORDER = "order"
    RESOURCE = "resource"
    SERVICE_ACCOUNT = "service_account"
    USER_ROLE = "user_role"

    def __str__(self) -> str:
        return str(self.value)
