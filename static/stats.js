/*NOTE: Currently this script (and jquery) will fail spectacularly if used on Internet Explorer 8 or older.
I doubt this is a major issue but let me know if compatibility is a major goal here.*/
var clientSocket;
var clientState;
var targetJson;
var socketConnected = 0;
var statsDiv = '<div class = "classStats"><button onclick="remDev(this.parentElement.id)">X</button><h2>Device <span class = "DeviceName"></span>:</h2><p>Hostname: <span class = "DeviceName">  </span></p><p>IPv4 Address: <span class = "IPv4Address"> </span></p><p>IPv6 Address: <span class = "IPv6Address"> </span></p><p>Further Info: <span class = "UserString"> </span></p><p>Last Updated: <span class = "LastUpdate"> </span></p><h2>Device Vitals</h2><p>Temperature: <span class = "TemperatureValue"> </span></p><p>Uptime: <span class = "UptimeValue"> </span></p><p>Free Disk Space: <span class = "FreeDisk"> </span></p><p>Used Disk Space: <span class = "UsedDisk"> </span></p></div>';
//0 for Celsius, 1 for Fahrenheit
function formatTemperature(x1,unit){
	if (unit==0) {
		return String(x1) + "°C";
	}
	else {
		return String(x1) + "°F";
	}
}

//takes an integer and returns it as a string that is always at least two digits.
function alwaysTwoDigit(num){
	if (num < 10 && num >= 0){
		return "0" + String(num);
	}
	else{
		return String(num);
	}
}
function sendCommand(value){
	var cmd = value;
	var target = $("#DeviceList").val();
	if (value == null){
		cmd = $("#CommandEntry").val();
		$("#CommandEntry").val("");
	}
	try{
		clientSocket.send("CMD:" + target + ":" + cmd);
	}
	catch(ex){
		console.log("Failed to send command.");
	}
}
function sendSig(id, tgt){
	try{
		clientSocket.send("SIGINT:" + tgt + ":" + id);
	}
	catch(ex){
		console.log("Network issues prevented the SIGINT from being sent.")
	}
}
//Takes uptime (in seconds) and adapts it to 0d00h00m00s format.
function formatUptime(uptime) {
	upRem = uptime;
	upDays = Math.floor(upRem / 86400);
	upRem -= upDays * 86400;
	upHours = Math.floor(upRem / 3600);
	upRem -= upHours * 3600;
	upMins = Math.floor(upRem / 60);
	upRem -= upMins * 60;
	upSecs = Math.floor(upRem);
	upString = String(upDays) + "d" + alwaysTwoDigit(upHours) + "h" + alwaysTwoDigit(upMins) + "m" + alwaysTwoDigit(upSecs) + "s";
	return upString;
}
function formatStorage(raw) {
	return String((raw/1048576).toFixed(2)) + " GB";
}
function getQueryVars()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

function connectSocket(){
	clientState = "";
	try{
		clientSocket.close();
	}
	catch(whatever){
		//we really don't care if this fails.
	}
	clientSocket = new WebSocket("ws://" + location.host + "/csock");
	clientSocket.onopen = function(event){
		socketConnected = 1;
		clientSocket.send("MON:");
	}
	clientSocket.onmessage = function(event){
		var i = event.data.indexOf(':');
		var msg = [event.data.slice(0,i), event.data.slice(i+1)];
		if (clientState == "OK"){
			if (msg[0] == "STA"){
				updateStats(JSON.parse(msg[1]))
			}
			if (msg[0] == "OUT"){
				updateTerms(JSON.parse(msg[1]))
			}
			if (msg[0] == "LST"){
				updateList(JSON.parse(msg[1]));
			}
		}
		if (clientState == ""){
			if (event.data == "OK"){
				clientState = "OK";
				subscribeAll();
                clientSocket.send("LST:");
			}
		}
	}
	clientSocket.onclose = function(event){
		socketConnected = 0;
		setTimeout(connectSocket(), 1000)

	}
}

