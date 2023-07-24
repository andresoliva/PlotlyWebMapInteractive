#note: This script must run using dash version  
#The following script was made in order to plot recieved data from a Data Collector Station (DCS)
#this data is recieved as a 'pandas-compatible' array
#
#---------------------------------------------------------------------------
#This script was created as part of my engenieering master degree thesis at Instituto Balseiro, Argentina
#Author:  Andres Oliva Trevisan
#Date:    2023/06/05 (June)
#version: 1.1 (beta)
#contact: olivaandres93@gmail.com
#Linkedin:https://www.linkedin.com/in/andres-oliva-trevisan-833561165/
#researchgroup Repository
#Thanks:  Dr. Karina Laneri
#         Eng. Nícolas Catalano   
#         Laila D. Kazimierski
#         Erika Kubisch
#
#tested library versions: 
    #dash:   2.10.2
    #plotly: 5.14.1    
    
#----------------------------------------------------------------------
##----------------------------libraries------------------
##comands to intall all
#pip install pyserial pandas plotly dash
#conda install -c conda-forge pyserial pandas plotly dash

import sys     #for getting file name
import os      #for getting path
import glob #for parsing text

import serial #pip install pyserial %conda install pyserial
#uncomment in order to implement threads. This is not necesary in this programa
#import threading           
#import time                #to implement delays
#to plot
#import plotly.graph_objects as go #not used at the moment
import plotly.express as px
#pandas to handle structs
import pandas as pd
import datetime            #to get time
#pandas date time format usefull information
#https://dataindependent.com/pandas/pandas-to-datetime-string-to-date-pd-to_datetime/
#https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html
#to use webbroser
import webbrowser #for opening a webbroser when running scrips
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
#from varname import nameof #for getting name of var #pip3 install varname
#---------------------------------------------------------------------
#---------------------------------------------------------------------
#--------------------DEFINE VALUES FOR CONFIGURATION------------------
#---------------------------------------------------------------------
serial_ignore_on=False #allows to ignore the serial port to run the api
#---------------------------------------------------------------------
#---------------------------------------------------------------------
#--------------------define constants
#----------------------------------------------------------------------
def constant(f):
    def fset(self, value):raise TypeError
    def fget(self):return f()
    return property(fget, fset)
class _Const(object):
  @constant
  def WEB_TITLE():               return 'Tortoise Data Collector Station (DCS)'  ##in float: 1.000102902456799e-37 in hex: 0x02082080
  @constant
  def WEB_BROWSER_URL_NAME():    return '127.0.0.1'          #-->-->-->------------default by dash:'127.0.0.1'   #-->-->-->-->        '127.0.0.1'
  @constant
  def WEB_BROWSER_URL_PORT():    return '8050'               #-->-->-->------------default by dash: '8050'       #-->-->-->-->                  '8050'
  @constant 
  def WEB_BROWSER_URL():         return ('http://'+CONST.WEB_BROWSER_URL_NAME+':'+CONST.WEB_BROWSER_URL_PORT+'/')#with default:'http://127.0.0.1:8050/'  
  @constant
  def DCS_DEBUG_FILE_NAME():     return 'maps_example_tortoises'
  @constant
  #WARNING DCS_COLUMNS_NAME IS FIRMWARE DEPENDANT, SO DO NOT CHANGE UNLESS YOU ARE GOING TO MODIFY THE COLLECTOR DEVICE (DCS) firmware!!!
  def DCS_COLUMNS_NAME():        return ['dateTime_gps_UTC','Time_reception_UTC','ID_num','bat_percent','animal_activity','activity_time','temp_MCU','temp_IMU','lat','lon','hdop','ID','Device_type','RSSI']
  @constant
  def DCS_COLUMN_PLOTTRACE_NAME():return 'ID_num'   #Value of data used to set names of the plotted points
  @constant
  def DCS_COLUMN_PLOTTRACE_SIZE():return 'hdop'     #IF DCS_COLUMN_PLOTTRACE_SIZE is not inside pandas struct, use size 
  @constant
  def DCS_COLUMN_PLOTTRACE_SIZE_DEFAULT():return 1.0   #IF DCS_COLUMN_PLOTTRACE_SIZE is not inside pandas struct, use this as size
  @constant
  def DCS_LOG_NAME():            return 'DCS_python_log' #part of the 
  @constant
  def DCS_NAME():                return 'DCS'
  @constant
  def DCS_NUMBER():              return 255        #ID_num number used to identify the DCS data
  @constant
  def DATA_RX_SIZE():            return 3000       #max amount of max bytes to be recived by serial port before timeout
  @constant 
  def RXDATA_START():            return bytearray(b'RxbyDCS:') #declared as a bytearray for an easy parsing
  @constant
  def RXDATA_END():              return bytearray(b'RxEND')    #declared as a bytearray for an easy parsing 
  @constant
  def SERIAL_UPDATE_MS():        return 2000     #time in ms used for recieving data using the serial port and then update the plot   
