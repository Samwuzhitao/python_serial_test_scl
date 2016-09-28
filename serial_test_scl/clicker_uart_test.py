#! /usr/bin/env python
"""\
Scan for serial ports.

Part of pySerial (http://pyserial.sf.net)
(C) 2002-2003 <cliechti@gmx.net>

The scan function of this module tries to open each port number
from 0 to 255 and it builds a list of those ports where this was
successful.
"""
# import system module
import serial
import array
import os
import time
import string
import linecache 
import threading
import ConfigParser
from time import sleep

# import user module
from uart_scan import uart_scan
import uart_status_machine
import uart_check

# global variable
uart_test_cmd_max = 0
uart_test_cmd_index = 0
uart_send_cmd_num = 0
uart_read_cmd_file_num = 0

def uart_get_cmd_message(file_name):
	global 	uart_test_cmd_max
	global uart_test_cmd_index
	global uart_read_cmd_file_num
	
	f = open(file_name,'rU')
	uart_read_cmd =linecache.getline(file_name,uart_test_cmd_index+1)
	print "uart send cmd : "+uart_read_cmd
	uart_read_cmd = linecache.getline(file_name,uart_test_cmd_index+2)
	#print "linecache.getline = "+uart_read_cmd
	
	f.close()
	uart_test_cmd_index = uart_test_cmd_index + 2 
	if uart_test_cmd_index == uart_test_cmd_max:
		uart_test_cmd_index = 0
		uart_read_cmd_file_num = uart_read_cmd_file_num + 1
	uart_read_cmd=uart_read_cmd.strip('\n')

	return uart_read_cmd

def store_test_result():
	global uart_send_cmd_num
	global uart_read_cmd_file_num
	global startTime
	global path
	
	endTime = time.time()
	
	f = open(path + '\\test_file\clicker_test_result.txt','w')
	f.write('[TEST] read cmd file count    = '+hex(uart_read_cmd_file_num)+'\r\n')
	f.write('[TEST] send cmd count         = '+hex(uart_send_cmd_num)+'\r\n')
	f.write('[TEST] ok  instructions count = '+hex(uart_check.uart_revice_cmd_ok_num)+'\r\n')
	f.write('[TEST] err instructions count = '+hex(uart_check.uart_revice_cmd_err_num)+'\r\n')
	f.write('[TEST] test time              = '+str(endTime-startTime)+'\r\n')
	f.close()

def uart_compress_cmd():
	global ser

	while True:
		read_char = ser.read(1)
		uart_status_machine.uart_decode_machine(read_char)
		if uart_status_machine.status == 100:
			uart_status_machine.uart_change_status(0)
			store_test_result()

def uart_send_cmd():
	global ser
	global uart_send_cmd_num
	global uart_test_file_name
	
	while True:
		uart_cmd_data = uart_get_cmd_message(uart_test_file_name)
		#print uart_cmd_data
		uart_cmd_data = uart_cmd_data.decode("hex")
		ser.write(uart_cmd_data)
		uart_send_cmd_num = uart_send_cmd_num + 1
		sleep(0.3)

if __name__=='__main__':
	# open uart port
	uart_scan();
	selport = input('Please select port: ')
	#selport = 5
	print "The port you select is :",selport
	
	# get uart configuration
	path = os.path.abspath("../")
	#print path
	config = ConfigParser.ConfigParser()
	config.readfp(open(path + '\\configuration\\' + 'uart_config.txt', "rb"))
	baudrate = config.get('setting', 'baudrate')
	timeout  = config.get('setting', 'timeout')
	
	# open serial port
	ser = serial.Serial( selport, string.atoi(baudrate, 10), timeout = string.atoi(timeout, 10))
	print "Open Port : ",ser.portstr
	print "Baudrate  :  "+baudrate
	print "TimeOut   :  "+timeout

	uart_send_cmd_switch = input('Open or Close cmd send function : ( 0 : [OFF] , 1 : [ON] ) ')

	if uart_send_cmd_switch == 1:
		# open read test file name
		uart_test_file_name = config.get('cmd_file_select', 'cmd_file_name')
		uart_test_file_name = path + '\\test_file\\' + uart_test_file_name
		print "uart test file name : "+uart_test_file_name
	
		# get the cmd num of the file 'clicker_test_cmd.txt'
		uart_test_cmd_max = len(open(uart_test_file_name,'rU').readlines()) 
		print "clicker_test_cmd len = ",uart_test_cmd_max/2

	startTime = time.time()

	#while True:
	#   if uart_send_cmd_switch == 1:
	#		uart_send_cmd()
	#	uart_compress_cmd()

	#reader = multiprocessing.Process(target=uart_compress_cmd)
	
	reader  = threading.Thread(target=uart_compress_cmd)
	reader.start()
	print 'Process reader is going to start...'

	if uart_send_cmd_switch == 1:
		#writer  = multiprocessing.Process(target=uart_send_cmd)
		writer  = threading.Thread(target=uart_send_cmd)
		writer .start()
		print 'Process writer is going to start...'