import strawberry

# Example:
# from typing import List
# from .types import MaintenanceWindowType
# from ..models import MaintenanceWindow
#
# @strawberry.type
# class Query:
#     @strawberry.field
#     def maintenance_windows(self) -> List[MaintenanceWindowType]:
#         return MaintenanceWindow.objects.all()
#
# schema = strawberry.Schema(query=Query)

@strawberry.type
class Query:
    pass

schema = strawberry.Schema(query=Query)
