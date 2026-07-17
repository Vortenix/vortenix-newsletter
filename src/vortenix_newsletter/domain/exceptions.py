class VortenixError(Exception): pass
class ConfigurationError(VortenixError): pass
class InvalidStatusTransition(VortenixError): pass
class DeliveryError(VortenixError): pass
