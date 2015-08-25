statsPage = u"""<html>

<head>
	<title>Stats Page</title>
	<link rel="stylesheet" type="text/css" href="static/stats.css">
	<script src="static/jquery-2.1.4.js"></script>
	<script src="static/stats.js" charset="utf-8"></script>
</head>
<body>
	<span class="PageHead">Device Stats</span>
	<span class = "DeviceSwitcher">
		<br>
		<select class = "DeviceSwitcher" onchange="if (this.value != null) {{addStats(this.value); this.selectedIndex = 0}}">
        <option value="null">Add Device\u2026</option>
		</select>
	</span>
	<br>
	<div class = "optionsMenu">
		<h2>Device Management:</h2>
		<div class = "optionButtons">
			<form onsubmit="sendCommand(null); return false;">
                <span style="display:inline;">Target Device:</span>
                <input type = "text" id = "DeviceList"><br>
                <input type = "text" id = "CommandEntry">
                <input type = "submit" id = "CommandSend" value = "Send"> <br>
			</form>
		</div>
        <div class = "noPadding" id = "terminalRoot">
        </div>
	</div>
    <div class = "noPadding" id = "statsRoot">
    	<div class = "classStats">
            <button onclick="remDev(this.parentElement.id)">X</button>
            <h2>Device <span class = "DeviceName">{DeviceName}</span>:</h2>
            <p>Hostname: <span class = "DeviceName">{DeviceName}</span></p>
            <p>IPv4 Address: <span class = "IPv4Address">{IPV4}</span></p>
            <p>IPv6 Address: <span class = "IPv6Address">{IPV6}</span></p>
            <p>Further Info: <span class = "UserString">{UString}</span></p>
            <p>Last Updated: <span class = "LastUpdate">{LastUpdate}</span></p>
            <h2>Device Vitals</h2>
            <p>Temperature: <span class = "TemperatureValue">{Temp}</span></p>
            <p>Uptime: <span class = "UptimeValue">{Uptime}</span></p>
            <p>Free Disk Space: <span class = "FreeDisk">{FreeDisk}</span></p>
            <p>Used Disk Space: <span class = "UsedDisk">{UsedDisk}</span></p>
        </div>
    </div>
</body>

</html>

"""

noDevice = """<html>
<head>
    <title>Choose a Device</title>
    <link rel="stylesheet" type="text/css" href="static/stats.css">
	<script src="static/jquery-2.1.4.js"></script>
	<script src="static/stats.js" charset="utf-8"></script>
<body>
<h2>Please select a device:</br></h2>
<select class = "DeviceSwitcher" style="float:left;width:250px;" onchange="location.href = '?device=' + this.value">
</select>
"""