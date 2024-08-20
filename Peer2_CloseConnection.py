# The code for peer2 is parallel to that of peer1. 
import socket
import threading
from queue import Queue 
import time 

# Initializing variables to be used as Global Variables

my_sequence_number = 0 # peer 2 sequence number
other_sequence_number = 0 # peer 1 expected sequence number
sending_ID = 1 # peer 2 message ID 
receiving_ID = 1 # peer 1 expected message ID

idle_time = 0 # track time spent idle in chat -> used to close the connection if idle for too long
stop_threading = 0 # flag that stops all threads once asserted 
messaging = 1 # flag that indicates peer 2 is sending a message (when it is asserted)
receiving = 1 # flag that indicates peer 2 is receiving a message (when it is asserted)

# Initializing Disctionaries
outgoing_packets = {} # used to store packets that have just been sent (saved locally in case retransmission is needed until corresponding ACK is received)
sent_packets = {} # used to store the timestamp of the packets that have just been sent (for ACK tracking)
reconstruction = {1:''} # used to temporarily store the received packets while building the full response message back

# Initializing queues to be used as buffers
incoming_queue = Queue() # used to store received packets from peer 1

# Timeout duration for waiting for ACK (in seconds)
ACK_timeout = 5 # 5 seconds timeout

#################################################################################################################################

# Defining functions for receiving and sending messages between peers
# Function that allows for sending messages in packets
def send_message(user_UDP_socket, client_address, user_TCP_socket):
    
    global my_sequence_number
    global sending_ID
    
    global messaging
    global idle_time
    global stop_threading
    
    max_packet_size = 1000 # initialize variable of max_packet_size of 1,000B

    while True: # infinite loop
       
       if not stop_threading: # while threading is not stopped
           
            messaging = 0 # set messaging flag to 0 until peer 1 inputs a message
            idle_time = time.time() # reset idle_time
            
            print("\n")
            message = input() # Input message
            
            messaging = 1 # set messaging flag to 1 because peer 2 is sending a message 
            
            if message == "<I WANT TO SEND A FILE>": # Handle sending files with TCP
                file_and_extension_name = input("Input the name of the file and its extension that you want to send: ")
                print("\n")
                send_TCP_file(client_address, file_and_extension_name)
            
            elif (message == "") and (stop_threading): # if peer 2 pressed enter and the threading must stop
                file_and_extension_name = ""
                send_TCP_file(client_address, file_and_extension_name) # used to call and declare that send_TCP_file shut down
            
            elif message == "": # if peer 2 pressed enter (did not write any message to be sent)
                print("Enter a valid message to send!")
                
            else: # Handle normal text messages
                
                message_packets = divide_message(message, max_packet_size) # divide the message into packets & store them in message_packets array 
                
                for packet in message_packets: # loop over all the packets inside array
                    
                    packet_with_headers = str(my_sequence_number) + ";" + str(sending_ID) + ";" + packet # Add sequence_number & ID as headers to the packet I am sending
                    packet_with_headers = packet_with_headers.encode() # encode packet_with_headers
                    user_UDP_socket.sendto(packet_with_headers,("127.0.0.1", 50000)) # send packet_with_headers to peer 1
                    
                    outgoing_packets[my_sequence_number] = packet_with_headers # insert ENCODED packet_with_headers into outgoing_packets
                    sent_packets[my_sequence_number] = time.time() # insert in dictionary the time at which the packet was sent at key=sequence_number
                    my_sequence_number += 1 # Increment sequence number
                sending_ID += 1 # increment message_ID so that the next message has a different ID
                
       else: # if threading must be stopped
           print("send_message shut down successfully.")
           print("Full application shut down successfully!")
           break
        
              
# Function to break down a message into smaller packets
def divide_message(message, max_packet_size):
    
    packets = [] # initialize to store the message's packets of max_packet_size = 1000B each
    
    for i in range(0, len(message), max_packet_size): # range = [0, len(msg)] & increments iterator by max_packet_size
        packet = message[i : i+max_packet_size] # packet = characters of the msg within range [i;i+max_packet_size]
        packets.append(packet) # append packet to packets array
     
    # Add <END> tag to the last packet to indicate last packet of the message before completion -> helps in reconstruction
    last_packet = packets[-1] + "<END>"  
    packets[-1] = last_packet  
    
    return packets

