local Content = [[==
<!doctype html>
<html>
  <head>
    <meta charset=utf-8>
    <title>subspace reactor</title>
	<script>
	  
	  let CBL1_power = 2
	  let CBL1_pressure = 0
	  let CBL1_stress = 0
	  let CBL1_integrityloss = 0
	  let CBL1_PressurePurge = 0
	  
	  let CBL2_power = 2
	  let CBL2_pressure = 0
	  let CBL2_stress = 0
	  let CBL2_integrityloss = 0
	  let CBL2_PressurePurge = 0
	  
	  let CBL3_power = 2
	  let CBL3_pressure = 0
	  let CBL3_stress = 0
	  let CBL3_integrityloss = 0
	  let CBL3_PressurePurge = 0
	  
	  let fan1_power = 1
	  let fan2_power = 1
	  let fan3_power = 1
	  let fan4_power = 1
	  let fan5_power = 1
	  let fan6_power = 1
	  
	  let coolant_pump1_power = 1
	  let coolant_pump1_Stability = 100
	  
	  let coolant_pump2_power = 1
	  let coolant_pump2_Stability = 100
	  
	  let coolant_pump3_power = 1
	  let coolant_pump3_Stability = 100
	  
	  let PEA_extraction_rate = 2
	  let PEA_stress = 0
	  let power_generation = 0
	  
	  let atmosphere_vent_button = 0
	  
	  let emergency_ventilate1 = 1
	  let emergency_ventilate2 = 1
	  let emergency_ventilate3 = 1
	  
	  let emergency_ventilate_in_use = 0
	  
	  // variables above for reactor controls
	  
	  let core_temp = 9420
	  let core_temp_fluctuation = 0
	  let core_temp_random = 0
	  let core_pressure = 5000
	  let core_net_output = 0
	  
      let generated_energy = 0
	  let quota = 512
	  let quota_progress = 0
	  
	  // variables above for reactor values
	  
	  function increaseCBL1power() {
	  CBL1_power=CBL1_power+1;
	  if (CBL1_power>5) { CBL1_power = 5 }
	  }
	  function decreaseCBL1power() {
	  CBL1_power=CBL1_power-1;
	  if (CBL1_power<1) { CBL1_power = 1 }
	  }
	  // functions above are for controlling CBL 1 power
	  function increaseCBL2power() {
	  CBL2_power=CBL2_power+1;
	  if (CBL2_power>5) { CBL2_power = 5 }
	  }
	  function decreaseCBL2power() {
	  CBL2_power=CBL2_power-1;
	  if (CBL2_power<1) { CBL2_power = 1 }
	  }
	  // functions above are for controlling CBL 2 power
	  function increaseCBL3power() {
	  CBL3_power=CBL3_power+1;
	  if (CBL3_power>5) { CBL3_power = 5 }
	  }
	  function decreaseCBL3power() {
	  CBL3_power=CBL3_power-1;
	  if (CBL3_power<1) { CBL3_power = 1 }
	  }
	  // functions above are for controlling CBL 3 power
	  function CBL1pressurepurge() {
	  CBL1_pressurePurge = 1
	  }
	  function CBL2pressurepurge() {
	  CBL2_pressurePurge = 1
	  }
	  function CBL3pressurepurge() {
	  CBL3_pressurePurge = 1
	  }
	  //functions above are for controlling CBL pressure purges
	  function togglefan1() {
	  if (fan1_power == 0) {fan1_power = 1}
	  else {fan1_power = 0}
	  }
	  function togglefan2() {
	  if (fan2_power == 0) {fan2_power = 1}
	  else {fan2_power = 0}
	  }
	  function togglefan3() {
	  if (fan3_power == 0) {fan3_power = 1}
	  else {fan3_power = 0}
	  }
	  function togglefan4() {
	  if (fan4_power == 0) {fan4_power = 1}
	  else {fan4_power = 0}
	  }
	  function togglefan5() {
	  if (fan5_power == 0) {fan5_power = 1}
	  else {fan5_power = 0}
	  }
	  function togglefan6() {
	  if (fan6_power == 0) {fan6_power = 1}
	  else {fan6_power = 0}
	  }
	  // functions above are for toggling all 6 fans
	  function increasePEAextractionrate() {
	  PEA_extraction_rate=PEA_extraction_rate+1;
	  if (PEA_extraction_rate>4) { PEA_extraction_rate = 4 }
	  }
	  function decreasePEAextractionrate() {
	  PEA_extraction_rate=PEA_extraction_rate-1;
	  if (PEA_extraction_rate<1) { PEA_extraction_rate = 1 }
	  }
	  // functions above are for controlling PEA extraction rate
	  function increasecoolantpump1power() {
	  coolant_pump1_power=coolant_pump1_power+1;
	  if (coolant_pump1_power>3) { coolant_pump1_power = 3 }
	  }
	  function decreasecoolantpump1power() {
	  coolant_pump1_power=coolant_pump1_power-1;
	  if (coolant_pump1_power<0) { coolant_pump1_power = 0 }
	  }
	  // functions above are for controlling coolant pump 1
	  function increasecoolantpump2power() {
	  coolant_pump2_power=coolant_pump2_power+1;
	  if (coolant_pump2_power>3) { coolant_pump2_power = 3 }
	  }
	  function decreasecoolantpump2power() {
	  coolant_pump2_power=coolant_pump2_power-1;
	  if (coolant_pump2_power<0) { coolant_pump2_power = 0 }
	  }
	  // functions above are for controlling coolant pump 2
	  function increasecoolantpump3power() {
	  coolant_pump3_power=coolant_pump3_power+1;
	  if (coolant_pump3_power>3) { coolant_pump3_power = 3 }
	  }
	  function decreasecoolantpump3power() {
	  coolant_pump3_power=coolant_pump3_power-1;
	  if (coolant_pump3_power<0) { coolant_pump3_power = 0 }
	  }
	  // functions above are for controlling coolant pump 3
	  
	  function subspacetick()  {
	  setTimeout(subspacetick, 2500);
	  
	  // part above displays core status
	  
	  if (core_pressure < 2250) { CBL1_power = 1 }
	  if (core_pressure < 2250) { CBL2_power = 1 }
	  if (core_pressure < 2250) { CBL3_power = 1 }
	  
	  core_temp_random = Math.floor(Math.random()*100) - 50
	  core_temp = core_temp + (CBL1_power + CBL2_power  + CBL1_power)*65 - (coolant_pump1_power + coolant_pump2_power + coolant_pump3_power)*120 + core_temp_random;
	  core_temp_fluctuation = (CBL1_power + CBL2_power  + CBL1_power)*65 - (coolant_pump1_power + coolant_pump2_power + coolant_pump3_power)*120 + core_temp_random;
	  core_pressure = core_pressure + Math.floor(core_temp/50) - (fan1_power + fan2_power + fan3_power + fan4_power + fan5_power + fan6_power)*70;
	  
	  power_generation = core_net_output*PEA_extraction_rate*0.25
	  quota_progress = quota_progress + power_generation/24
	  
	  PEA_stress = PEA_stress + PEA_extraction_rate*4 + Math.floor(power_generation/500) - Math.floor((coolant_pump1_power + coolant_pump2_power + coolant_pump3_power)*1.5) - 6
	  
	  
	  if (core_temp < 6000) { core_net_output = Math.floor(core_temp/250) + 50 }
	  
	  if (core_temp >= 6000) { core_net_output = Math.floor(core_temp/160) + 100 }
	  
	  if (core_temp > 17500) { core_net_output = Math.floor(core_temp/120) + 250 }
	  if (core_temp > 17500) { core_pressure = core_pressure + 200 }
	  
	  if (core_temp > 29500) { core_net_output = Math.floor(core_temp/45) + 400 }
	  if (core_temp > 29500) { core_temp = core_temp + 700 }
	  if (core_temp > 29500) { core_temp_fluctuation = core_temp_fluctuation + 700 }
	  if (core_temp > 29500) { core_pressure = core_pressure + 300 }
	  
	  if (core_pressure < 2250) { core_temp = core_temp - 750 }
	  if (core_pressure < 2250) { core_temp_fluctuation = core_temp_fluctuation - 750 }
	  if (core_pressure > 13500) { core_temp = core_temp + Math.floor(core_pressure/100) }
	  if (core_pressure > 13500) { core_temp_fluctuation = core_temp_fluctuation + Math.floor(core_pressure/100) }
	  
	  if (core_pressure > 13500) { PEA_stress = PEA_stress +2 }
	  
	  if (core_pressure < 2250) { CBL1_pressure = CBL1_pressure - 20 }
	  if (core_pressure < 2250) { CBL2_pressure = CBL2_pressure - 20 }
	  if (core_pressure < 2250) { CBL3_pressure = CBL3_pressure - 20 }
	  if (core_pressure < 2250) { CBL1_stress = CBL1_stress - 3 }
	  if (core_pressure < 2250) { CBL2_stress = CBL2_stress - 3 }
	  if (core_pressure < 2250) { CBL3_stress = CBL3_stress - 3 }
	  
	  
	  //part above is for interactions between variables
	  
	  if (CBL1_pressure < 0) {CBL1_pressure = 0}
	  if (CBL2_pressure < 0) {CBL2_pressure = 0}
	  if (CBL3_pressure < 0) {CBL3_pressure = 0}
	  if (CBL1_pressure > 100) {CBL1_pressure = 100}
	  if (CBL2_pressure > 100) {CBL1_pressure = 100}
	  if (CBL3_pressure > 100) {CBL1_pressure = 100}
	  if (CBL1_stress < 0) {CBL1_stress = 0}
	  if (CBL2_stress < 0) {CBL2_stress = 0}
	  if (CBL3_stress < 0) {CBL3_stress = 0}
	  
	  if (PEA_stress < 0) {PEA_stress = 0}
	  if (PEA_stress > 100) {PEA_stress = 100}
	  
	  if (quota_progress > quota) {quota_progress = quota}

	  // part above is for preventing values from reaching unintended levels
	  document.getElementById("CBL1power").innerHTML = "CBL 1 power: [" + CBL1_power*25 + "%]";
	  document.getElementById("CBL2power").innerHTML = "CBL 2 power: [" + CBL2_power*25 + "%]";
	  document.getElementById("CBL3power").innerHTML = "CBL 3 power: [" + CBL3_power*25 + "%]";
	  
	  document.getElementById("CBL1pressure").innerHTML = "CBL 1 pressure: [" + CBL1_pressure + "]";
	  document.getElementById("CBL2pressure").innerHTML = "CBL 2 pressure: [" + CBL2_pressure + "]";
	  document.getElementById("CBL3pressure").innerHTML = "CBL 3 pressure: [" + CBL3_pressure + "]";
	  
	  document.getElementById("CBL1stress").innerHTML = "CBL 1 stress: [" + CBL1_stress + "%]";
	  document.getElementById("CBL2stress").innerHTML = "CBL 2 stress: [" + CBL2_stress + "%]";
	  document.getElementById("CBL3stress").innerHTML = "CBL 3 stress: [" + CBL3_stress + "%]";
	  
	  document.getElementById("fan1state").innerHTML = "fan 1 state: [" + fan1_power + "]";
	  document.getElementById("fan2state").innerHTML = "fan 2 state: [" + fan2_power + "]";
	  document.getElementById("fan3state").innerHTML = "fan 3 state: [" + fan3_power + "]";
	  document.getElementById("fan4state").innerHTML = "fan 4 state: [" + fan4_power + "]";
	  document.getElementById("fan5state").innerHTML = "fan 5 state: [" + fan5_power + "]";
	  document.getElementById("fan6state").innerHTML = "fan 6 state: [" + fan6_power + "]";
	  
	  document.getElementById("coolantpump1power").innerHTML = "coolant pump 1 power: [" + coolant_pump1_power + "]";
	  document.getElementById("coolantpump2power").innerHTML = "coolant pump 2 power: [" + coolant_pump2_power + "]";
	  document.getElementById("coolantpump3power").innerHTML = "coolant pump 3 power: [" + coolant_pump3_power + "]";
	  
	  document.getElementById("coolantpump1stability").innerHTML = "coolant pump 1 stability: [" + coolant_pump1_Stability + "]";
	  document.getElementById("coolantpump2stability").innerHTML = "coolant pump 2 stability: [" + coolant_pump2_Stability + "]";
	  document.getElementById("coolantpump3stability").innerHTML = "coolant pump 3 stability: [" + coolant_pump3_Stability + "]";
	  
	  // part above is for displaying control values
	  
	  document.getElementById("coretemp").innerHTML = "core temperature " + core_temp + "°F";
	  document.getElementById("coretempfluctuation").innerHTML = "core temperature fluctuation " + core_temp_fluctuation + "°F";
	  document.getElementById("corenetoutput").innerHTML = "core net output " + core_net_output + " GW";
	  document.getElementById("PEAextractionrate").innerHTML = "PEA extraction rate " + PEA_extraction_rate*25 + " %";
	  document.getElementById("PEAstress").innerHTML = "PEA stress " + Math.floor(PEA_stress) + " %";
	  document.getElementById("corepressure").innerHTML = "core pressure " + core_pressure + " PSI";
	  
	  // part above is for displaying core values
	  
	  document.getElementById("quotaprogress").innerHTML = "Quota completion: " + Math.floor(quota_progress/quota*100) + "%";
	  
	  // part above is for displaying quota progression
	  
	  if (core_temp < 6000) { document.getElementById("corestatus").innerHTML = "State 0" }
	  if (core_temp >= 6000) { document.getElementById("corestatus").innerHTML = "State 1" }
	  if (core_temp > 17500) { document.getElementById("corestatus").innerHTML = "State 2" }
	  if (core_temp > 29500) { document.getElementById("corestatus").innerHTML = "State 3" }
	  
	  if (core_temp < 2000) { document.getElementById("corestatus").innerHTML = "Reactor stall" }
	  if (core_temp > 39000) { document.getElementById("corestatus").innerHTML = "Reactor meltdown" }
	  if (core_temp < 2000) { return; }
	  if (core_temp > 39000) { return; }
	  }
	  //part above is for displaying core status
	  // function above is for interactions between values and displaying them
    </script>
  </head>
    <b>
    <button onclick="subspacetick()">start the subspace reactor</button>
	<br>
	<br>
	<button onclick="activatemergencyventilate1()">activate emergency ventilate 1</button>
	<br>
	<button onclick="activatemergencyventilate2()">activate emergency ventilate 2</button>
	<br>
	<button onclick="activatemergencyventilate3()">activate emergency ventilate 3</button>
	<br>
	<br>
	<button onclick="activateAVB()">activate atmosphere vent</button>
	<br>
	<br>
	<button onclick="increaseCBL1power()">increase CBL 1 power</button> <button onclick="increaseCBL2power()">increase CBL 2 power</button> <button onclick="increaseCBL3power()">increase CBL 3 power</button>
	<br>
	<button onclick="decreaseCBL1power()">decrease CBL 1 power</button> <button onclick="decreaseCBL2power()">decrease CBL 2 power</button> <button onclick="decreaseCBL3power()()">decrease CBL 3 power</button>
	<br>
	<button onclick="CBL1pressurepurge()">CBL 1 pressure purge</button> <button onclick="CBL2pressurepurge()">CBL 2 pressure purge</button> <button onclick="CBL3pressurepurge()">CBL 3 pressure purge</button>
	<br>
	<p1 id="CBL1power" ></p1> <p1 id="CBL1pressure" ></p1> <p1 id="CBL1stress" ></p1>
	<br>
	<p1 id="CBL2power" ></p1> <p1 id="CBL2pressure" ></p1> <p1 id="CBL2stress" ></p1>
	<br>
	<p1 id="CBL3power" ></p1> <p1 id="CBL3pressure" ></p1> <p1 id="CBL3stress" ></p1>
	<br>
	<br>
	<button onclick="togglefan1()">toggle fan 1</button> <button onclick="togglefan2()">toggle fan 2</button> <button onclick="togglefan3()">toggle fan 3</button> <p1 id="fan1state" ></p1> <p1 id="fan2state" ></p1> <p1 id="fan3state" ></p1>
	<br>
	<button onclick="togglefan4()">toggle fan 4</button> <button onclick="togglefan5()">toggle fan 5</button> <button onclick="togglefan6()">toggle fan 6</button> <p1 id="fan4state" ></p1> <p1 id="fan5state" ></p1> <p1 id="fan6state" ></p1>
	<br>
	<br>
	<button onclick="increasePEAextractionrate()">increase PEA extraction rate</button> <button onclick="decreasePEAextractionrate()">decrease PEA extraction rate</button>
	<br>
	<br>
	<button onclick="increasecoolantpump1power()">increase coolant pump 1 power</button> <button onclick="decreasecoolantpump1power()">decrease coolant pump 1 power</button>
	<br>
	<button onclick="increasecoolantpump2power()">increase coolant pump 2 power</button> <button onclick="decreasecoolantpump2power()">decrease coolant pump 2 power</button>
	<br>
	<button onclick="increasecoolantpump3power()">increase coolant pump 3 power</button> <button onclick="decreasecoolantpump3power()">decrease coolant pump 3 power</button>
	<br>
	<p1 id="coolantpump1power" ></p1> <p1 id="coolantpump1stability" ></p1>
	<br>
	<p1 id="coolantpump2power" ></p1> <p1 id="coolantpump2stability" ></p1>
	<br>
	<p1 id="coolantpump3power" ></p1> <p1 id="coolantpump3stability" ></p1>
	<br>
	<br>
	<h1 id="quotaprogress" ></h1>
	<h1 id="corestatus" ></h1>
	<p1 id="coretemp" ></p1>
	<br>
	<p1 id="coretempfluctuation" ></p1>
	<br>
	<p1 id="corenetoutput" ></p1>
	<br>
	<p1 id="PEAextractionrate" ></p1>
	<br>
	<p1 id="PEAstress" ></p1>
	<br>
	<p1 id="corepressure" ></p1>
	</b>
	<br>
    
  </body>
</html>
==]]

return Content
