from pydantic import BaseModel


class TracingSettings(BaseModel):
    enabled: bool = False
    service_name: str = "trainer_equipment"
    otlp_traces_endpoint: str = ""