#################################################################################################################################

# Function that allows for receiving messages & puts them in incoming_queue
def receive_packet(user_UDP_socket):
    
    global stop_threading 
    
    while True: # infinite loop
        
        while not stop_threading: # while threading is not stopped
            
            try:
                user_UDP_socket.settimeout(1) # set timeout for the receive operation -> used to help when needing to stop the threading => goes to exception to pass and not get stuck on socket.recvfrom method
                response_packet, user_socket_add = user_UDP_socket.recvfrom(1024) # recvfrom returns a tuple (response= data,user_socket_add= address)
                response_packet = response_packet.decode() # decode the recieved packet+sequence_number+message_ID
                incoming_queue.put(response_packet) # insert the response_packet at tail of incoming_queue
            except socket.timeout:
                pass
        else: # if threading must be stopped
           print("receive_message shut down successfully.")  
           break   

        
# Function that processes received packets    
def process_packet(user_UDP_socket, client_address):
    
    global other_sequence_number
    global receiving_ID 
    
    global receiving
    global idle_time
    global stop_threading
    
    while True: # infinite loop
        
        if not stop_threading: # while threading is not stopped
            
            if not incoming_queue.empty(): # a response was received & saved in incoming_queue
                
                receiving = 1 # set receiving flag to 1 because I am receiving/processing packets -> peer 2 is not idle
                
                packet_with_headers = incoming_queue.get() # remove & return response(packet+seq_nbr+ID) at the head of incoming_queue
                seq_str, ID_str, packet = packet_with_headers.split(";", 2) # split the response at the first 2 instances of ";" between seq & ID & actual packet
                
                if seq_str == "ACK": # handle ACK message & note: packet is actually the ACK number
                    handle_peer_ack_message(packet)
                else: # handle regular packet
                    handle_peer_regular_packet(seq_str, ID_str, packet, user_UDP_socket, client_address)
            
                idle_time = time.time() # reset idle_time here -> logic
                
            else:
                receiving = 0 # set receiving flag to 0 because incoming_queue is empty <=> peer 2 is not receiving packets <=> peer 2 is idle
                 
        else: # if threading must be stopped
           print("process_message shut down successfully.")  
           break

# Function that handles regular packets                
def handle_peer_regular_packet(seq_str, ID_str, packet, user_UDP_socket, client_address):
    
    global other_sequence_number
    global receiving_ID
    
    seq = int(seq_str) # casting the seq nbr extracted, from string to integer type
    ID = int(ID_str) # casting ID nbr extracted, from string to integer type
    
    if seq == other_sequence_number: # if seq_nbr extracted = seq_nbr expected => it is the packet I am expecting => correct order of delivery
        
        if ID == receiving_ID: # The packet received has the expected ID

            if ID not in reconstruction: # if the packet received is the 1st packet of a new message -> create its key:value=ID:packet1 pair inside dictionary
                reconstruction[ID] = packet
            else:
                reconstruction[ID] += packet # if ID is already a key inside reconstruction dictionary, concatenate packets to form entire message => ID:packet1+packet2+...
            
            if packet[-5:] == "<END>": # there are no packets left to wait for -> this message is complete
                print("\n")
                print("Received from Person 1:" + reconstruction[ID][:-5]) # print the completed message + excluding <END> tag
                print("\n")
                del reconstruction[receiving_ID] # remove completely reconstructed message
                receiving_ID += 1  # increment receiving_ID to indicate the current message is completed and I expect a new one with a different ID


        else: # peer 1 received the seq expected (correct order of delivery) but not the ID expected (this is a new message and the one before it is complete)
            
            if receiving_ID in reconstruction: # check if previous ID was correctly deleted; if not:
                print("\n")
                print("Received from Person 1:" + reconstruction[receiving_ID][:-5]) # print previously the completed message
                print("\n") 
                del reconstruction[receiving_ID] # remove completed reconstructed message
            
            reconstruction[ID] = packet  # add next message's 1st packet to reconstruction dictionary
            receiving_ID += 1 # increment receiving_ID to indicate we're constructing a new message
            
        other_sequence_number += 1 # increment sequence number peer 1 is expecting
        create_and_send_ack_message(seq, user_UDP_socket, client_address) # call function that creates & sends ack_message back to peer 2 for this packet

    elif seq > other_sequence_number: #seq_nbr extracted > seq_nbr expected => packet delivered in Wrong Order
        pckt_with_headers = str(seq) + ";" +  str(ID) + ";" + packet # add corresponding headers back to the packet
        incoming_queue.put(pckt_with_headers) # insert the pckt_with_headers back at the tail of incoming_queue to be processed again later
        
    else: # seq < other_sequence_number => duplicated packet! I will not print it but I will send an ACK so that it is NOT retransmitted again
        create_and_send_ack_message(seq, user_UDP_socket, client_address)


