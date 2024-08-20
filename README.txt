READ ME
---------------------------------------------------------------------------------------------------
Software required to run the project:
- Any software tool that supports Python3: Visual Studio Code VSCode & Python Extensions, Spyder, etc...
- Linux Ubuntu version 23.10
- Virtual Machine to run Linux: VMware, VirtualBox
- Netem package on Linux OS
---------------------------------------------------------------------------------------------------
Overview of the codes:
The project consists of two main components:
1- Peer to Peer chat connection: 2 python files to run -> Peer1 & Peer2
2- Graphical User Interface GUI: 3 python files to run -> GUI1.py & GUI2.py & clock.py + additional files: msg.png & file.png

Note: there exists two additional files in the submission folder: Peer1_CloseConnection.py & Peer2_CloseConnection.py; 
These python codes implement a special feature that closes the connection between the peers after a specified idle time (30 seconds for testing purposes)
These codes guarantee correct functionality in VSCode. They were not tested using netem emulator.

					
Required Libraries:
- tkinter
- PIL
- datetime
- time
- threading
- socket
- queue
- base64
---------------------------------------------------------------------------------------------------
How to run the codes:

A) Peer-to-Peer chat connection:
 
A.1) message and files exchange in VSCode:
1- Open both Peer1.py & Peer2.py files in VSCode
2- Run each code in their dedicated terminal
3- follow the on-screen instructions in the terminal and start sending messages or files
NOTE: when choosing which file to send, it must be already present inside the same folder as the python files!

A.2) Netem emulation in Linux Ubuntu:
1- Open two terminal windows
2- Choose what reliability test you want to emulate by entering one of the following commands in the terminal:
	- Delay: sudo tc qdisc add dev lo root netem delay 6000ms
	- Packet loss: sudo tc qdisc add dev lo root netem loss 50%
	- Duplication: sudo tc qdisc add dev lo root netem duplicate 50%
	- Reordering: sudo tc qdisc add dev lo root netem delay 100ms reorder 25% 50%
3- to revert back to normal conditions, use the following command in the terminal:
	- sudo tc qdisc del dev lo root netem
4- Enter in each code the following command, respectively in each: python3 Peer1.py, python3 Peer2.py

A.3) message and files exchange with closing connection feature in VSCode:
1- Open both Peer1_CloseConnection.py & Peer2_CloseConnection.py files in VSCode
2- Run each code in their dedicated terminal
3- follow the on-screen instructions in the terminal and start sending messages or files
NOTE: when choosing which file to send, it must be already present inside the same folder as the python files!


B) GUI:
1-Open all GUI files on VSCode (make sure they are in the same directory, otherwise the code will not run properly)
2-Now you should have GUI.py, GUI2.py, clock.py, file.png, msg.png open on your VSCode
3-Click on GUI.py and run it, do the same for GUI2.py and clock.py simultanuously (if it promts you to launch a new instance, please proceed to do so)
4-You should now have 3 floating docks: That of the first client, the second client, and a running clock
5-Have fun chatting! 