#create the constant class
CONST = _Const()

#---------------------------------------------------------------------
#--------------------define GLOBAL VATIABLES
#----------------------------------------------------------------------
global serial_port;
global DCS_log_name;global pd_devices;global file_name_to_load_test_data;
global serial_rx_counter;   serial_rx_counter=0;                 #initialize
global Rx_data_buffer;  Rx_data_buffer=bytearray(b'\n'); #initialize
#---------------------------------------------------------------------
##functions for serial port simulation or "test mode"
#---------------------------------------------------------------------
def serial_data_simulator_generator():
    global file_name_to_load_test_data
    file_exists = os.path.exists(file_name_to_load_test_data)
    if not(file_exists):
        test_data='''date_time_gps_UTC,reception_time,ID_num,bat_percent,animal_activity,activity_time,temp_MCU,temp_IMU,lat,lon,hdop,ID,device_type,RSSI
2023-06-01 00:00:00,00:00:00,255,19,still,2,25,23.4,-40.58325,-64.99817,5,00:12:00:00:00:00:00:00,MD_TORTOISE,110
2023-06-01 00:00:00,00:01:00,1,19,still,51,25,23.4,-40.5815,-64.9917,1.51,00:12:4B:00:1C:AA:42:4E,MD_TORTOISE,110
2023-06-01 00:00:00,00:02:00,2,29,still,2,25,23.4,-40.5845,-64.9967,1.51,00:12:4B:00:1C:AA:42:E4,MD_TORTOISE,110
2023-06-01 00:00:00,00:03:00,3,39,still,3,25,23.4,-40.5885,-64.9957,1.51,00:12:4B:00:1C:AA:44:CB,MD_TORTOISE,110
2023-06-01 00:00:00,00:04:00,4,49,moving,3,25,23.4,-40.5825,-64.9987,1.51,00:12:4B:00:1C:AA:4B:65,MD_TORTOISE,110
2023-06-01 00:00:00,00:05:00,5,59,still,3,25,23.4,-40.5855,-64.9997,1.51,00:12:4B:00:1C:AA:4B:2F,MD_TORTOISE,110
2023-06-01 00:00:00,00:06:00,6,69,moving,3,25,23.4,-40.5875,-64.9947,1.51,00:12:4B:00:1C:AA:46:53,MD_TORTOISE,110
2023-06-01 00:00:00,00:07:00,7,91,still,3,25,23.4,-40.5835,-64.9927,1.51,00:12:4B:00:1C:AA:44:7D,MD_TORTOISE,110'''
        file = open(file_name_to_load_test_data, "w")
        file.write(test_data)
        file.close()
    #checks if the files are in the OS, other wise, create them!
    file_exists = os.path.exists(file_name_to_load_test_data_toadd)
    #this is how the sata dended by the serial port from the DCS could look
    if not(file_exists):
        test_data='''                      moving,3,25,23.4,-40.5855,-64.9927,1.51,00:12:4B:00:1C:AA:44:7D,MD_TORTOISE,110RxEND
RxbyDCS:2023-06-01 00:00:40,02:00:00,3,39,still,8,25,23.4,-40.5835,-64.9957,1.51,00:12:4B:00:1C:AA:44:CB,MD_TORTOISE,110RxEND
RxbyDCS:2023-06-01 00:00:50,03:00:00,4,49,still,7,25,23.4,-40.5825,-64.9987,1.51,00:12:4B:00:1C:AA:4B:65,MD_TORTOISE,110RxEND
RxbyDCS:2023-06-01 00:00:60,04:00:00,5,59,still,3,25,23.4,-40.5845,-64.9997,1.51,00:12:4B:00:1C:AA:4B:2F,MD_TORTOISE,110RxEND
RxbyDCS:2023-06-01 00:00:70,05:00:00,6,69,moving,5,25,23.4,-40.5845,-64.9947,1.51,00:12:4B:00:1C:AA:46:53,MD_TORTOISE,110RxEND
RxbyDCS:2023-06-01 00:00:80,06:00:00,9,79,still,4,25,23.4,-40.5895,-64.9937,1.51,00:12:4B:00:1C:AA:98:99,MD_TORTOISE,110RxEND
RxbyDCS:2023-06-01 00:00:00,00:07:00,2,89,
'''
        file = open(file_name_to_load_test_data_toadd, "w")
        file.write(test_data)
        file.close()
