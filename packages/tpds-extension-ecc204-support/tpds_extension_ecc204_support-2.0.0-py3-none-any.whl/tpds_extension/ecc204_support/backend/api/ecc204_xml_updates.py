# -*- coding: utf-8 -*-
# 2019 to present - Copyright Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
# PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT, SPECIAL,
# PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY
# KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP
# HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO THE
# FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN
# ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
# THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.

from __future__ import annotations
import os
import json
from pathlib import Path
from lxml import etree
import datetime
from cryptography import x509
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from wpc_pt_config.api.certs_schema import WPCRootCertParams
from wpc_pt_config.api.wpc_root import create_wpc_root_cert
from wpc_pt_config.api.wpc_mfg import create_wpc_mfg_cert
from wpc_pt_config.api.wpc_puc import create_wpc_puc_cert

from tpds.certs.tflex_certs import TFLEXCerts
from tpds.tp_utils.tp_keys import TPAsymmetricKey
from tpds.certs.cert_utils import get_device_public_key, get_backend, get_certificate_CN, get_certificate_issuer_CN
from tpds.schema import get_ecc204_ta010_xsd_path
from tpds.schema.models.ecc204_1_2.ecc204_ta010_config_1_2 import (
    Ecc204Config, Ecc206Config, Ta010Config, DataSourceType, StaticBytesType, SecretBinaryDataType,
    X509NameType, X509CertificateType, X509SignatureAlgorithmType, X509SignatureAlgorithmEcdsatype,
    X509CacertificateChainType, X509SerialNumberType, X509TimeType, X509SubjectPublicKeyInfoType,
    X520DirectoryStringOrFromSourceType, QiCertificateChainType, HashType, DataSourcesWriterType,
    DeviceGenerateKeyType, GenerateKeyEcctype, HsmrandomType, CounterType, BytesPadType, TemplateType,
    X509ExtensionsType, X509ExtensionType, DerbinaryDataOrFromSourceType, X509AuthorityKeyIdentifierType, BinaryDataOrStringType, CryptoAuthCompressedCertificateSntype,
    DateTimeModifyType, DateTimeModifySetFieldsType, CryptoAuthCompressedCertificateType, Kdftype, HkdfextractType, HkdfexpandType,
    StringOrDataOrFromSourceType, CryptoAuthDeriveKeyType, FixedSizeAlignment, BytesEncodeType, BytesEncodeHexType, X509SubjectKeyIdentifierType, KeyIdentifierCalculatedType,
    X509KeyUsageType, X509BasicConstraintsType, X509ExtendedKeyUsageType
)


