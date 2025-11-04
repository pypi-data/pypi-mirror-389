from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from tpds.devices.tpds_models import DeviceInterface


class ConfiguratorMessageReponse(BaseModel):
    '''
    Configurator Message response data
    '''
    response: str = 'OK'
    status: str = 'success'


class ConfiguratorXMLTypes(str, Enum):
    '''
    XML format types from Configurators
    '''
    # proto XML contains data in clear format
    proto = 'proto_xml'
    # production XML contains secrets in encrypted format
    prod = 'prod_xml'


class ConfiguratorSlotTypes(str, Enum):
    '''
    Slot types information from Configurator
    '''
    private = 'private'
    cert = 'cert'
    general = 'general'
    secret = 'secret'


class ConfiguratorSlotLock(str, Enum):
    '''
    Slot lock information from Configurator
    '''
    enabled = 'enabled'
    disabled = 'disabled'


class ConfiguratorKeyLoad(str, Enum):
    '''
    Slot lock information from Configurator
    '''
    no_load = 'noLoad'
    cert = 'cert'
    load = 'load'


class ConfiguratorCertTypes(str, Enum):
    '''
    Certificates types information from Configurator
    '''
    no_cert = 'No certs'
    cust_cert = 'custCert'


class TFLXConfiguratorSlotInfo(BaseModel):
    '''
    Base class for TFLX Slot Information in the message from Configuratorconfigurator
    '''
    slot_id: int = 0
    slot_type: ConfiguratorSlotTypes = ConfiguratorSlotTypes.private
    key_load_config: ConfiguratorKeyLoad = ConfiguratorKeyLoad.no_load
    slot_lock: Optional[ConfiguratorSlotLock] = ConfiguratorSlotLock.disabled
    data: Optional[str] = ''


class TFLXAUTHConfiguratorSlotInfo(TFLXConfiguratorSlotInfo):
    '''
    Slot Information in the message from Configurator
    '''
    cert_type: Optional[ConfiguratorCertTypes] = ConfiguratorCertTypes.no_cert
    # Custom org name for Device certificate
    d_cert_org: Optional[str] = 'default d_org'
    # Custom common name for Device certificate
    d_cert_cn: Optional[str] = 'sn0123030405060708EE'
    # Custom expiry years for Device certificate
    d_cert_expiry_years: Optional[str] = '10'
    # Custom org name for Signer certificate
    s_cert_org: Optional[str] = 'default s_org'
    # Custom common name for Signer certificate
    s_cert_cn: Optional[str] = 'default s_cn'
    # Custom expiry years for Signer certificate
    s_cert_expiry_years: Optional[str] = '15'
    # Custom org name for Root certificate
    signer_ca_org: Optional[str] = 'default r_org'
    # Custom common name for Root certificate
    signer_ca_cn: Optional[str] = 'default r_cn'
    # Custom Public key for Root certificate
    signer_ca_pubkey: Optional[str] = ''\
        '5F00014CA54512F8A84481ABE07FA343'\
        '44AD7C52FACA3984C08061365D8B7FF1'\
        'E58187BB309EE602DE8B97DD0549B01A'\
        '173324ED5D99C02D5FDADFB8506CD2C9'


class TFLXWPCConfiguratorSlotInfo(TFLXConfiguratorSlotInfo):
    '''
    TFLXWPC Slot Information in the message from Configurator
    '''
    pass


class TFLXConfiguratorMessage(BaseModel):
    '''
    Base class for TFLX configurator Request Message
    '''
    # Provisioning base XML file to use for final XML
    base_xml: str = ''
    # XML format to be generated
    xml_type: str = 'proto_xml'
    # Interface Type
    interface: Optional[DeviceInterface] = DeviceInterface.i2c
    # Device Address
    device_address: str = ''
    # Fixed Reference
    fixed_reference: bool = False
    # Limited Use Key
    limited_key_use: str = ''
    # Enable Encrypted Write for HMAC Key
    encrypt_write: bool = False
    # diversified key option
    diversified_key: bool = False
    # Monotonic Counter
    counter_value: int = 0
    # serial number sn01, sn8
    sn01: str = "0123"
    sn8: str = "EE"
    slot3_kdf_value: str = "HKDF_Extract"


class TFLXAUTHConfiguratorMessage(TFLXConfiguratorMessage):
    '''
    TFLXAUTH Configurator Request Message
    '''
    # Provisioning base XML file to use for final XML
    base_xml: str = 'ECC204_TFLXAUTH'
    # Enable Compliance Mode
    compliance: bool = False
    # health test
    health_test: bool = False
    # Slots information
    slot_info: List[TFLXAUTHConfiguratorSlotInfo] = [
        TFLXAUTHConfiguratorSlotInfo()]
    # Part Number
    part_number: str = ''


class TFLXWPCConfiguratorMessage(TFLXConfiguratorMessage):
    '''
    TFLXWPC Configurator Request Message
    '''
    # Provisioning base XML file to use for final XML
    base_xml: str = 'ECC204_TFLXWPC'
    # Slots information
    slot_info: List[TFLXWPCConfiguratorSlotInfo] = [
        TFLXWPCConfiguratorSlotInfo()]
    # WPC PTMC Code
    ptmc: str = '004E'
    # Customer Qi ID
    qi_id: str = '11430'
    # Manufacturer CA Sequence ID
    ca_seq_id: str = '01'
    # Part Number
    part_number: str = ''
