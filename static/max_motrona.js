import * as con from './controllers/daemon_connection.js'

export {
    refreshAllData,
    setMinMode,
    sendRequest,
    sendInt,
    sendFloat,
    sendString,
    sendARequest,
    toggle,
    getToggles
}


let minMode = false;


function setMinMode() {
    minMode = true;
}

async function refreshAllData(url, prefix) {
    let hwData = await con.getStatus(url)

    if (hwData) {
        con.setConnected(prefix + "_connect_status", true);
        updateUi(prefix, hwData);
    }
    else {
        con.setConnected(prefix + "_connect_status", false);
    }
}


async function sendRequest(url, prefix, spinner, request ) {
    let hwData = await con.sendRequestAndSpin(url, request, spinner);
    updateUi(prefix, hwData);
}

function getToggles(prefix, hwData) {
    con.getEl(prefix + "_debug_rs232").checked = hwData["debug_rs232"];
    con.getEl(prefix + "_debug_motrona").checked = hwData["debug_motrona"];
    con.getEl(prefix + "_debug_broker").checked = hwData["debug_broker"];
}

function updateElement(id, value) {
    con.getEl(id).innerText = value;
}

function updateUi(prefix, hwData) {
    con.getEl(prefix + '_request_id').innerText = hwData["request_id"];
    con.getEl(prefix + '_request_finished').innerText = hwData["request_finished"];
    con.getEl(prefix + '_target_charge').innerText = hwData["target_charge(nC)"];
    con.getEl(prefix + '_counts').innerText = hwData["counts"];
    con.getEl(prefix + '_status').innerText = hwData["status"];
    con.getEl(prefix + '_charge').innerText = hwData["charge(nC)"];
    updateElement(prefix + '_counting_time', hwData["counting_time(msec)"]);
    updateElement(prefix + '_current', hwData["current(nA)"]);
    updateElement(prefix + '_error', hwData["error"]);

    if (!minMode) {
        updateElement(prefix + '_pulse_to_counts', hwData["counter_factor"]);
        updateElement(prefix + '_analog_end', hwData["analog_end"]);
        updateElement(prefix + '_analog_start', hwData["analog_start"]);
        updateElement(prefix + '_analog_offset', hwData["analog_offset"]);
        updateElement(prefix + '_analog_gain', hwData["analog_gain"]);
        updateElement(prefix + '_preselection_1', hwData["preselection_1"]);
        updateElement(prefix + '_preselection_2', hwData["preselection_2"]);
        updateElement(prefix + '_preselection_3', hwData["preselection_3"]);
        updateElement(prefix + '_preselection_4', hwData["preselection_4"]);
        updateElement(prefix + '_target_counts', hwData["target_counts"]);
        updateElement(prefix + '_firmware_version', hwData["firmware_version"]);
        updateElement(prefix + '_counts_to_charge', hwData["nc_to_pulses_conversion_factor"]);
        updateElement(prefix + '_count_mode', hwData["count_mode"]);
        updateElement(prefix + '_input_pulse_type', hwData["input_pulse_type"]);
        con.setBadgeState(prefix + "_error_status", hwData["error"] != "Success");
        updateElement(prefix + '_debug_rs232', hwData["debug_rs232"]);
        updateElement(prefix + '_debug_motrona', hwData["debug_motrona"]);
        updateElement(prefix + '_debug_broker', hwData["debug_broker"]);
        con.getEl(prefix + "_debug_rs232").checked = hwData["debug_rs232"];
        con.getEl(prefix + "_debug_motrona").checked = hwData["debug_motrona"];
        con.getEl(prefix + "_debug_broker").checked = hwData["debug_broker"];
    }
}


async function toggle(url, prefix, id, requestKey) {
    let value = con.getEl(prefix + "_" +id + "_request").checked;
    let request = {};
    request[requestKey] = value;
    await sendRequest(url,prefix, prefix +"_" +id + "_spinner", request);
}

//these could be made generic if updateUi is passed in as an argument 
function sendARequest(url, prefix, id ,request) {
    let jsonRequest =  JSON.parse(request);
    sendRequest(url,prefix, prefix +"_" +id + "_spinner", jsonRequest);
}

function sendInt(url,prefix, id, requestKey) {
    let value = parseInt(con.getEl(prefix + "_" +id + "_request").value);
    if (!Number.isInteger(value)) {
        alert("This is not a valid integer number");
        return;
    }
    let request = {};
    request[requestKey] = value;
    sendRequest(url,prefix, prefix +"_" +id + "_spinner", request);
}

function sendString(url,prefix, id, requestKey) {
    let value = con.getEl(prefix + "_" +id + "_request").value;
    if (value === "Choose...") { return; }
    let request = {};
    request[requestKey] = value;
    sendRequest(url,prefix, prefix +"_" +id + "_spinner", request);
}

function sendFloat(url,prefix, id, requestKey) {
    let value = parseFloat(con.getEl(prefix + "_" +id + "_request").value);
    if (isNaN(value)) {
        alert("This is not a valid floating point number");
        return;
    }
    let request = {};
    request[requestKey] = value;
    sendRequest(url,prefix, prefix +"_" +id + "_spinner", request);
}