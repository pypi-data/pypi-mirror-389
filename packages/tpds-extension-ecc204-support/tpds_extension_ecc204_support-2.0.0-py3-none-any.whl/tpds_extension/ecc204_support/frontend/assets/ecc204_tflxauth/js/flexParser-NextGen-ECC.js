ws = new WebSocket("ws://localhost:1302/websocket");
let formNameMain = slotdataform;

let keyLoadConfig = {
  0: "noLoad",
  1: "cert",
  2: "load",
  3: "load",
};

let slotsize = {
  0: "32",
  1: "320",
  2: "64",
  3: "32",
  4: "64",
};

let tflexSlotType = {
  0: "private",
  1: "cert",
  2: "general",
  3: "secret",
};

let slotValidateDict = {
  0: "none",
  1: "none",
  2: "none",
  3: "none",
};

function validateSlotOpt() {
  let generateXml = true;
  for (let i = 0; i < 3; i++) {
    if (slotValidateDict[i] == "invalid") {
      alert("Enter valid data in slot " + i);
      generateXml = false;
    }
  }
  return generateXml;
}

function verify_slot_data_bytes(slot_data, slot_number) {
  let formatedString = slot_data
    .replaceAll(" ", "")
    .replaceAll("\n", "")
    .replaceAll("\r", "")
    .replaceAll("\t", "")
    .replaceAll("0x", "")
    .replaceAll(",", "")
    .toUpperCase();
  let slotDataValid = false;

  if (slotsize[slot_number] * 2 == formatedString.length) {
    if (is_hex(formatedString)) {
      let string = "Data valid,";
      string += " entered values are:\n";
      string += prettyPrintHex(formatedString, 32);
      slotDataValid = true;
    } else {
      alert("Error: Data contains non-hex characters");
      slotDataValid = false;
    }
  } else {
    if (slot_number != 5)
      alert(
        "The slot" +
          slot_number +
          "expects: " +
          slotsize[slot_number] +
          "bytes" +
          "\nYou have entered: " +
          formatedString.length / 2 +
          "bytes"
      );
    else
      alert(
        "The custom root expects: " +
          slotsize[slot_number] +
          "bytes" +
          "\nYou have entered: " +
          formatedString.length / 2 +
          "bytes"
      );
    slotDataValid = false;
  }
  return slotDataValid;
}

function get_clean_slot_data_bytes(slot_data) {
  return slot_data
    .replaceAll(" ", "")
    .replaceAll("\n", "")
    .replaceAll("\r", "")
    .replaceAll("\t", "")
    .replaceAll("0x", "")
    .replaceAll(",", "")
    .toUpperCase();
}

