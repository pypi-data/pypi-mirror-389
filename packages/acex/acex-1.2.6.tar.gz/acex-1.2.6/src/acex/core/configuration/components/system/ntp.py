from acex.core.configuration.components.base_component import ConfigComponent
from acex.core.models.ntp_server import NtpAttributes

class NTPServer(ConfigComponent):
    type = "ntp_server"
    model_cls = NtpAttributes