#---------------------------------------------------------------------
##function to get current serial port list
#---------------------------------------------------------------------
def serial_ports():# Lists serial port names]
    if sys.platform.startswith('win'):ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'): ports = glob.glob('/dev/tty.*') #raspibian
    else:raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):pass
    result.append('Simulate Serial Port')
    return result #A list of the serial ports available on the system
serial_port_list=serial_ports()
print("Serial port List:",serial_port_list)
#---------------------------------------------------------------------
##functions to manipulate serial information as recieved from the 
#####
#---------------------------------------------------------------------
#convert bytes arrays to string as if was readed from a .csv file
def byte_array_list_to_csv_read(byte_array_tuple):
    if (len(byte_array_tuple))>0:
      string_ret=byte_array_tuple[0].decode('ascii')
      if (len(byte_array_tuple)>1):
         for byte_array in byte_array_tuple[1:]:
            byte_string=byte_array.decode('ascii')
            byte_string= byte_string.replace(' ','') #Remove white space to avoid issues at pandas parsing
            string_ret=string_ret+'\n'+byte_string
    else: string_ret=''
    return(string_ret)
#parser to obtain desired bytes strings
def bytearray_remove_elements_start_end(byte_array):
    byte_array_ret=byte_array.replace(b'\n',b'')#Remove breakline
    byte_array_ret=byte_array_ret.replace(b'\r',b'')#Remove return
    byte_array_ret=byte_array_ret.replace(b' ',b'')#Remove white space to avoid issues at pandas parsing
    return(byte_array_ret)
def rxdata_to_string(byte_array_raw,start_word,end_word):
    #before starting parce,remove the breaklines and other undesired elements at the end of the string to ensure a proper parsing
    byte_array=bytearray_remove_elements_start_end(byte_array_raw)#ensures a proper parsing
    #proceed to parce
    len_start=len(start_word)
    len_array=len(byte_array)
    i_min_new=0;i=0; i_max=len_array;
    ret_struct=[]
    notfound=True
    while (i_min_new>-1):
      i_min=byte_array[i:i_max].find(start_word)
      i_end=byte_array[i+len_start:i_max].find(end_word)
      i_min_new=byte_array[i+i_min+len_start:i_max].find(start_word)
      #print(i,i_max,i+i_min,i+i_end+len_start,i+i_min_new+i_min+len_start)
      if ((i_end+len_start)>i_min): #new found value, check consistency
           if((i_min_new+i_min)>i_end):
                notfound=False;
                i_limit=i+len_start+i_end
               # print("found:",byte_array[i+len_start:i_limit])
                ret_struct.append(byte_array[i+len_start:i_limit])
                i=i+i_min+len_start+i_min_new
           else: i=i+len_start+i_end
      else:  i=i+i_min#not consistent, so jump to nex part
    #now we return the last non parsed bytes and  a tuple with the bytes arrays
    if notfound:ret_nonparsed=byte_array #return all
    else:       ret_nonparsed=byte_array[i+i_min-len_start:i_max] #return non parsed
    return(ret_nonparsed,ret_struct)
