from pydantic import BaseModel
from typing import List, Optional, FrozenSet, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import dubbo
from dubbo.configs import ServiceConfig
from dubbo.proxy.handlers import RpcMethodHandler, RpcServiceHandler

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
    created_at: datetime = datetime.utcnow()
    uuid: UUID = uuid4()
    login_history: List[LoginRecord] = []
    meta: Optional[UserMeta] = None

class UserListResponse(BaseModel):
    users: List[User]
    total_count: int
    greeting: str
    generated_at: datetime = datetime.utcnow()

class UserServiceHandler:
    def __init__(self):
        self.users_db = {
            'name' : 'aditya'
        }
        # [
        #     User(
        #         id=1,
        #         name="Alice",
        #         email="alice@example.com",
        #         age=30,
        #         login_history=[
        #             LoginRecord(timestamp=datetime.utcnow() - timedelta(days=1), ip_address="192.168.1.10"),
        #             LoginRecord(timestamp=datetime.utcnow(), ip_address="192.168.1.11")
        #         ],
        #         meta=UserMeta(tags=frozenset(["admin", "beta"]), scores=(88, 92, 85))
        #     ),
        #     User(
        #         id=2,
        #         name="Bob",
        #         email="bob@example.com",
        #         age=25,
        #         login_history=[
        #             LoginRecord(timestamp=datetime.utcnow() - timedelta(hours=2), ip_address="192.168.1.20")
        #         ],
        #         meta=UserMeta(tags=frozenset(["tester"]), scores=(75, 80, 70))
        #     )
        # ]

    def listUsers(self, request) -> UserListResponse:
        print(f"🔧 [SERVER] Raw request: {request}")
        print(f"🔧 [SERVER] Request type: {type(request)}")

        if isinstance(request, list):
            if len(request) > 0:
                request_data = request[0]
                if isinstance(request_data, dict):
                    if '__model_data__' in request_data:
                        actual_data = request_data['__model_data__']
                        request = UserRequest(**actual_data)
                    else:
                        request = UserRequest(**request_data)
                else:
                    request = request_data
            else:
                request = UserRequest(name="Unknown", age=0)
        elif isinstance(request, dict):
            if '__model_data__' in request:
                request = UserRequest(**request['__model_data__'])
            else:
                request = UserRequest(**request)
        elif not isinstance(request, UserRequest):
            try:
                request = UserRequest(**request)
            except:
                request = UserRequest(name="Unknown", age=0)

        print(f"✅ [SERVER] Parsed UserRequest: {request}")

        greeting = f"Hello {request.name} (age {request.age})!"

        response = UserListResponse(
            users=self.users_db,
            total_count=len(self.users_db),
            greeting=greeting,
            generated_at=datetime.utcnow()
        )
        print(f"📦 [SERVER] Sending enriched response:\n{response.model_dump_json(indent=2, exclude_none=True)}")
        return response

def build_service_handler_manual(codec_type: str = 'json'):
    service_impl = UserServiceHandler()
    method_handler = RpcMethodHandler.unary(
        method=service_impl.listUsers,
        method_name="unary",
        params_types=[UserRequest],
        return_type=UserListResponse,
        codec=codec_type
    )
    service_handler = RpcServiceHandler(
        service_name="org.apache.dubbo.samples.serialization.automatic",
        method_handlers=[method_handler],
    )
    return service_handler

def build_service_handler_automatic_fixed(codec_type: str = 'json'):
    service_impl = UserServiceHandler()
    method_handler = RpcMethodHandler.unary(
        method=service_impl.listUsers,
        codec=codec_type
    )
    service_handler = RpcServiceHandler(
        service_name="org.apache.dubbo.samples.serialization.automatic",
        method_handlers=[method_handler],
    )
    return service_handler

def build_service_handler_multiple_methods(codec_type: str = 'json'):
    service_impl = UserServiceHandler()
    list_users_handler = RpcMethodHandler.unary(
        method=service_impl.listUsers,
        method_name="listUsers",
        params_types=[UserRequest],
        return_type=UserListResponse,
        codec=codec_type
    )
    service_handler = RpcServiceHandler(
        service_name="org.apache.dubbo.samples.serialization.automatic",
        method_handlers=[list_users_handler],
    )
    return service_handler

def run_server(mode: str = "manual", codec_type: str = 'json', host: str = "127.0.0.1", port: int = 50051):
    print(f"🚀 Starting Dubbo server in {mode.upper()} mode with {codec_type} codec...")

    if mode == "manual":
        service_handler = build_service_handler_manual(codec_type)
    elif mode == "automatic":
        service_handler = build_service_handler_automatic_fixed(codec_type)
    elif mode == "multiple":
        service_handler = build_service_handler_multiple_methods(codec_type)
    else:
        raise ValueError(f"Unknown mode: {mode}. Use: manual, automatic, or multiple")

    service_config = ServiceConfig(
        service_handler=service_handler,
        host=host,
        port=port
    )

    server = dubbo.Server(service_config).start()

    print(f"✅ Server running at {host}:{port}")
    print(f"📋 Service: {service_handler.service_name}")
    print(f"🔧 Mode: {mode}")
    print(f"📦 Codec: {codec_type}")
    print(f"📚 Available methods: {list(service_handler.method_handlers.keys())}")
    print("\nPress Enter to stop the server...")

    input()
    print("🛑 Server stopped")

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "manual"
    codec_type = sys.argv[2] if len(sys.argv) > 2 else "json"
    run_server(mode=mode, codec_type=codec_type)