class ECC204_TA010_XMLUpdates():
    def __init__(self, base_xml) -> None:
        # To Resolve ForwardRef Problem
        X509CertificateType.TbsCertificate.__pydantic_model__.update_forward_refs()
        X509NameType.RelativeDistinguishedName.__pydantic_model__.update_forward_refs()
        X509AuthorityKeyIdentifierType.IdMethod.__pydantic_model__.update_forward_refs()
        self.xml_path = os.path.join(os.path.dirname(
            __file__), "base", "ECC204_TA010_base.xml")
        self.xsd_path = get_ecc204_ta010_xsd_path()
        self.base_xml = base_xml
        xml_string = Path(self.xml_path).read_text()
        config_map = {
            "ECC204": Ecc204Config,
            "ECC206": Ecc206Config,
            "TA010": Ta010Config,
        }
        config = next((cfg for key, cfg in config_map.items() if key in base_xml), Ta010Config)
        self.xml_obj = XmlParser().from_string(xml_string, config)

    def save_root(self, dest_xml):
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)
        Path(dest_xml).touch()
        with Path(dest_xml).open("w") as fp:
            serializer.write(out=fp, obj=self.xml_obj, ns_map={
                None: "https://www.microchip.com/schema/ECC204_TA010_Config_1.2"})

        status = self.__validate_xml(dest_xml, self.xsd_path)
        if (status != "valid"):
            Path(dest_xml).unlink(missing_ok=True)
            raise BaseException(f"XML generation failed with: {status}")

    def process_compressed_cert_xml(self, name, cert, certificate, ca_certificate, signer_or_device):
        '''
        CryptoAuthCompressedCertificateType certificate data for provisioning XML
        '''
        ds = DataSourceType(name=name)
        ds.crypto_auth_compressed_certificate = CryptoAuthCompressedCertificateType()
        ds.crypto_auth_compressed_certificate.certificate = certificate
        ds.crypto_auth_compressed_certificate.ca_certificate = ca_certificate

        if signer_or_device == "signer":
            c_definition_string = cert.get_signer_c_definition_string().get("cust_def_signer.c")
            c_def_value = c_definition_string.split(b'\n', 1)[1]
        elif signer_or_device == "device":
            c_definition_string = cert.get_device_c_definition_string().get("cust_def_device.c")
            c_def_value = c_definition_string.split(b'\n', 2)[2]

        c_def_value = str(c_def_value, encoding='utf-8').replace('\n', '\n\t\t\t')
        ds.crypto_auth_compressed_certificate.atcacert_def = CryptoAuthCompressedCertificateType.AtcacertDef(
            cryptoauthlib_version="3.7.0", value=c_def_value)
        return ds

    def process_xml_cert_extensions(self, extensions_params):
        extensions = X509ExtensionsType()
        if extensions_params.get("extension"):
            extension = []
            for each in extensions_params.get("extension"):
                each_extension = X509ExtensionType(extn_id=each.get("extn_id"), critical=each.get("critical"),
                                                   extn_value=DerbinaryDataOrFromSourceType(value=each.get("extn_value"),
                                                                                            from_source=each.get("from_source")))
                extension.append(each_extension)
            setattr(extensions, "extension", extension)

        if extensions_params.get("authority_key_identifier"):
            aki_params = extensions_params.get("authority_key_identifier")
            AKI = X509AuthorityKeyIdentifierType(
                critical=aki_params.get("critical"),
                id_method=X509AuthorityKeyIdentifierType.IdMethod())

            if aki_params.get("key_identifier"):
                key_identifier_params = aki_params.get("key_identifier")
                AKI.id_method.key_identifier = X509AuthorityKeyIdentifierType.IdMethod.KeyIdentifier()
                if key_identifier_params.get("from_ca_subject_key_identifier") is not None:
                    AKI.id_method.key_identifier.from_ca_subject_key_identifier = key_identifier_params.get("from_ca_subject_key_identifier")
                elif key_identifier_params.get("calculated"):
                    calculated_params = key_identifier_params.get("calculated")
                    AKI.id_method.key_identifier.calculated = KeyIdentifierCalculatedType()
                    AKI.id_method.key_identifier.calculated.method = calculated_params.get("method")
                    AKI.id_method.key_identifier.calculated.truncated_size = calculated_params.get("truncated_size")
            if aki_params.get("issuer_and_serial_number"):
                AKI.id_method.issuer_and_serial_number = aki_params.get("issuer_and_serial_number").get("issuer_and_serial_number")
            setattr(extensions, "authority_key_identifier", AKI)

        if extensions_params.get("subject_key_identifier"):
            ski_params = extensions_params.get("subject_key_identifier")
            SKI = X509SubjectKeyIdentifierType(
                critical=ski_params.get("critical"), key_identifier=X509SubjectKeyIdentifierType.KeyIdentifier())
            SKI.key_identifier.from_source = ski_params.get("from_source")
            SKI.key_identifier.calculated = KeyIdentifierCalculatedType()
            SKI.key_identifier.calculated.method = ski_params.get("method")
            SKI.key_identifier.calculated.truncated_size = ski_params.get("truncated_size")
            setattr(extensions, "subject_key_identifier", SKI)

        if extensions_params.get("key_usage"):
            key_usage = X509KeyUsageType()
            useage_params = extensions_params.get("key_usage")
            usage_list = [
                "critical", "digital_signature", "content_commitment", "key_encipherment", "data_encipherment",
                "key_agreement", "key_cert_sign", "crl_sign", "encipher_only", "decipher_only"]
            for each_usage in usage_list:
                setattr(key_usage, each_usage, useage_params.get(each_usage))
            setattr(extensions, "key_usage", key_usage)

        if extensions_params.get("basic_constraints"):
            constraint_params = extensions_params.get("basic_constraints")
            basic_constraints = X509BasicConstraintsType(
                critical=constraint_params.get("critical"),
                ca=constraint_params.get("ca"),
                path_len_constraint=constraint_params.get("path_len_constraint"))
            setattr(extensions, "basic_constraints", basic_constraints)

        if extensions_params.get("extended_key_usage"):
            extended_params = extensions_params.get("extended_key_usage")
            extended_usage = X509ExtendedKeyUsageType(
                critical=extended_params.get("critical"), key_purpose_id=extended_params.get("key_purpose_id")
            )
            setattr(extensions, "extended_key_usage", extended_usage)

        return extensions

    def process_cert_xml(self, cert_data):
        '''
        process X509 certificate data for provisioning XML
        '''
        ds = DataSourceType(name=cert_data.get("name"), description=cert_data.get("desc"))
        ds.x509_certificate = X509CertificateType()

        ds.x509_certificate.ca_certificate_chain = X509CacertificateChainType(value=cert_data.get("cert_chain"))
        ds.x509_certificate.signature_algorithm = X509SignatureAlgorithmType(
            ecdsa=X509SignatureAlgorithmEcdsatype(hash=cert_data.get("hash")))
        ds.x509_certificate.tbs_certificate = X509CertificateType.TbsCertificate(
            version="V3")
        ds.x509_certificate.tbs_certificate.serial_number = X509SerialNumberType(
            value="Certificate_SN")
        ds.x509_certificate.tbs_certificate.validity = X509CertificateType.TbsCertificate.Validity()
        ds.x509_certificate.tbs_certificate.validity.not_before = X509TimeType(
            value="Certificate_Not_Before", type_value="UTC_Time", from_source="True")
        if cert_data.get("expiry_years") == 0:
            ds.x509_certificate.tbs_certificate.validity.not_after = X509TimeType(
                value="9999-12-31T23:59:59", type_value="Auto", from_source="False")
        else:
            ds.x509_certificate.tbs_certificate.validity.not_after = X509TimeType(
                value="Certificate_Not_After", type_value="Generalized_Time", from_source="True")
        if cert_data.get("cert_common_name") and cert_data.get("cert_common_name") != "":
            ds.x509_certificate.tbs_certificate.subject = X509NameType(relative_distinguished_name=[X509NameType.RelativeDistinguishedName(
                common_name=X520DirectoryStringOrFromSourceType(
                    type_value="UTF8_String", from_source="True", value="Certificate_CN"))])
        subject_public_key = "Device_Public_Key"
        if cert_data.get("subject_public_key_info"):
            subject_public_key = cert_data.get("subject_public_key_info")
        ds.x509_certificate.tbs_certificate.subject_public_key_info = X509SubjectPublicKeyInfoType(
            key=X509SubjectPublicKeyInfoType.Key(value=subject_public_key))
        if cert_data.get("extensions"):
            setattr(ds.x509_certificate.tbs_certificate, "extensions", self.process_xml_cert_extensions(cert_data.get("extensions")))
        return ds

    def __validate_xml(self, xml_path: str, xsd_path: str):
        '''
        checks xml against it's xsd file
        '''
        with open(xsd_path) as f_schema:
            schema_doc = etree.parse(f_schema)
            schema = etree.XMLSchema(schema_doc)
            parser = etree.XMLParser(schema=schema)

            with open(xml_path) as f_source:
                try:
                    etree.parse(f_source, parser)
                except etree.XMLSyntaxError as e:
                    return e
        return "valid"