#--------------------------------------------------------------------
#converts "2023-06-0110:00:05" to 2023-06-01 10:00:05

def pd_correct_dataTime(df,column_name):
   for index, row in df.iterrows(): #parse each row
       Datetime_str=row[column_name]
       if (Datetime_str[10]!=' '):
           row[column_name]=''.join((Datetime_str[0:10],' ',Datetime_str[10:]))
           df.loc[index]= row
   return(df)   
#--------------------------------------------------------------------
#---------------------------------------------------------------------
##function to update data_frame and store log
##pass the original structure
#---------------------------------------------------------------------
def store_data_into_log_csv(df,head=False):
    df.to_csv(DCS_log_csv_name, mode='a', index=False, header=head)

def create_map_with_devices(pd_plot):
    #ensure that the critical data used to make the plot is in the proper fortmat
    pd_plot=pd_plot.astype({'lat':'float','lon':'float',CONST.DCS_COLUMN_PLOTTRACE_NAME:'str'})#to ensure a proper work
    hover_data=CONST.DCS_COLUMNS_NAME #elements to list display at mouseover
    hover_data.remove('lat');hover_data.remove('lon');
    if CONST.DCS_COLUMN_PLOTTRACE_SIZE in pd_plot.columns:
         map_size=CONST.DCS_COLUMN_PLOTTRACE_SIZE
         pd_plot=pd_plot.astype({'hdop':'float'})#to ensure a proper work
         hover_data.remove('hdop'); #remove elements to not add to the mouseover
    else:#the provided column name is not inside the struct, so use the default size
         map_size='map_size'
         pd_plot['map_size'] = CONST.DCS_COLUMN_PLOTTRACE_SIZE_DEFAULT
    fig = px.scatter_mapbox(pd_plot, lat="lat", lon="lon", hover_name=CONST.DCS_COLUMN_PLOTTRACE_NAME, 
                         hover_data=hover_data,
                         size=map_size, #this casues to crash due tto consider hdop as string
                         color=CONST.DCS_COLUMN_PLOTTRACE_NAME, 
                         color_discrete_sequence=px.colors.qualitative.Bold, #Dark24 >10 #Bold or Prism <10 colors
                         )      
    return fig   

def update_devices_list_data(pd_in,pd_add):
   for index_add, row_add in pd_add.iterrows(): #compares to check if the added element exists 
        to_update=True #flag to ensure proper behaivour
        for index, row in pd_in.iterrows():
            if (row_add[CONST.DCS_COLUMN_PLOTTRACE_NAME]==row[CONST.DCS_COLUMN_PLOTTRACE_NAME]): #elements alreay exist:, update 
                #print("updating :",row_add['CONST.DCS_COLUMN_PLOTTRACE_NAME'] )
                pd_in.loc[index]= pd_add.loc[index_add]
                to_update=False
        if to_update==True:     
                #print("adding :" ,row_add['CONST.DCS_COLUMN_PLOTTRACE_NAME'] )
                pd_in=pd.concat([pd_in, row_add.to_frame().T],ignore_index = True)#pd.append(row_add,ignore_index = True)

   to_detect_DCS = pd_in[CONST.DCS_COLUMN_PLOTTRACE_NAME] ==CONST.DCS_NUMBER
   pd_in.loc[to_detect_DCS, CONST.DCS_COLUMN_PLOTTRACE_NAME] = CONST.DCS_NAME
   pd_in["ID_num"] = pd_in[CONST.DCS_COLUMN_PLOTTRACE_NAME].astype(str)
   return pd_in                