function gererateXML(xml_type) {
  let secretSlots = [3];
  let XMLContainsSecrets = false;
  let isManIdValid = true;
  let certOptValue = "No certs";

  let device_address = document.getElementById("deviceAddress").value || 39;
  if (Number("0x" + device_address) > Number("0x7F")) {
    alert("Invalid Device address");
    return false;
  }
  let sn01 = document.getElementById("sn01").value || "0123";
  sn01 = sn01.padStart(4, "0");
  let sn8 = document.getElementById("sn8").value || "EE";
  sn8 = sn8.padStart(2, "0");
  let health_test = document.getElementById("health_test").checked;
  let fixed_reference = document.getElementById("fixedReference").checked;
  let counter_value = document.getElementById("counterVal").value;
  counter_value = counter_value ? 10000 - counter_value : 0;
  let devIface = getFormRadioValue(formNameMain, "devIface");
  let compliance = document.getElementById("compliance").checked;
  let limited_key_use = "disabled";
  let diversified_key = document.getElementById("diversified_key");
  diversified_key = diversified_key ? diversified_key.checked : false;
  if (getFormRadioValue(formNameMain, "limitedUse")) {
    limited_key_use = getFormRadioValue(formNameMain, "limitedUse");
  } else {
    alert("Select an option for Limited Key Use.");
    return false;
  }

  slot3_kdf_value = "none";
  if (getFormRadioValue(formNameMain, "slot3KDFValue")) {
    slot3_kdf_value = getFormRadioValue(formNameMain, "slot3KDFValue");
  } else {
    alert("Select an option for KDF type in slot 3.");
    return false;
  }

  let jsObj = { base_xml: "ECC204_TFLXAUTH" };
  Object.assign(jsObj, { ["xml_type"]: xml_type });
  Object.assign(jsObj, { ["interface"]: devIface });
  Object.assign(jsObj, { ["device_address"]: device_address });
  Object.assign(jsObj, { ["health_test"]: health_test });
  Object.assign(jsObj, { ["fixed_reference"]: fixed_reference });
  Object.assign(jsObj, { ["limited_key_use"]: limited_key_use });
  Object.assign(jsObj, { ["encrypt_write"]: xml_type === "prod_xml" });
  Object.assign(jsObj, { ["diversified_key"]: diversified_key });
  Object.assign(jsObj, { ["compliance"]: compliance });
  Object.assign(jsObj, { ["counter_value"]: counter_value });
  Object.assign(jsObj, { ["sn01"]: sn01 });
  Object.assign(jsObj, { ["sn8"]: sn8 });
  Object.assign(jsObj, { ["slot3_kdf_value"]: slot3_kdf_value });

  // Update the slots with user's data.
  let jsSlotsData = [];
  for (let i = 0; i < 4; i++) {
    let jsSlot = { slot_id: i };
    Object.assign(jsSlot, { ["slot_type"]: tflexSlotType[i] });
    Object.assign(jsSlot, { ["key_load_config"]: keyLoadConfig[i] });
    let slotLock = document.getElementById("slotlock" + i.toString());
    let slot_lock_data =
      slotLock !== null ? (slotLock.checked ? "enabled" : "disabled") : null;
    Object.assign(jsSlot, { ["slot_lock"]: slot_lock_data });

    if (keyLoadConfig[i] == "noLoad") {
    } else if (keyLoadConfig[i] == "load") {
      slot_data_bytes = getFormDataSlot(formNameMain, i);
      if (slot_data_bytes != null) {
        if (verify_slot_data_bytes(slot_data_bytes, i)) {
          slot_data_bytes = get_clean_slot_data_bytes(slot_data_bytes);
          slotValidateDict[i] = "valid";
        } else {
          return;
        }
      }
      Object.assign(jsSlot, { ["data"]: slot_data_bytes });
    } else if (keyLoadConfig[i] === "cert") {
      // Getting value from selection button
      certOptValue = getFormRadioValue(formNameMain, "slot" + i + "certopt");
      let dev_sig_inputs = [1, 12]; //1-Device 12-signer
      if (certOptValue === "custCert" && i === 1) {
        if (
          document.getElementById(dev_sig_inputs[0] + "certname").value == "" ||
          document.getElementById(dev_sig_inputs[0] + "certcommonname").value ==
            "" ||
          document.getElementById(dev_sig_inputs[0] + "certyear").value == "" ||
          document.getElementById(dev_sig_inputs[1] + "certname").value == "" ||
          document.getElementById(dev_sig_inputs[1] + "certcommonname").value ==
            "" ||
          document.getElementById(dev_sig_inputs[1] + "certyear").value == ""
        ) {
          alert(
            "For Custom Certificates, all certificate fields to be populated!. Please verify fields in Slot" +
              i +
              "."
          );
          return;
        } else if (i == 1) {
          if (
            document.getElementById("4certname").value == "" ||
            document.getElementById("4certcommonname").value == ""
          ) {
            alert(
              "For Custom Certificates, all certificate fields to be populated!. Please verify Custom root Information."
            );
            return;
          }

          slot4_data_bytes = getFormDataSlot(formNameMain, 4);
          if (slot4_data_bytes == null) {
            alert(
              "Custom root public key data is not complete... Please check and try again."
            );
            return;
          } else {
            if (verify_slot_data_bytes(slot4_data_bytes, 4))
              slot4_data_bytes = get_clean_slot_data_bytes(slot4_data_bytes);
            else return;
          }
        }
      }

      Object.assign(jsSlot, { ["cert_type"]: certOptValue });

      if (certOptValue === "custCert") {
        //device
        Object.assign(jsSlot, {
          ["d_cert_org"]: document.getElementById(i + "certname").value,
        });
        Object.assign(jsSlot, { ["d_cert_cn"]: "sn0123030405060708EE" });
        Object.assign(jsSlot, {
          ["d_cert_cn"]: document.getElementById(i + "certcommonname").value,
        });
        Object.assign(jsSlot, {
          ["d_cert_expiry_years"]: document.getElementById(i + "certyear")
            .value,
        });
        //signer
        Object.assign(jsSlot, {
          ["s_cert_org"]: document.getElementById(
            dev_sig_inputs[1] + "certname"
          ).value,
        });
        Object.assign(jsSlot, { ["s_cert_cn"]: "sn0123030405060708EE" });
        Object.assign(jsSlot, {
          ["s_cert_cn"]: document.getElementById(
            dev_sig_inputs[1] + "certcommonname"
          ).value,
        });
        Object.assign(jsSlot, {
          ["s_cert_expiry_years"]: document.getElementById(
            dev_sig_inputs[1] + "certyear"
          ).value,
        });
        //ca
        Object.assign(jsSlot, {
          ["signer_ca_org"]: document.getElementById("4certname").value,
        });
        Object.assign(jsSlot, {
          ["signer_ca_cn"]: document.getElementById("4certcommonname").value,
        });
        Object.assign(jsSlot, { ["signer_ca_pubkey"]: slot4_data_bytes });
      }
    } else {
      console.error("Config Error" + i + keyLoadConfig[i]);
    }

    // Code to change mode secret slots to random if not used
    if (secretSlots.includes(i)) {
      let status = getFormRadioValue(formNameMain, "slot" + i + "dataopt");
      if (status && status !== "unused") {
        XMLContainsSecrets = true;
      }
    }
    jsSlotsData.push(jsSlot);
  }

  Object.assign(jsObj, { ["slot_info"]: jsSlotsData });

  partNumberString = document
    .getElementById("partNumberId")
    .value.toUpperCase();
  if (partNumberString == "") partNumberString = "ECC204-MAHAA-T";
  Object.assign(jsObj, { ["part_number"]: partNumberString });

  let useCaseValid = validateUseCaseSlots();
  let slotDataValidity = validateSlotOpt();

  if (
    useCaseValid === false &&
    slotDataValidity === true &&
    isManIdValid === true
  ) {
    if (XMLContainsSecrets) {
      // alert("Secrets in the generated XML output file are not encrypted. \n\nThe file needs to be encrypted before it can be sent over to Microchip provisioning service.");
    }
    if (xml_type === "proto_xml" || xml_type === "prod_xml") {
      ecc204_tflxauth_json(JSON.stringify(jsObj));
    } else {
      ecc204_tflxauth_proto_prov(JSON.stringify(jsObj));
    }
  }
}

