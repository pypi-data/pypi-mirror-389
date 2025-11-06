from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from zeep import Client, Settings
from zeep.helpers import serialize_object
from zeep.transports import Transport
from zeep.exceptions import Fault
from anyio import to_thread
import requests

def create_app(wsdl_url: str) -> FastAPI:
    session = requests.Session()
    session.headers.update({"User-Agent": "soap2rest/0.1"})
    transport = Transport(session=session, timeout=10)
    settings = Settings(strict=False, xml_huge_tree=True)
    client = Client(wsdl_url, transport=transport, settings=settings)
    app = FastAPI(title="SOAP to REST")

    operations = {}

    for service in client.wsdl.services.values():
        for port in service.ports.values():
            for op_name, op in port.binding._operations.items():
                input_fields = []
                try:
                    if hasattr(op.input.body, 'type') and op.input.body.type:
                        elements = op.input.body.type.elements
                        if elements:
                            for el in elements:
                                if hasattr(el, 'name'):
                                    input_fields.append(el.name)
                                elif isinstance(el, tuple):
                                    # Handle tuple format (name, type)
                                    input_fields.append(el[0] if el[0] else str(el))
                                else:
                                    input_fields.append(str(el))
                except (AttributeError, TypeError):
                    pass
                if not input_fields:
                    # Fallback: try to get from signature
                    try:
                        method = getattr(client.service, op_name)
                        import inspect
                        sig = inspect.signature(method)
                        input_fields = list(sig.parameters.keys())
                        # Remove 'self' or service instance
                        input_fields = [f for f in input_fields if f not in ('self', 'kwargs')]
                    except:
                        pass
                if input_fields:
                    operations[op_name] = input_fields

    def make_input_model(op_name):
        field_names = operations[op_name]
        # For Pydantic v2, we need to use __annotations__ and create_model
        from pydantic import create_model
        field_definitions = {name: (str, ...) for name in field_names}
        return create_model(f"{op_name}Input", **field_definitions)

    for op_name in operations:
        InputModel = make_input_model(op_name)

        def make_route(op: str, model: BaseModel):
            async def route_fn(data: model):
                try:
                    method = getattr(client.service, op)
                    # Use model_dump() for Pydantic v2, fallback to dict() for v1
                    data_dict = data.model_dump() if hasattr(data, 'model_dump') else data.dict()
                    result = await to_thread.run_sync(lambda: method(**data_dict))
                    return {"result": serialize_object(result)}
                except Fault as fault:
                    detail = {
                        "faultcode": getattr(fault, "faultcode", None),
                        "faultstring": getattr(fault, "message", str(fault)),
                    }
                    raise HTTPException(status_code=400, detail=detail)
                except requests.exceptions.Timeout as e:
                    raise HTTPException(status_code=504, detail="SOAP backend timeout")
                except requests.exceptions.RequestException as e:
                    raise HTTPException(status_code=502, detail="SOAP backend connection error")
                except Exception as e:
                    raise HTTPException(status_code=500, detail="Internal server error")

            route_fn.__name__ = f"call_{op}"
            return route_fn

        app.post(f"/call/{op_name}", response_model=dict)(make_route(op_name, InputModel))

    @app.get("/")
    def index():
        return {
            "message": "Available SOAP methods via REST",
            "endpoints": [f"/call/{op}" for op in operations]
        }

    return app