#---------------------------------------------------------------------
#--------------------check if test files exist, otherwise, generate them modes and adjust
#----------------------------------------------------------------------
#----------------------------------------------------------------------------------
script_path, script_name = os.path.split((sys.argv[0]))
print("Script name:",script_name)
#get the files names to get the data
file_name_to_load_test_data=script_name.split('.', 1)[0]+'_'+CONST.DCS_DEBUG_FILE_NAME+'.csv'
file_name_to_load_test_data_toadd=script_name.split('.', 1)[0]+'_'+CONST.DCS_DEBUG_FILE_NAME+'_toadd'+'.txt'
#checks if the files are in the OS, other wise, create them!
file_exists = os.path.exists(file_name_to_load_test_data)
#----------------------------------------------------------------------------------
#--------------------|||||||MAIN MAIN MAIN||||||||||||||||||||||||------------------------------------------------
#------------------------------------------------------------------------------
#------->>>>>>>>>>>>>>>>>>MAIN PROGRAM<<<<<<<<<<<<<<<<<<<<<<<--------
#----------------------------------------------------------------------------------
#--------------------|||||||||||||||||||||||||||||||--------------------------------------------------------------
#----------------------------------------------------------------------------------
#get serial port lists
serial_port_list=serial_ports()
print(serial_port_list)
#figure specs
map_size_scale=2.0
gps_degree_to_meters_scale=111139#convert degrees to meters
# getting the current date and time
system_date_time_utc =  datetime.datetime.now(datetime.timezone.utc)
#setting the file name #---->note: to print UTC time without decimals:str(system_date_time_utc.time()).split('.', 1)[0]
DCS_log_csv_name=CONST.DCS_LOG_NAME+'_'+str(system_date_time_utc.date())+'.csv'
#  create pandas structure
pd_devices=pd.DataFrame(columns =CONST.DCS_COLUMNS_NAME)
#  store collumns
store_data_into_log_csv(pd_devices, head=True);
#create empty map
fig=create_map_with_devices(pd_devices);
fig.update_layout(mapbox_zoom=14,mapbox_style="open-street-map")#carto-positron #open-street-map
fig['layout']['title'] ='Awaiting for data...'
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#Proceed to create the dash web structure to plot the information
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
graph_plots=[]#list of dash graph plots we want to add. makes easier to have multiple plots
graph_plots.append(dcc.Graph(id='graph_devices_map',figure=fig,style={'width': '75vw', 'height': '75vh'}))  
row = html.H1(children=graph_plots)
#.......................................................
#we add the element with the desired tittle
#.......................................................
header   = html.H1(children=CONST.WEB_TITLE,style={'color':'#107896','font_size': '150%'})
subheader =html.H2(['\U0001F422 \U0001F422 \U0001F422'+'Grupo de Física Estadística e Interdisciplinaria (FiEstIn) '+'\U0001F422 \U0001F422 \U0001F422',
                    html.Br(),'& Laboratorio de Telecomunicaciones',html.Br(),'Instituto Balseiro, Argentina'],style={'color':'#1C4E80'})
footprint = html.H3(children="\U0001F98E Andrés Oliva Trevisan, Nicolás Catalano, Laila D. Kazimierski, Erika Kubisch, Karina Laneri \U0001F98E ",style={'color':'#0092CC','text-align': 'right'}) #0092CC                                               
#serial tittle and alements
serial_sel_title= html.H4(children="Select Serial Port to communicate with DCS hardware:",style={'color':'#ECECEC','text-align': 'left'})
serial_sel_menu= dcc.Dropdown(id="dropdown_serial_port_list",options=serial_port_list,style={'width': '220px',})
#we add the element with the timer
graph_timer= dcc.Interval(id='timer_graph_update',interval=CONST.SERIAL_UPDATE_MS # in milliseconds
                                                 ,n_intervals=0) #initial value of intervals