function updateStats(deviceInfo){
    statsBox = $("#" + deviceInfo.h);
	if (statsBox.length==0){
			statsBox = $(statsDiv).appendTo('#statsRoot');
			statsBox.prop("id", deviceInfo.h);
		}
	statsBox.find(".TemperatureValue").text(formatTemperature(deviceInfo.t,0));
	statsBox.find(".UptimeValue").text(formatUptime(deviceInfo.u));
	statsBox.find(".DeviceName").text(deviceInfo.h);
	statsBox.find(".IPv4Address").text(deviceInfo.i4);
	statsBox.find(".IPv6Address").text(deviceInfo.i6);
	statsBox.find(".UserString").text(deviceInfo.s);
	statsBox.find(".LastUpdate").text(deviceInfo.d);
	statsBox.find(".FreeDisk").text(formatStorage(deviceInfo.df));
	statsBox.find(".UsedDisk").text(formatStorage(deviceInfo.du));
}
function updateList(list){
	var selectObj = $('select.DeviceSwitcher');
    selectObj.find('option')
    	.remove()
    	.end()
	var listlen = list.length;
	selectObj.append($('<option>', {
		value : 'null',
		text : 'Add Device...'
	}));
	for (var i = 0; i < listlen; i++){
		selectObj.append($('<option>', {
			value : list[i],
			text : list[i]
		}));
	}
	selectObj.val('null');
}
function remDev(id){
	clientSocket.send("REM:" + id);
	deleteDiv("#" + id);
}
function deleteDiv(id){
	var div = $(id);
	div.addClass('removeDiv');
	div.one('webkitAnimationEnd oanimationend msAnimationEnd animationend',
	function(e){
		div.remove();
	});
}
function subscribeAll(){
	devs = $('#statsRoot').children();
	for (var i = 0; i < devs.length; i++){
		addStats($(devs[i]).attr('id'));
	}
}
function addStats(target){
	if (socketConnected==1) {
		clientSocket.send("ADD:" + target);
	}
}
function updateTerms(termInfo){
    //update terminal windows//
	var escapedText = termInfo[2].replace(/&/g, '&amp;')
						  .replace(/>/g, '&gt;')
						  .replace(/</g, '&lt;')
						  .replace(/\n/g, '<br>')
						  // + ' > div.terminal'
	selection = $(".HOST_" + termInfo[1] + ".TERM_" + (termInfo[0]));
	if (selection.length == 0) {
		autoScrollCode = '<input type = "checkbox" class = "autoScroll toggleBox termOption" checked><span class = "termOption">Auto-Scroll</span></input>'
		headerCode = '<span class = "termHeader">' + termInfo[1] + '</span>';
		sigButtonCode = '<button class = "exitTerm " onClick = "sendSig(' + termInfo[0] +', \'' + termInfo[1] + '\')">^C</button>';
		closeButtonCode = '<button class = "exitTerm " onClick = "deleteDiv(\'.HOST_'+ termInfo[1] + '.TERM_' + termInfo[0] + '\')">X</button>';
		termdiv = '<div class = "terminal"></div>';
		$("#terminalRoot").append('<div class = "noPadding termDiv HOST_' + termInfo[1] + ' TERM_' + termInfo[0] + '">' + headerCode + closeButtonCode + sigButtonCode + autoScrollCode + termdiv + '</div>');
		selection = $(".HOST_" + termInfo[1] + ".TERM_" + (termInfo[0]));
	}
	ter = selection.find('.terminal')
	ter.append(escapedText);
	if(selection.find('.autoScroll').is(':checked')){
		var height = ter.prop('scrollHeight');
		ter.scrollTop(height);
	}
}
//DOM ready function
$(function() {
	qvars = getQueryVars();
	targetJson = qvars.device;
    $(".classStats").prop("id", targetJson);
	connectSocket()
});