# Function that creates and sends ack message back to peer 2
def create_and_send_ack_message(seq_int, user_UDP_socket, client_address):
    ack_message = "ACK;0;" + str(seq_int) # create ACK to send back to peer 2
    ack_message = ack_message.encode() # encode ACK message
    user_UDP_socket.sendto(ack_message, client_address) # send ACK message via socket   

# Function that handles ACKs        
def handle_peer_ack_message(ack_nbr_str):
    ack_nbr = int(ack_nbr_str) # casting the ack nbr extracted from string to integer type
    if ack_nbr in sent_packets:
        del sent_packets[ack_nbr] # deleting the ack's corresponding value (timestamp) from the dictionary
    if ack_nbr in outgoing_packets:
        del outgoing_packets[ack_nbr] # remove & return the ack's corresponding message out of the outgoing_messages


# Function that handles missing packets
def handle_missing_packets(user_UDP_socket, client_address):
    
    global idle_time
    global messaging
    global stop_threading
    
    while True: # infinite loop
        
        if not stop_threading: # while threading is not stopped
            
            if len(sent_packets) != 0:
                
                messaging = 1 # set messaging flag to 1 because I am awaiting an ACK or else sending back a missing packet => peer 2 is not idle!
                
                for seq, timestamp in sent_packets.items(): # iterate over the dictionary's key:value pairs 
                    
                    if time.time() - timestamp > ACK_timeout: # if the pair still exists in the dictionary for more than ACK_timeout -> retransmit the packet!
                        
                        print("Timeout! Resending...")
                        print("\n")
                        
                        message = outgoing_packets[seq] # remove & return the ENCODED packet from outgoing_queue
                        
                        user_UDP_socket.sendto(message, client_address) # retransmit the packet to peer 1
                        create_and_send_ack_message(seq, user_UDP_socket, client_address) # send a new ACK to peer 1
                        sent_packets[seq] = time.time() # reset the sent packet's timestamp
                        
                idle_time = time.time() # reset idle_time
                
            else: # if sent_packets is empty => peer 1 not expecting any ACKs because peer 1 haven't been sending messages 
                messaging = 0    
                
            time.sleep(1) # Check for missing messages periodically every 1 second to save resources
            
        else: # if threading must be stopped
           print("handle_missing_messages shut down successfully.")  
           break                        
     
                
#################################################################################################################################

# Function that starts the chat application
def start_chatting(user_UDP_socket, client_address, user_TCP_socket):
    print("Start up your conversation!")
    print("Note: To send a file, input the message '<I WANT TO SEND A FILE>' and follow the instructions!")
    print("Note: Being idle for 30 seconds will close the chat connection with your peer!")
    threading.Thread(target=send_message, args=(user_UDP_socket, client_address, user_TCP_socket)).start() # Thread for sending messages
    threading.Thread(target=receive_packet, args=(user_UDP_socket,)).start() # Thread for receiving packets
    threading.Thread(target=process_packet, args=(user_UDP_socket, client_address)).start() # Thread for processing packets
    threading.Thread(target=handle_missing_packets, args=(user_UDP_socket, client_address)).start() # Thread for checking for missing packets periodically
    threading.Thread(target=receive_TCP_file, args=(user_TCP_socket,)).start() # Thread for checking if there is a file to receive
    threading.Thread(target=check_for_connection).start() # Thread for checking peers are active or idle => to close the chat application