function setRadioValue(form, radioName, radioSelect) {
  let radios = form.elements[radioName];

  for (let i = 0; i < radios.length; i++) {
    if (radios[i].value == radioSelect) {
      radios[i].checked = true;
    } else {
      radios[i].checked = false;
    }
  }

  return null;
}

function getFormRadioValue(form, name) {
  let radios = form.elements[name];

  for (let i = 0; i < radios.length; i++) {
    if (radios[i].checked == true) {
      return radios[i].value;
    }
  }

  return null;
}

function getFormDataSlot(form, slotNumber) {
  let radioName = "slot" + slotNumber + "dataopt";
  let status;
  let slotData = null;

  if (null != (status = getFormRadioValue(form, radioName))) {
    if (status == "unused") {
      slotData = null;
    } else if (status == "hexdata") {
      slotData = document.getElementById(radioName + "id").value;
    } else if (status == "pemdata") {
      slotData = document.getElementById(radioName + "id").value;
    } else {
      console.error("Unknown radio value");
      slotData = null;
    }
  } else {
    console.error("Radio Value fetch error");
  }
  return slotData;
}

function getDataFromSlot(radioName) {
  let status;
  let slotData = null;

  if (null != (status = getFormRadioValue(formNameMain, radioName))) {
    if (status == "unused") {
      //Do nothing?
      slotData = null;
    } else if (status == "hexdata") {
      slotData = document.getElementById(radioName + "id").value;
    } else if (status == "pemdata") {
      slotData = null;
    } else {
      console.error("Unknown radio value");
      slotData = null;
    }
  } else {
    console.error("Radio Value fetch error");
  }
  return slotData;
}

String.prototype.replaceAll = function (search, replacement) {
  let target = this;
  return target.replace(new RegExp(search, "g"), replacement);
};
