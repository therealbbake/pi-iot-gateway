Powering and controlling a FOTEK SSR-40 DA (3–32V DC input, 24–380V AC output) with a Raspberry Pi is a common, reliable way to switch high-voltage AC loads (up to 40A) using 3.3V logic. Because the SSR-40 DA has an opto-isolated input, it can typically be driven directly by the Raspberry Pi's GPIO pins, though using a 5V pin for power is more robust. [1, 2, 3, 4, 5]  
Components Needed 

• Raspberry Pi (any model) 
• FOTEK SSR-40 DA Solid State Relay 
• Jumper Wires 
• AC Load (e.g., light bulb, heater) 
• AC Power Source 

Wiring Guide 
The SSR-40 DA has four terminals: 3 & 4 (Input DC), 1 & 2 (Output AC). 

1. DC Input Side (Control - Low Voltage): 

	• SSR Terminal 3 (+): Connect to a 5V pin on the Raspberry Pi (Pin 2 or 4). 
	• SSR Terminal 4 (-): Connect to a GPIO pin (e.g., GPIO 21 / Pin 40). 
	• Note: While 3.3V GPIO can often trigger the input, using 5V for the VCC side ensures enough current (~13mA) to activate the optoisolator. 

2. AC Output Side (Load - High Voltage): 

	• Terminal 1: Connect to the AC Load (Live). 
	• Terminal 2: Connect to the AC Power Supply (Live). 
	• Neutral from the power supply goes directly to the load. 
	• ⚠️ WARNING: High voltage AC is dangerous. Ensure all power is off while wiring. [1, 9, 10, 11, 12]  

Controlling with Python 
The following Python script turns the relay on and off: 
Key Considerations 

• Safety: Always insulate AC connections. 
• Mounting: The SSR-40 DA can get hot at high loads; use a heatsink if switching over 10-15 amps. 
• Voltage Drop: If the GPIO signal is not enough to turn the relay off, ensure you are using a 5V source for the trigger, as the 3.3V from the Pi might be too low. 
• Counterfeit Modules: Be aware that many Fotek relays on the market are counterfeit and may not meet the 40A rating. [3, 13, 14, 15, 16]  

AI can make mistakes, so double-check responses

[1] https://www.facebook.com/groups/212139715483282/posts/7572734776090369/
[2] https://ielectrony.com/en/product/%D8%B3%D9%88%D9%84%D9%8A%D8%AF-%D8%B3%D8%AA%D8%A7%D8%AA-%D8%B1%D9%8A%D9%84%D8%A7%D9%8A-%D9%87%D8%A7%D9%8A-%D8%A8%D8%A7%D9%88%D8%B1-40da/
[3] https://forums.raspberrypi.com/viewtopic.php?t=252008
[4] https://www.facebook.com/groups/knoxhomebrewer/posts/765584673454701/
[5] https://forum.arduino.cc/t/can-i-power-10-ssr-relay-with-a-single-esp32/1032647
[6] https://www.facebook.com/groups/1146919932050339/posts/25335514772764184/
[7] https://bc-robotics.com/shop/solid-state-relay-40a/
[8] https://www.omch.com/solid-state-relay-diagram/
[9] https://www.youtube.com/watch?v=gNg93sfoqtA
[10] https://forums.raspberrypi.com/viewtopic.php?t=191872
[11] https://www.reddit.com/r/raspberry_pi/comments/1kod2v/tutorial_on_using_relays_and_relay_boards_with/
[12] https://www.melopero.com/wp-content/uploads/2021/10/RB-StromPi3-Manual-13-10-20.pdf
[13] https://www.youtube.com/watch?v=cn5oD02fnok
[14] https://www.youtube.com/watch?v=DZrOOhRCtZM
[15] https://www.quora.com/How-do-you-connect-an-SSR-module-to-Raspberry-Pi-or-Arduino-HCMODU0115-Arduino-Raspberry-Pi-solid-state-relay-electronics
[16] https://www.ubuy.ls/en/product/4JPRWYNTG-3pcs-solid-state-relay-ssr-40da-single-phase-solid-state-relay-module-input-3-32v-dc-output-24-380v-ac-for-temperature-controller