#create an object to chare ,json compatilble data between elements of the web site or external one
data_to_share=dcc.Store(id='data_to_transfer', storage_type='local')
#-----------------------------------------------------------------------------------
#we create the app layout adding all the objsects ---------------------------------
app_layout = html.Div(children=[header,subheader, serial_sel_title,serial_sel_menu,row,data_to_share, graph_timer,footprint], style={
"text-align": "center", "justifyContent":"center",'backgroundColor':"#F1F1F1"})
#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------
#---------------WEB UPDATE CALLBACK FUNCTION--------------------------------------
#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------
#Define dash callback function to update plot.
#-----Must be defined here because 'serial_port' var has to be initialized before define
#---------------------------------------------------------------------------------
app = dash.Dash(__name__)
app.layout=app_layout
#------callback function to serial menu
@app.callback(        
    Output('dropdown_serial_port_list','value'),
    Output('dropdown_serial_port_list', 'options'),
    Input('dropdown_serial_port_list', 'value')
)
def connect_to_serial_port(selected_serial_port):
    global serial_rx_counter; global serial_port;global pd_devices;global file_name_to_load_test_data; global serial_ignore_on;
    serial_ports_ret=serial_ports()
    if selected_serial_port=='Simulate Serial Port': serial_port = serial.serial_for_url('loop://', timeout=1);serial_ignore_on=True;
    else:                                            serial_port = serial.Serial(selected_serial_port,115200,timeout=1);serial_ignore_on=False;#timeout must be passed in seconds
    if(serial_port.isOpen()): print(serial_port.read(CONST.DATA_RX_SIZE*20))#read all it can before time out, allow us to clean the buffer
    serial_port.timeout=0; #remove timeout to avoid SYNC issues
    serial_rx_counter=-2 #=-2: do not change for make this work with the simulation
    if serial_ignore_on:
        serial_data_simulator_generator();#generate example to read
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Serial simulator on!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("Serial port opened:",serial_port)
    return(selected_serial_port,serial_ports_ret)

#---this callback is triggred by the periodic timer    
@app.callback(Output('data_to_transfer',  'data'), #must be named data, otherwise raise error
              Input('timer_graph_update', 'n_intervals')
              )
#This function recieves serial data and stract the sedired messagers
# and pass it to the function in charge of the plottling
def function_rx_serial_port(n_intervals):
          global Rx_data_buffer;
          #get all the Rx data in PC uart buffer
          if(serial_port.isOpen()):Rx_data=serial_port.read(CONST.DATA_RX_SIZE); #get Rx data in PC uart buffer         
          else:   Rx_data=[];#empty
          #print rx data
          if(len(Rx_data))>0:print("Rxdata:",Rx_data)
          #add simulated data if correspondds
          if serial_ignore_on and ((serial_rx_counter/7).is_integer()):
              f = open(file_name_to_load_test_data_toadd, "r")#load simulated data from .text
              rx_string_test=f.read()
              f.close()
              Rx_data=bytes(rx_string_test,'ascii')#convert to bytes the simulated data
          #add the data to the current buffer
          Rx_data_buffer+=(bytearray(Rx_data)) #or ((bytearray(Rx_data)).reverse()) if data is recieved inverted
          print("rx data buffer",Rx_data_buffer)
          #------------Reception ends, starts to parse----------------
          #parce the buffer to get desired information
          Rx_data_buffer, Rx_data_founded=rxdata_to_string(Rx_data_buffer,CONST.RXDATA_START,CONST.RXDATA_END)
          #convert the obtained data to string
          Rx_data_to_plot_as_str=byte_array_list_to_csv_read(Rx_data_founded)
          return(Rx_data_to_plot_as_str) 
##############################################################################     
##############################################################################     
#------callback function to read data that has been stores and then update the plot 
#-------this callback is triggred each time the 'data_to_transfer': 'data' object
         # is returned
 ##############################################################################     
 ##############################################################################              
@app.callback(Output('graph_devices_map', 'figure'),#figure MUST be an output to store the modified version
              Input('data_to_transfer', 'data'), #must be named data, otherwise raise error
              Input('graph_devices_map', 'figure') #figure MUST be an input in order to be modified
              )
