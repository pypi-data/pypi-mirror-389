ws = new WebSocket("ws://localhost:1302/websocket");

function send(msg, _handle) {
  if (
    typeof ws == "undefined" ||
    ws.readyState === undefined ||
    ws.readyState > 1
  ) {
    console.log("send - reopen socket");
    ws = new WebSocket("ws://localhost:1302/websocket");
  } else {
    ws.onmessage = _handle;
    ws.send(JSON.stringify(msg));
    // console.log("send sent:", JSON.stringify(msg));
  }
  console.log("handle: ", _handle);
  ws.onopen = function () {
    console.log(_handle);
    console.log("socket re-opened");
    ws.onmessage = _handle;
    ws.send(JSON.stringify(msg));
    // console.log("send sent (re-open path):", JSON.stringify(msg));
  };
}

function send_message(id, args, _handle) {
  var msg = { msg_id: id, parameters: args };
  console.log("send_message", msg);
  send(msg, _handle);
}

function open_link(mdfile) {
  send_message(3, [String(mdfile)], open_link_handle);
}

function open_link_handle(evt) {
  response = handle_message(evt);
  console.log(response);
}

function handle_message(evt) {
  var msg = JSON.parse(evt.data);
  if (msg.status == "OK") {
    console.log("handle_message: ", msg.response, "OK");
  } else if (msg.status == "error") {
    console.log("handle_messag: ERROR: ", msg.response);
  }
  console.log("hanlde_message - close socket");
  ws.close();
  console.log("handle_message - close socket");
  var response = msg.response;
  console.log("handle_message - response: ", response);
  return response;
}

function ecc204_tflxwpc_json(jsonOBJ) {
  console.log([String(jsonOBJ)]);
  fetch("http://localhost:5001/ecc204/generate_tflxwpc_xml", {
    method: "POST",
    body: String(jsonOBJ),

    headers: {
      "Content-Type": "application/json",
    },
  })
    .then(function (res) {
      return res.json();
    })
    .then(function (data) {
      if (["ABORT", "OK"].includes(data.response) === false) {
        alert(
          "Response: " +
            data.response +
            "\n\nStatus Message:\n" +
            data.status.replace(/(<([^>]+)>)/gi, "")
        );
      }
    });
}

function ecc204_tflxwpc_proto_prov(jsonOBJ) {
  console.log([String(jsonOBJ)]);
  fetch("http://localhost:5001/ecc204/provision_tflxwpc_device", {
    method: "POST",
    body: String(jsonOBJ),

    headers: {
      "Content-Type": "application/json",
    },
  })
    .then(function (res) {
      return res.json();
    })
    .then(function (data) {
      if (data.response !== "OK") {
        alert(
          "Response: " +
            data.response +
            "\n\nStatus Message:\n" +
            data.status.replace(/(<([^>]+)>)/gi, "")
        );
      }
    });
}

// check validity for monotonic counter value
const input_counter = document.querySelector("#counterVal");
input_counter.addEventListener("change", (e) => {
  if (!e.target.checkValidity()) {
    e.target.value = "";
  }
  counter_val = document.getElementById("counterVal").value
    ? document.getElementById("counterVal").value
    : 10000;
  document.getElementById("limitedUseHMAC").title =
    "Connect HMAC Key to Monotonic Counter for " + counter_val + " counts";
});

// check validity for device address
const input_address = document.querySelector("#deviceAddress");
input_address.addEventListener("change", (e) => {
  if (!e.target.checkValidity()) {
    e.target.value = "";
  }
  if (e.target.value) {
    const value = parseInt(e.target.value, 16);
    if (value < 1 || value > 127) {
      e.target.value = "";
    }
  }
});
