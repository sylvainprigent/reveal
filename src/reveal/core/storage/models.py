from reveal.core.common.models import CoreModel
from reveal.core.relational.models import RelationalType


class StorageColumn(CoreModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool
    unique: bool
    


class StorageForeignKey(CoreModel):
    column: str
    referenced_table: str
    referenced_column: str