class ECC204_TA010_TFLXAUTH_XMLUpdates(ECC204_TA010_XMLUpdates):
    def update_with_user_data(self, user_data):
        user_data = json.loads(user_data)
        self.__process_slot_config(user_data)
        self.__process_slot_data(user_data)

    def __process_slot_config(self, user_data):
        '''
        process config slots to provisiong XML
        '''
        self.xml_obj.config_name = f"{user_data.get('part_number')} {user_data.get('xml_type')}"

        # configuration_subzone_0
        configuration_subzone_0 = self.xml_obj.configuration_subzone_0
        configuration_subzone_0.io_options.interface = "SWI_PWM" if (
            user_data.get("interface") == "swi") else "I2C"
        if user_data.get("sn01"):
            configuration_subzone_0.sn_0_1.value = user_data.get("sn01")
        if user_data.get("sn8"):
            configuration_subzone_0.sn_8.value = user_data.get("sn8")

        # configuration_subzone_1
        configuration_subzone_1 = self.xml_obj.configuration_subzone_1
        configuration_subzone_1.chip_mode.cmos_en = "Fixed_Reference" if user_data.get(
            "fixed_reference") else "VCC_Referenced"
        configuration_subzone_1.chip_mode.clock_divider = "0b11"
        configuration_subzone_1.chip_mode.rng_nrbg_health_test_auto_clear = "True" if user_data.get(
            "health_test") else "False"
        configuration_subzone_1.slot_config0.limited_use = "True" if (
            user_data.get("limited_key_use") == "private") else "False"
        configuration_subzone_1.slot_config3.limited_use = "True" if (
            user_data.get("limited_key_use") == "secret") else "False"
        configuration_subzone_1.slot_config3.write_mode = "Encrypted" if user_data.get(
            "encrypt_write") else "Clear"
        configuration_subzone_1.lock = "True"

        # configuration_subzone_2
        configuration_subzone_2 = self.xml_obj.configuration_subzone_2
        configuration_subzone_2.counts_remaining = 10000 - \
            user_data.get("counter_value")
        configuration_subzone_2.lock = "True"

        # configuration_subzone_3
        configuration_subzone_3 = self.xml_obj.configuration_subzone_3
        configuration_subzone_3.device_address = f'0x{user_data.get("device_address")}'
        configuration_subzone_3.cmp_mode = "True" if user_data.get(
            "compliance") else "False"
        configuration_subzone_3.lock = "True"

    def __process_slot_data(self, user_data):
        '''
        Process data slots to provisioning XML
        '''
        slot_info = user_data.get("slot_info")

        # slot locks
        slot_locks = self.xml_obj.slot_locks
        slot_locks.slot_0 = "True"
        slot_locks.slot_1 = "True" if (slot_info[1].get(
            "slot_lock") == "enabled") else "False"
        slot_locks.slot_2 = "True" if (slot_info[2].get(
            "slot_lock") == "enabled") else "False"
        slot_locks.slot_3 = "True" if (slot_info[3].get(
            "slot_lock") == "enabled") else "False"

        self.xml_obj.data_sources.data_source = []

        # Slot 0 - Data_Sources - Device_Generate_Key
        ds = DataSourceType(name="Device_Public_Key")
        ds.device_generate_key = DeviceGenerateKeyType(target="Slot 0")
        ds.device_generate_key.ecc = GenerateKeyEcctype(curve="secp256r1")
        self.xml_obj.data_sources.data_source.append(ds)

        # Slot 1 - Data_Sources - certs
        cert_data = user_data.get('slot_info')[1]
        if (cert_data.get('cert_type') == "custCert"):
            self.__process_certs(cert_data)

        # Slot 2 - Data_Sources - general
        if (slot_info[2].get("data")):
            ds = DataSourceType(name="Slot_2_Client_Data",
                                description="Slot 2 general public data storage (64 bytes)")
            ds.static_bytes = StaticBytesType(public=BinaryDataOrStringType(
                value=slot_info[2].get("data"), encoding="Hex"))
            self.xml_obj.data_sources.data_source.append(ds)

        # Slot 3 - Data_Sources - secret
        if (slot_info[3].get("data")):
            if user_data.get('slot3_kdf_value') != "no_kdf":
                name_value, true_false = ("IKM", "False") if user_data.get('slot3_kdf_value') == "HKDF_Extract" else (
                    ("PRK", "False") if user_data.get('slot3_kdf_value') == "HKDF_Expand" else ("Parent_Key", "False"))
            else:
                name_value, true_false = "Slot_3_Client_Data", "False"
            ds = DataSourceType(name=name_value, description="Slot 3 Storage for a secret key")
            ds.static_bytes = StaticBytesType(secret=SecretBinaryDataType(
                encoding="Hex", key_name="WrapKey1", algorithm="AES256_GCM"), encrypted=true_false)
            ds.static_bytes.secret.encrypted = true_false
            ds.static_bytes.secret.value = slot_info[3].get("data")
            self.xml_obj.data_sources.data_source.append(ds)

            # Add Process_Info and KDF_Seed if diversified key is checked and Crypto_Auth_Derive_Key selected
            if user_data.get('slot3_kdf_value') in ["Crypto_Auth_Derive_Key"]:
                ds = DataSourceType(name="Process_Info")
                ds.process_info = ""
                self.xml_obj.data_sources.data_source.append(ds)

                ds = DataSourceType(name="KDF_Seed")
                ds.bytes_pad = BytesPadType()
                ds.bytes_pad.input = "Process_Info.Serial_Number"
                ds.bytes_pad.fixed_size = BytesPadType().FixedSize()
                ds.bytes_pad.fixed_size.output_size = "32"
                ds.bytes_pad.fixed_size.pad_byte = "0x00"
                ds.bytes_pad.fixed_size.alignment = FixedSizeAlignment(value="Pad_Right")
                self.xml_obj.data_sources.data_source.append(ds)

            # Add KDF type if diversified key is checked
            if user_data.get('slot3_kdf_value') in ["HKDF_Extract", "HKDF_Expand", "Crypto_Auth_Derive_Key"]:
                ds = DataSourceType(name="KDF") if user_data.get('slot3_kdf_value') in ["HKDF_Extract", "HKDF_Expand"] else DataSourceType(name="Diversified_Key")
                ds.kdf = Kdftype()

                if user_data.get('slot3_kdf_value') == "HKDF_Extract":
                    ds.kdf.hkdf_extract = HkdfextractType()
                    ds.kdf.hkdf_extract.initial_keying_material = "IKM"
                    ds.kdf.hkdf_extract.output_size = "32"
                    ds.kdf.hkdf_extract.hash = "SHA256"
                elif user_data.get('slot3_kdf_value') == "HKDF_Expand":
                    ds.kdf.hkdf_expand = HkdfexpandType()
                    ds.kdf.hkdf_expand.pseudorandom_key = "PRK"
                    ds.kdf.hkdf_expand.info = StringOrDataOrFromSourceType()
                    ds.kdf.hkdf_expand.info.from_source = "False"
                    ds.kdf.hkdf_expand.info.encoding = "Hex"
                    ds.kdf.hkdf_expand.output_size = "32"
                    ds.kdf.hkdf_expand.hash = "SHA256"
                else:
                    ds.kdf.crypto_auth_derive_key = CryptoAuthDeriveKeyType()
                    ds.kdf.crypto_auth_derive_key.parent_key = "Parent_Key"
                    ds.kdf.crypto_auth_derive_key.target_key = "3"
                    ds.kdf.crypto_auth_derive_key.seed = StringOrDataOrFromSourceType()
                    ds.kdf.crypto_auth_derive_key.seed.from_source = "True"
                    ds.kdf.crypto_auth_derive_key.seed.value = "KDF_Seed"
                    ds.kdf.crypto_auth_derive_key.output_size = "32"
                self.xml_obj.data_sources.data_source.append(ds)

        # data source writer
        self.xml_obj.data_sources.writer = []

        # Writer For Slot 1
        cert_data = user_data.get('slot_info')[1]
        if (cert_data.get('cert_type') == "custCert"):
            wr = DataSourcesWriterType(source_name="Slot_1_Data", target="Slot 1")
            self.xml_obj.data_sources.writer.append(wr)

        # Writer For Slot 2
        if (slot_info[2].get("data")):
            wr = DataSourcesWriterType(
                source_name="Slot_2_Data", target="Slot 2")
            self.xml_obj.data_sources.writer.append(wr)

        # Writer For Slot 3
        if (slot_info[3].get("data")):
            if user_data.get('slot3_kdf_value') != "no_kdf":
                wr = DataSourcesWriterType(source_name="KDF", target="Slot 3") if user_data.get('slot3_kdf_value') in [
                    "HKDF_Extract", "HKDF_Expand"] else DataSourcesWriterType(source_name="Diversified_Key", target="Slot 3")
            else:
                wr = DataSourcesWriterType(source_name="Slot_3_Client_Data", target="Slot 3")
            self.xml_obj.data_sources.writer.append(wr)

        # data source wrapped key
        self.xml_obj.data_sources.wrapped_key = []

    def __process_certs(self, cert_data):
        tflex_certs = TFLEXCerts(device_name="ECC204")
        tflex_certs.build_root(
            org_name=cert_data.get('signer_ca_org'),
            common_name=cert_data.get('signer_ca_cn'),
            validity=int(cert_data.get('s_cert_expiry_years')),
            user_pub_key=bytes(cert_data.get('signer_ca_pubkey'), 'ascii'))
        tflex_certs.build_signer_csr(
            org_name=cert_data.get('s_cert_org'),
            common_name=cert_data.get('s_cert_cn'),
            signer_id='FFFF')
        tflex_certs.build_signer(
            validity=int(cert_data.get('s_cert_expiry_years')))
        tflex_certs.build_device(
            device_sn=cert_data.get('d_cert_cn'),
            org_name=cert_data.get('d_cert_org'),
            validity=int(cert_data.get('d_cert_expiry_years')))
        tflex_certs.save_tflex_c_definitions()
        certs_txt = tflex_certs.root.get_certificate_in_text() + "\n\n" + \
            tflex_certs.signer.get_certificate_in_text() + "\n\n" + \
            tflex_certs.device.get_certificate_in_text()

        Path("custom_certs.txt").write_text(certs_txt)
        Path("root.crt").write_bytes(tflex_certs.root.get_certificate_in_pem())
        Path("signer.crt").write_bytes(tflex_certs.signer.get_certificate_in_pem())
        Path("device.crt").write_bytes(tflex_certs.device.get_certificate_in_pem())

        signer_pem = tflex_certs.signer.get_certificate_in_pem()
        root_pem = tflex_certs.root.get_certificate_in_pem()
        cert_chain_text = f'\nSubject: CN={cert_data.get("s_cert_cn")},O={cert_data.get("s_cert_org")}\n' + \
            f'Issuer: CN={cert_data.get("signer_ca_cn")},O={cert_data.get("signer_ca_org")}\n' + \
            str(signer_pem, 'utf-8') + \
            f'\n\nSubject: CN={cert_data.get("signer_ca_cn")},O={cert_data.get("signer_ca_org")}\n' + \
            f'Issuer: {cert_data.get("signer_ca_cn")},O={cert_data.get("signer_ca_org")}\n' + \
            str(root_pem, 'utf-8')

        device_cert = x509.load_pem_x509_certificate(
            tflex_certs.device.get_certificate_in_pem())
        current_date = datetime.datetime.now()
        expiry_years = int(cert_data.get("d_cert_expiry_years"))
        if expiry_years == 0:
            expiry_date = current_date.max
        else:
            expiry_date = current_date.replace(
                year=current_date.year + int(cert_data.get("d_cert_expiry_years")))

        cert_data = {
            "name": "Device_Certificate",
            "desc": "Slot 1 Device and Signer compressed certificate",
            "cert_chain": cert_chain_text.replace("\n", "\n\t\t\t"),
            "hash": "SHA256",
            "version": "V3",
            "serial_number": f'sn{device_cert.serial_number}',
            "not_valid_before": current_date.strftime("Z%Y%m%d"),
            "not_valid_after": expiry_date.strftime("Z%Y%m%d"),
            "cert_common_name": get_certificate_CN(device_cert),
            "expiry_years": expiry_years,
            "extensions": {
                "authority_key_identifier": {
                    "critical": "False",
                    "key_identifier": {
                        "from_ca_subject_key_identifier": "",
                    }
                },
                "subject_key_identifier": {
                    "critical": "False",
                    "method": "RFC5280_Method1"
                },
                "key_usage": {
                    "critical": "True",
                    "digital_signature": "True",
                    "content_commitment": "False",
                    "key_encipherment": "False",
                    "data_encipherment": "False",
                    "key_agreement": "True",
                    "key_cert_sign": "False",
                    "crl_sign": "False",
                    "encipher_only": "False",
                    "decipher_only": "False",
                },
                "basic_constraints": {
                    "critical": "True",
                    "ca": "False"
                },
            }
        }

        ds = self.process_cert_xml(cert_data=cert_data)
        self.xml_obj.data_sources.data_source.append(ds)

        # Compressed device and signer certificates
        ds = self.process_compressed_cert_xml(name="Device_Certificate_Compressed",
                                              cert=tflex_certs,
                                              certificate="Device_Certificate.Certificate",
                                              ca_certificate="Device_Certificate.CA_Certificate_1",
                                              signer_or_device="device")
        self.xml_obj.data_sources.data_source.append(ds)

        ds = self.process_compressed_cert_xml(name="Signer_Certificate_Compressed",
                                              cert=tflex_certs,
                                              certificate="Device_Certificate.CA_Certificate_1",
                                              ca_certificate="Device_Certificate.CA_Certificate_2",
                                              signer_or_device="signer")
        self.xml_obj.data_sources.data_source.append(ds)

        # Slot_1_Data
        ds = DataSourceType(name="Slot_1_Data", description="Pad out slot 1 data to the full slot size.")
        ds.bytes_pad = BytesPadType()
        ds.bytes_pad.input = "Slot_1_Client_Data_Unpadded"
        ds.bytes_pad.fixed_size = BytesPadType().FixedSize()
        ds.bytes_pad.fixed_size.output_size = "320"
        ds.bytes_pad.fixed_size.pad_byte = "0x00"
        ds.bytes_pad.fixed_size.alignment = FixedSizeAlignment(value="Pad_Right")
        self.xml_obj.data_sources.data_source.append(ds)

        # Slot 1 Client Data that conatins the certificates
        ds = DataSourceType(name="Slot_1_Client_Data_Unpadded", description="Slot 1 Device and Signer compressed certificate")
        ds.template = TemplateType()
        ds.template.definition = TemplateType.Definition(value=((
            "\n\t\t\t{Device_Certificate_Compressed.Compressed_Certificate}"
            "\n\t\t\t{Signer_Certificate_Compressed.Compressed_Certificate}"
            "\n\t\t\t{Signer_Certificate_Compressed.Public_Key}\n\t\t")), encoding="Hex")
        self.xml_obj.data_sources.data_source.append(ds)

        # Certificate_Not_Before_Raw used by Certificate_Not_Before_MS_Zero
        ds = DataSourceType(name="Certificate_Not_Before_Raw", description=((
            "Start with the current date time for the certificate not before (issue) date.")))
        ds.current_date_time = ""
        self.xml_obj.data_sources.data_source.append(ds)

        # Certificate_Not_Before_MS_Zero used by Certificate_Not_Before
        ds = DataSourceType(name="Certificate_Not_Before_MS_Zero", description=((
                            "Standard compressed certificate validity dates have minutes and seconds set to zero.")))
        ds.date_time_modify = DateTimeModifyType(input="Certificate_Not_Before_Raw")
        ds.date_time_modify.set_fields = DateTimeModifySetFieldsType(minute="0", second="0", fractional_second="0")
        self.xml_obj.data_sources.data_source.append(ds)

        # Certificate_Not_Before used by Cerificate_SN
        ds = DataSourceType(name="Certificate_Not_Before", description=((
            "Standard compressed certificate not before (issue) date can't be on a leap day.")))
        ds.date_time_modify = DateTimeModifyType(input="Certificate_Not_Before_MS_Zero")
        ds.date_time_modify.apply_only_if_leap_day = "True"
        ds.date_time_modify.set_fields = DateTimeModifySetFieldsType(day="28")
        self.xml_obj.data_sources.data_source.append(ds)

        if expiry_years:
            # Certificate_Not_After
            ds = DataSourceType(name="Certificate_Not_After", description=(("")))
            ds.date_time_modify = DateTimeModifyType(input="Certificate_Not_Before")
            ds.date_time_modify.add_period = f"P{expiry_years}Y"
            self.xml_obj.data_sources.data_source.append(ds)

        # Certificate_SN used by serial_number
        ds = DataSourceType(name="Certificate_SN", description=((
            "Device certificate serial number is generated from the certificate validity dates "
            "and public key instead of being stored directly.")))
        ds.crypto_auth_compressed_certificate_sn = CryptoAuthCompressedCertificateSntype(issue_date="Certificate_Not_Before")
        ds.crypto_auth_compressed_certificate_sn.source = "SNSRC_PUB_KEY_HASH"
        ds.crypto_auth_compressed_certificate_sn.size = "16"
        ds.crypto_auth_compressed_certificate_sn.expire_years = f"{expiry_years}"
        ds.crypto_auth_compressed_certificate_sn.public_key = "Device_Public_Key"
        self.xml_obj.data_sources.data_source.append(ds)

        # Process_Info
        ds = DataSourceType(name="Process_Info")
        ds.process_info = ""
        self.xml_obj.data_sources.data_source.append(ds)

        # SN_Hex
        ds = DataSourceType(name="SN_Hex")
        ds.bytes_encode = BytesEncodeType(input="Process_Info.Serial_Number")
        ds.bytes_encode.algorithm = BytesEncodeType.Algorithm()
        ds.bytes_encode.algorithm.hex = BytesEncodeHexType(case="Upper", separator="")
        self.xml_obj.data_sources.data_source.append(ds)

        # Certificate_CN
        ds = DataSourceType(name="Certificate_CN", description="Certificate common name has the device serial number in hex")
        ds.template = TemplateType(definition=TemplateType.Definition(value="sn{SN_Hex}", encoding="String_UTF8"))
        self.xml_obj.data_sources.data_source.append(ds)