# Function that checks if peers are active or not to consider closing the chat application
def check_for_connection():
    global idle_time
    global stop_threading
    global messaging
    global receiving
    
    counter = 6 # used as a countdown to alert peer 2 before closing the connection
    
    while True: # infinite loop
        
        if (time.time() - idle_time >= 30) and (not receiving) and (not messaging): # idle for 30 seconds and not messaging nor receiving
            
            if counter > -1: # to avoid errors
                
                print("Your chat connection will close in " + str(counter) + " seconds") # alerting peer 2
                counter -= 1 # decrement counter till 0
                
                time.sleep(1) # let 1 second pass
                
        else:
            counter = 6 # resetting the counter
        
        if counter == 0: # peers have been idle for 30 seconds => close the connection
            stop_threading = 1 # set flag to 1 to stop threading
            print("Beginning process of closing chatting application...")
            print("YOU MUST PRESS ENTER TO FINALIZE THE CLOSING PROCESS!")
            print("check_for_connection shut down successfully.")
            break 
        


#################################################################################################################################

def send_TCP_file(client_address, file_and_extension_name):
    
    global stop_threading
    
    if not stop_threading:
        
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sending_socket.connect(client_address) # connect to peer 1 using TCP
        
        file = open(file_and_extension_name, "rb") # open file we want to send in "reading binary" mode
        
        file_name_to_client = "received_" + file_and_extension_name
        sending_socket.send(str(file_name_to_client).encode()) # peer 1 gets file name
        print("Sending...")
        data = file.read()
        sending_socket.sendall(data) # sends all file data to peer 1
        sending_socket.send(b"<END>") # sends an <END> tag in bytes to make sure the file is fully sent and sending process is over
        print("Sent!")
        file.close()
        sending_socket.close()
        
    else: # if threading must be stopped
        print("send_TCP_file shut down successfully.") 
    
    
def receive_TCP_file(user_TCP_socket):
    
    global stop_threading
    
    while True: # infinite loop
        
        while not stop_threading: # while threading is not stopped
                        
            try:
                user_TCP_socket.settimeout(1) # set timeout for the receive operation
                client_socket, client_address = user_TCP_socket.accept() # accept TCP connection
                
                file_name = client_socket.recv(1024) # file name I will receive
                file_name = file_name.decode() # decode it
                print("File to be received: " + file_name)
                print("\n")
                
                file = open(file_name, "wb") # open a file in that file_name in "write binary" mode
                
                file_bytes = b"" # variable to store the bytes of the file being received through the client_socket
                
                done = False # boolean variable used to indicate whether transfer is complete
                
                while not done:
                    data = client_socket.recv(1024)
                    if file_bytes[-5:] == b"<END>": # <END> flag is received indicating file is fully transferred
                        done = True # set boolean to true
                    else:
                        file_bytes += data # keep adding bytes of file
                
                file.write(file_bytes[:-5]) # write into the file that was opened the bytes received excluding <END> flag
                print(file_name + " successfully received!")
                print("\n")
                file.close() # close the file
                client_socket.close() # close the connection with the client
            except socket.timeout:
                pass
            
        else: # if threading must be stopped
           print("receive_TCP_file shut down successfully.")  
           break      
                    
#################################################################################################################################

# Save user/host's IP address
host_name = socket.gethostname() # Save hostname
host_ip = socket.gethostbyname(host_name) # Save host IP
# Save addresses for peer 1 & peer 2
user_1_address = (host_ip, 50000)
user_2_address = (host_ip, 50010)

# Create socket for peer 1 with UDP & bind it to its address
user_2_UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
user_2_UDP_socket.bind(user_2_address)
# Create TCP socket for peer 1 & bind it to its address
user_2_TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
user_2_TCP_socket.bind(user_2_address)

user_2_TCP_socket.listen() # listen for TCP connection
print("I am ready to receive files!")

# Start Chatting
start_chatting(user_2_UDP_socket, user_1_address, user_2_TCP_socket)

while True: # infinite loop
    if stop_threading: # threading must be stopped => close UDP sockets
        print("Closing Socket...")
        time.sleep(10)
        user_2_UDP_socket.close()
        print("Socket closed successfully.")
        break