# === client.py ===

import dubbo
from dubbo.configs import ReferenceConfig
from pydantic import BaseModel
from typing import List, Optional, FrozenSet, Tuple
from datetime import datetime
from uuid import UUID

class LoginRecord(BaseModel):
    timestamp: datetime
    ip_address: str

class UserMeta(BaseModel):
    tags: FrozenSet[str]
    scores: Tuple[int, int, int]

class UserRequest(BaseModel):
    name: str
    age: int

class User(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    uuid: UUID
    login_history: List[LoginRecord]
    meta: Optional[UserMeta] = None

class UserListResponse(BaseModel):
    users: List[User]
    total_count: int
    greeting: str
    generated_at: datetime

class UserServiceStub:
    def __init__(self, client: dubbo.Client):
        self.client = client
        self._list_users = client.unary(
            method_name="unary",  
            params_types=[UserRequest],
            return_type=UserListResponse,
            codec="json",
        )

    def list_users(self, request: UserRequest) -> UserListResponse:
        print(f"📤 [CLIENT] Sending request object: {request}")
        print(f"📤 [CLIENT] Sending request dict: {request.model_dump()}")  # ✅ fixed dict warning

        result = self._list_users(request)

        print(f"📥 [CLIENT] Raw response type: {type(result)}")
        print(f"📥 [CLIENT] Raw response object: {result}")

        if isinstance(result, dict):
            result = UserListResponse(**result)

        print(f"📥 [CLIENT] Parsed UserListResponse: {result}")
        return result

if __name__ == "__main__":
    print("🔗 Connecting to Dubbo server...")

    reference_config = ReferenceConfig.from_url(
        "tri://127.0.0.1:50051/org.apache.dubbo.samples.serialization.automatic"  # ✅ match service name
    )
    dubbo_client = dubbo.Client(reference_config)

    stub = UserServiceStub(dubbo_client)

    try:
        request = UserRequest(name="dubbo-python", age=18)
        print(f"📤 Calling list_users with: {request}")

        result = stub.list_users(request)
        print(result)

        print(f"\n✅ Success!")
        print(f"📨 Greeting: {result.greeting}")
        print(f"🕒 Generated At: {result.generated_at}")
        print(f"👥 Total users: {result.total_count}")
        print(f"📋 Users:")
        for user in result.users:
            print(f"   - {user.name} ({user.email}), Age: {user.age}, Active: {user.is_active}")
            print(f"     🔹 Created: {user.created_at}")
            print(f"     🔹 UUID: {user.uuid}")
            print(f"     🔹 Login History:")
            for log in user.login_history:
                print(f"         - {log.timestamp} from {log.ip_address}")
            if user.meta:
                print(f"     🔹 Tags: {list(user.meta.tags)}")
                print(f"     🔹 Scores: {user.meta.scores}")

    except Exception as e:
        print(f"❌ Error calling service: {e}")
        import traceback
        traceback.print_exc()