class ECC204_TA010_TFLXWPC_XMLUpdates(ECC204_TA010_XMLUpdates):
    def update_with_user_data(self, user_data):
        user_data = json.loads(user_data)
        self.__process_slot_config(user_data)
        self.__process_slot_data(user_data)

    def __process_slot_config(self, user_data):
        self.xml_obj.config_name = f"{self.base_xml} {user_data.get('xml_type')}"

        # configuration_subzone_0
        configuration_subzone_0 = self.xml_obj.configuration_subzone_0
        configuration_subzone_0.io_options.interface = "I2C"
        if user_data.get("sn01"):
            configuration_subzone_0.sn_0_1.value = user_data.get("sn01")
        if user_data.get("sn8"):
            configuration_subzone_0.sn_8.value = user_data.get("sn8")

        # configuration_subzone_1
        configuration_subzone_1 = self.xml_obj.configuration_subzone_1
        configuration_subzone_1.chip_mode.cmos_en = "Fixed_Reference" if user_data.get(
            "fixed_reference") else "VCC_Referenced"
        configuration_subzone_1.chip_mode.clock_divider = "0b11"
        configuration_subzone_1.slot_config3.limited_use = "True" if (
            user_data.get("limited_key_use") == "HMAC") else "False"
        configuration_subzone_1.slot_config3.write_mode = "Encrypted" if user_data.get(
            "encrypt_write") else "Clear"
        configuration_subzone_1.lock = "True"

        # configuration_subzone_2
        configuration_subzone_2 = self.xml_obj.configuration_subzone_2
        configuration_subzone_2.counts_remaining = 10000 - \
            user_data.get("counter_value")
        configuration_subzone_2.lock = "True"

        # configuration_subzone_3
        configuration_subzone_3 = self.xml_obj.configuration_subzone_3
        configuration_subzone_3.device_address = f'0x{user_data.get("device_address")}'
        configuration_subzone_3.lock = "True"

    def __process_slot_data(self, user_data):
        slot_info = user_data.get("slot_info")

        # slot locks
        slot_locks = self.xml_obj.slot_locks
        slot_locks.slot_0 = "True"
        slot_locks.slot_1 = "True" if (slot_info[1].get(
            "slot_lock") == "enabled") else "False"
        slot_locks.slot_2 = "True" if (slot_info[2].get(
            "slot_lock") == "enabled") else "False"
        slot_locks.slot_3 = "True" if (slot_info[3].get(
            "slot_lock") == "enabled") else "False"

        self.xml_obj.data_sources.data_source = []

        # data source - Device generate key
        device_gkey_ds = DataSourceType(name="Device_Public_Key")
        device_gkey_ds.device_generate_key = DeviceGenerateKeyType(
            ecc=GenerateKeyEcctype(curve="secp256r1"), target="Slot 0")
        self.xml_obj.data_sources.data_source.append(device_gkey_ds)

        # data source - hsm random
        hsm_rand_ds = DataSourceType(name="Certificate_SN_Raw")
        hsm_rand_ds.hsm_random = HsmrandomType(size=9, secret_data="False")
        self.xml_obj.data_sources.data_source.append(hsm_rand_ds)

        # data source - Force Non-negative fixed size
        force_nnfs_ds = DataSourceType(name="Certificate_SN")
        force_nnfs_ds.force_nonnegative_fixed_size = DataSourceType.ForceNonnegativeFixedSize(
            input="Certificate_SN_Raw")
        self.xml_obj.data_sources.data_source.append(force_nnfs_ds)

        # data source - current_date_time
        cdt_ds = DataSourceType(name="Certificate_Not_Before")
        cdt_ds.current_date_time = ""
        self.xml_obj.data_sources.data_source.append(cdt_ds)

        # data source - counter
        counter_ds = DataSourceType(name="RSID_Counter")
        counter_ds.counter = CounterType(counter_name="RSID Counter " + user_data.get(
            "ptmc") + "-" + user_data.get("ca_seq_id"), size=9, byte_order="Big", signed="False")
        self.xml_obj.data_sources.data_source.append(counter_ds)

        # data source WPC_Qi_Auth_RSID_Extn_Value
        rsid_extn_ds = DataSourceType(name="WPC_Qi_Auth_RSID_Extn_Value", description=((
            "Composes the wpc-qiAuth-rsid (2.23.148.1.2) extension value manually. "
            "It's an ASN.1 octet string (tag 04) with a fixed size of 9 bytes.")))
        rsid_extn_ds.template = TemplateType(definition=TemplateType.Definition(
            value="04 09 {RSID_Counter}", encoding="Hex"))
        self.xml_obj.data_sources.data_source.append(rsid_extn_ds)

        # Slot 1 - Data_Sources - Full product unit certificate
        self.__process_wpc_certs_data(user_data)

        # data source - bytes pad qi_product_unit_certificate
        qi_puc_bytespad_ds = DataSourceType(name="Qi_Product_Unit_Certificate_Padded")
        qi_puc_bytespad_ds.bytes_pad = BytesPadType(input="Qi_Product_Unit_Certificate.Certificate", fixed_size=BytesPadType.FixedSize(
            output_size=320, pad_byte="0x00", alignment="Pad_Right"))
        self.xml_obj.data_sources.data_source.append(qi_puc_bytespad_ds)

        # data source certificate chain
        qi_chain_ds = DataSourceType(name="Qi_Certificate_Chain")
        qi_chain_ds.qi_certificate_chain = QiCertificateChainType(root_ca_certificate="Qi_Product_Unit_Certificate.CA_Certificate_2",
                                                                  manufacturer_ca_certificate="Qi_Product_Unit_Certificate.CA_Certificate_1",
                                                                  product_unit_certificate="Qi_Product_Unit_Certificate.Certificate")
        self.xml_obj.data_sources.data_source.append(qi_chain_ds)

        # data source chain digest
        qi_chain_digest = DataSourceType(name="Qi_Certificate_Chain_Digest")
        qi_chain_digest.hash = HashType(
            input="Qi_Certificate_Chain", algorithm="SHA256")
        self.xml_obj.data_sources.data_source.append(qi_chain_digest)

        # data source - bytes pad qi certificate chain digest
        qi_ccd_bytespad_ds = DataSourceType(name="Qi_Certificate_Chain_Digest_Padded")
        qi_ccd_bytespad_ds.bytes_pad = BytesPadType(input="Qi_Certificate_Chain_Digest", fixed_size=BytesPadType.FixedSize(
            output_size=64, pad_byte="0x00", alignment="Pad_Right"))
        self.xml_obj.data_sources.data_source.append(qi_ccd_bytespad_ds)

        # Slot 3 - Data_Sources - secret
        if (slot_info[3].get("data")):
            if user_data.get('slot3_kdf_value') != "no_kdf":
                name_value, true_false = ("IKM", "False") if user_data.get('slot3_kdf_value') == "HKDF_Extract" else (
                    ("PRK", "False") if user_data.get('slot3_kdf_value') == "HKDF_Expand" else ("Parent_Key", "False"))
            else:
                name_value, true_false = "Slot_3_Client_Data", "False"
            ds = DataSourceType(name=name_value, description="Slot 3 Storage for a secret key")
            ds.static_bytes = StaticBytesType(secret=SecretBinaryDataType(
                encoding="Hex", key_name="HMAC_Secret_key", algorithm="AES256_GCM"), encrypted=true_false)
            ds.static_bytes.secret.encrypted = true_false
            ds.static_bytes.secret.value = slot_info[3].get("data")
            self.xml_obj.data_sources.data_source.append(ds)

            # Add Process_Info and KDF_Seed if diversified key is checked and Crypto_Auth_Derive_Key selected
            if user_data.get('slot3_kdf_value') in ["Crypto_Auth_Derive_Key"]:
                ds = DataSourceType(name="Process_Info")
                ds.process_info = ""
                self.xml_obj.data_sources.data_source.append(ds)

                ds = DataSourceType(name="KDF_Seed")
                ds.bytes_pad = BytesPadType()
                ds.bytes_pad.input = "Process_Info.Serial_Number"
                ds.bytes_pad.fixed_size = BytesPadType().FixedSize()
                ds.bytes_pad.fixed_size.output_size = "32"
                ds.bytes_pad.fixed_size.pad_byte = "0x00"
                ds.bytes_pad.fixed_size.alignment = FixedSizeAlignment(value="Pad_Right")
                self.xml_obj.data_sources.data_source.append(ds)

            # Add KDF type if diversified key is checked
            if user_data.get('slot3_kdf_value') in ["HKDF_Extract", "HKDF_Expand", "Crypto_Auth_Derive_Key"]:
                ds = DataSourceType(name="KDF") if user_data.get('slot3_kdf_value') in [
                    "HKDF_Extract", "HKDF_Expand"] else DataSourceType(name="Diversified_Key")
                ds.kdf = Kdftype()

                if user_data.get('slot3_kdf_value') == "HKDF_Extract":
                    ds.kdf.hkdf_extract = HkdfextractType()
                    ds.kdf.hkdf_extract.initial_keying_material = "IKM"
                    ds.kdf.hkdf_extract.output_size = "32"
                    ds.kdf.hkdf_extract.hash = "SHA256"
                elif user_data.get('slot3_kdf_value') == "HKDF_Expand":
                    ds.kdf.hkdf_expand = HkdfexpandType()
                    ds.kdf.hkdf_expand.pseudorandom_key = "PRK"
                    ds.kdf.hkdf_expand.info = StringOrDataOrFromSourceType()
                    ds.kdf.hkdf_expand.info.from_source = "False"
                    ds.kdf.hkdf_expand.info.encoding = "Hex"
                    ds.kdf.hkdf_expand.output_size = "32"
                    ds.kdf.hkdf_expand.hash = "SHA256"
                else:
                    ds.kdf.crypto_auth_derive_key = CryptoAuthDeriveKeyType()
                    ds.kdf.crypto_auth_derive_key.parent_key = "Parent_Key"
                    ds.kdf.crypto_auth_derive_key.target_key = "3"
                    ds.kdf.crypto_auth_derive_key.seed = StringOrDataOrFromSourceType()
                    ds.kdf.crypto_auth_derive_key.seed.from_source = "True"
                    ds.kdf.crypto_auth_derive_key.seed.value = "KDF_Seed"
                    ds.kdf.crypto_auth_derive_key.output_size = "32"
                self.xml_obj.data_sources.data_source.append(ds)

        # data source writer
        self.xml_obj.data_sources.writer = []
        self.xml_obj.data_sources.writer.append(
            DataSourcesWriterType(source_name="Qi_Product_Unit_Certificate_Padded", target="Slot 1"))
        self.xml_obj.data_sources.writer.append(DataSourcesWriterType(
            source_name="Qi_Certificate_Chain_Digest_Padded", target="Slot 2"))

        # Writer For Slot 3
        if (slot_info[3].get("data")):
            if user_data.get('slot3_kdf_value') != "no_kdf":
                wr = DataSourcesWriterType(source_name="KDF", target="Slot 3") if user_data.get('slot3_kdf_value') in [
                    "HKDF_Extract", "HKDF_Expand"] else DataSourcesWriterType(source_name="Diversified_Key", target="Slot 3")
            else:
                wr = DataSourcesWriterType(source_name="Slot_3_Client_Data", target="Slot 3")
                self.xml_obj.data_sources.writer.append(DataSourcesWriterType(
                    source_name="Slot_3_Client_Data", target="Slot 3"))
            self.xml_obj.data_sources.writer.append(wr)

        # data source wrapped key
        self.xml_obj.data_sources.wrapped_key = []

    def __process_wpc_certs_data(self, user_data):
        root_key = None
        mfg_key = None
        ptmc_code = user_data.get('ptmc')
        ca_seq_id = user_data.get('ca_seq_id')
        qi_id = user_data.get('qi_id')
        puc_pubkey = get_device_public_key(None)
        puc_pubkey = ec.EllipticCurvePublicNumbers(
            x=int(puc_pubkey[:64], 16),
            y=int(puc_pubkey[64:], 16),
            curve=ec.SECP256R1()).public_key(get_backend())

        # Generate root certificate
        root_key = TPAsymmetricKey(key=root_key)
        root_key.get_private_pem()
        root_params = WPCRootCertParams(ca_key=root_key.get_private_pem())
        wpc_root_crt = create_wpc_root_cert(
            root_key.get_private_key(),
            root_params.root_cn,
            root_params.root_sn)

        # Generate Manufacturer certificate
        mfg_key = TPAsymmetricKey(key=mfg_key)
        mfg_key.get_private_pem()
        wpc_mfg_crt = create_wpc_mfg_cert(
            int(ptmc_code, 16),
            int(ca_seq_id, 16),
            int(qi_id),
            mfg_key.get_public_key(),
            root_key.get_private_key(),
            wpc_root_crt)

        # Generate Product Unit certificate
        wpc_puc_crt = create_wpc_puc_cert(
            qi_id=int(qi_id),
            rsid=int.from_bytes(os.urandom(4), byteorder='big'),
            public_key=puc_pubkey,
            ca_private_key=mfg_key.private_key,
            ca_certificate=wpc_mfg_crt)

        puc_key = TPAsymmetricKey()
        puc_key.set_public_key(puc_pubkey)

        cert_chain_text = f'\nSubject: CN={get_certificate_CN(wpc_mfg_crt)}\n' + \
            f'Issuer: CN={get_certificate_issuer_CN(wpc_mfg_crt)}\n' + \
            str(wpc_mfg_crt.public_bytes(
                encoding=serialization.Encoding.PEM), 'utf-8') + \
            f'\n\nSubject: CN={get_certificate_CN(wpc_root_crt)}\n' + \
            f'Issuer: CN={get_certificate_issuer_CN(wpc_root_crt)}\n' + \
            str(wpc_root_crt.public_bytes(
                encoding=serialization.Encoding.PEM), 'utf-8')\

        cert_data = {
            "name": "Qi_Product_Unit_Certificate",
            "desc": "Product Unit Full Certificate",
            "cert_chain": cert_chain_text.replace("\n", "\n\t\t\t\t\t"),
            "hash": "SHA256",
            "version": "V3",
            "serial_number": "Certificate_SN",
            "not_valid_before": "Certificate_Not_Before",
            "not_valid_after": "9999-12-31T23:59:59",
            "cert_common_name": get_certificate_CN(wpc_puc_crt),
            "subject_public_key_info": "Device_Public_Key",
            "extensions": {
                "extension": [{"extn_id": "2.23.148.1.2",
                               "critical": "True",
                                "from_source": "True",
                                "extn_value": "WPC_Qi_Auth_RSID_Extn_Value"}],
            },
            "expiry_years": 0,
        }
        ds = self.process_cert_xml(cert_data=cert_data)
        self.xml_obj.data_sources.data_source.append(ds)


if __name__ == "__main__":
    pass