#this functions recived the data from the serial port as a group of strings, 
#then append this data to the pandas structure and proceeds to plot it
def function_update_plot(Rx_data,figure):
        global pd_devices;global serial_rx_counter
        pd_devices_update=[]
        #check if there is data to plot, and then creates the structure
        #--->check reception data and add it to a pandas structure
        if len(Rx_data)>0:#this means new data frames where detected
              serial_rx_counter=serial_rx_counter+1
              pd_devices_update = pd.DataFrame([x.split(',') for x in Rx_data.split('\n')])
              pd_devices_update.columns =CONST.DCS_COLUMNS_NAME
            #print(pd_devices_update)
        #--->for debug/simulation with no real serial port
        if serial_ignore_on:
            if (serial_rx_counter==-1):
               pd_devices_update = pd.read_csv(file_name_to_load_test_data)
               pd_devices_update.columns =CONST.DCS_COLUMNS_NAME
        #update structure if there is something to        
        if (len(pd_devices_update)>0):
            if(serial_rx_counter==-1): #first time creation
                    pd_devices=pd_devices_update.copy(deep=True);
            pd_devices_update= pd_correct_dataTime(pd_devices_update,'dateTime_gps_UTC')#make corrections after parsing
            store_data_into_log_csv(pd_devices_update);
            pd_devices=update_devices_list_data(pd_devices,pd_devices_update) 
            #check if the pandas structure to plot has elements, then plot
            if(serial_rx_counter==-1):
               print("create first map")
               figure=create_map_with_devices(pd_devices)
               figure.update_layout(mapbox_zoom=14,mapbox_style="open-street-map")#carto-positron #open-street-map
            #add other figures
            else:
                fig_to_dict= (create_map_with_devices(pd_devices)).to_dict()
                figure['data']=fig_to_dict['data']
                #figure=create_map_with_devices(pd_devices) Non used
                #figure.update_layout(mapbox_zoom=14,mapbox_style="open-street-map") Non used
            #system_date_time_utc =  (pd.Timestamp(datetime.datetime(2023, 6, 1))).utcnow()
            system_date_time_utc = datetime.datetime.now(datetime.timezone.utc)
            figure['layout']['title'] ='Last Update: '+str(system_date_time_utc.date())+' '+ str(system_date_time_utc.time()).split('.', 1)[0]+ ' UTC';
        if (serial_ignore_on):serial_rx_counter=serial_rx_counter+1
        print(serial_rx_counter)
        return(figure)
#--------------------------------------------------------------
#--------------------------------------------------------------                             
#--------------------------------------------------------------
# Open web browser and start dash server
#--------------------------------------------------------------
webbrowser.open_new(CONST.WEB_BROWSER_URL)  #opens a web browser with the default site
app.run(host=CONST.WEB_BROWSER_URL_NAME,port=CONST.WEB_BROWSER_URL_PORT,debug=False)
#--------------------------------------------------------------
# End of program: this point is reach when dash server is shutted down
#--------------------------------------------------------------
try:     serial_port.close() #we try to- close the opeened serial port in order to release it for other app
finally: print('End of program: Serial port was closed')
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#####commented: not used at the momment, but could be used in the future
#------------------------------------------------------------------------
#  @constant
#  def SERIAL_PORT_ID_WIN():      return 'COM1'  ##in float: 1.000102902456799e-37 in hex: 0x02082080
# @constant
#  def SERIAL_PORT_ID_LINUX():    return '/dev/ttyACM0'  ##in float: 1.000102902456799e-37 in hex: 0x02082080
#  @constant
#  def SERIAL_PORT_ID_RASPBIAN(): return '/dev/ttyS0'#serial 0:'/dev/ttyS0',serial 1:'/dev/ttyAMA0' 
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#Proceed to open and init serial port #now this was made obsolote due to the use of a selector
#-----------------------------------------------------------------------------------
#import platform #to get my operative system
#opertative_system=platform.system()
#if opertative_system=='Raspbian': serial_port_id=CONST.SERIAL_PORT_ID_RASPBIAN
#if opertative_system=='Linux':    serial_port_id=CONST.SERIAL_PORT_ID_LINUX
#if opertative_system=='Windows':  serial_port_id=CONST.SERIAL_PORT_ID_WIN
#try :   serial_port.close() #will try to close port if already opened, this is a secutiry meassure
#except: pass #DO NOT COMMENT if we can't close, we don't do anything
#finally:
 #    if serial_ignore_on:serial_port = serial.serial_for_url('loop://', timeout=1)
#     else:               serial_port = serial.Serial(serial_port_id,115200,timeout=1)#timeout must be passed in seconds
#print('Serial port',serial_port) #to know the serial port used
#---------------------------------------------------------------------------------------
