#Szükséges csomagok importálása

import sys, os, time, picamera, urllib.request, smtplib
import ssl, subprocess, mimetypes, email, datetime
import RPi.GPIO as GPIO
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


#E-mail beállítások

receiver_email = 'mynameisnepster@gmail.com'

sender_email = 'raspi.sec.system@gmail.com'
username = 'raspi.sec.system'
password = '*********'


#GPIO tüskék beállítása

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pir_pin = 5                
green_led_pin = 27
red_led_pin = 22

GPIO.setup(pir_pin, GPIO.IN)
GPIO.setup(green_led_pin, GPIO.OUT)
GPIO.setup(red_led_pin, GPIO.OUT)

GPIO.output(green_led_pin, GPIO.LOW)
GPIO.output(red_led_pin, GPIO.LOW)


#Internet kapcsolat ellenőrzése

def internet_access():
    internet = False
    
    print ('Internet kapcsolat ellenőrzése...')
    
    while not internet:
        try:
            urllib.request.urlopen('http://google.com')
            print('Van internet kapcsolat!')
            internet = True
        except:
            print ('Nincs internet kapcsolat!')
            time.sleep(5)
            

#LED beállítása

def led_light():
    if GPIO.input(pir_pin) == True:
        GPIO.output(green_led_pin, False)
        GPIO.output(red_led_pin, True)
        
    elif GPIO.input(pir_pin) == False:
        GPIO.output(red_led_pin, False)
        GPIO.output(green_led_pin, True)

#Inicializáció

def initialization():
    internet_access()
    
    public_ip_request = subprocess.Popen("host myip.opendns.com resolver1.opendns.com | grep 'myip.opendns.com has' | awk '{print $4}'", shell=True, stdout=subprocess.PIPE)
    public_ip = (public_ip_request.communicate()[0].decode("utf-8").split('\n')[0])
    
    private_ip_request = subprocess.Popen("ip route show default | grep -oP 'src \K\S+'", shell=True, stdout=subprocess.PIPE)
    private_ip = (private_ip_request.communicate()[0].decode("utf-8").split('\n')[0])

    interface_request = subprocess.Popen("ip route show default | grep -oP 'dev \K\S+'", shell=True, stdout=subprocess.PIPE)
    interface_type = (interface_request.communicate()[0].decode("utf-8").split('\n')[0])
    
    initializated = False
    
    while not initializated:
        try:
            message = ('Biztonsági rendszer aktiválva!\n\nPublikus IP: %s\nPrivát IP: %s\nInterfész típusa: %s\n\n' % (public_ip,private_ip,interface_type))
            msg_date = (datetime.datetime.now().strftime("%Y.%m.%d. %H:%M:%S"))
            print (message)
            print ('Inicializálós email küldése...')
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = 'Biztonsági rendszer aktiválva!'          
            msg.attach(MIMEText(message + msg_date))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.sendmail(sender_email,receiver_email, msg.as_string())
            server.quit()
            initializated = True         
            print ('Inicializálós email elküldve!')
            
        except Exception as error:
            print ('Hiba az email elküldése közben!\nHibakód:', error, '\nÚjrapróbálkozás 5mp múlva...')
            time.sleep (5)
       
    
    
#Videó felvétel beállítása

def video_capture():
    caught = False
    
    while not caught:
        try:
            with picamera.PiCamera() as camera:
                camera.resolution = (1280, 720)
                camera.framerate = 60
                camera.sharpness = 0
                camera.contrast = False
                camera.ISO = 0
                camera.saturation = 0
                camera.exposure_mode = 'auto'
                camera.exposure_compensation = 0
                camera.video_stabilization = False
                camera.crop = (0.0, 0.0, 1.0, 1.0)
                camera.hflip = True
                camera.vflip = False
                camera.brightness = 60
        
                print ('Videófelvétel készítése...')
                filename = 'record.h264'
                camera.start_recording(filename)
                camera.wait_recording(10)
                camera.stop_recording()
                caught = True
                print ('Videófelvétel elkészült!')
            
                print ('Videófelvétel konvertálása...')
                global converted
                converted = False
                if os.path.isfile('record.h264'):
                    subprocess.call(['MP4Box -add record.h264 record.mp4'], shell=True)
                
                if os.path.isfile('record.mp4'):
                    print ('Videófelvétel konvertálása elkészült!')
                    converted = True
                else:
                    print ('Hiba történt a konvertálás közben!\nEredeti felvétel elküldése...')
                                             
        except Exception as error:
            print ('Hiba történt a videófelvétel közben!\nHibakód: ', error)
        
 

#Fájlok módosítása és törlése

def files_manager():  
    if os.path.isfile('record.mp4'):
        os.rename ('record.mp4', os.path.join("Records", datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4"))
        if os.path.isfile('record.h264'):
            os.remove("record.h264")  
      
    elif os.path.isfile('record.h264'):
        os.rename('record.h264', os.path.join("Records", datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".h264"))
 
 
#Email küldése 
 
def send_email():
    internet_access()
    sended = False
    
    while not sended:
        try:
            print ('E-mail küldése...')
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = 'Mozgást érzékelt a biztonsági rendszer!'
            message = 'Mozgást érzékelt a biztonsági rendszer!\n\n'
            msg_date = (datetime.datetime.now().strftime("%Y.%m.%d. %H:%M:%S"))
            msg.attach(MIMEText(message + msg_date))
            
            if converted:
                videofile_name = 'record.mp4'
            else:
                videofile_name = 'record.h264'          
            videofile = open(videofile_name, 'rb')
            attachment = MIMEApplication(videofile.read())
            videofile.close()
            attachment.add_header('Content-Disposition','attachment', filename = videofile_name)                   
            msg.attach(attachment)
        
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.sendmail(sender_email,receiver_email, msg.as_string())
            server.quit()
            
            sended = True         
            print ('Email elküldve!')
    
        except Exception as error:
            print ('Hiba az email elküldése közben!\nHibakód: ', error, '\nÚjrapróbálkozás 5mp múlva...')
            time.sleep (5)
        
            

#Főprogram futása

try:
    initialization()
    while True:
        led_light()
        if GPIO.input(pir_pin) == False:
            print ('A rendszer nem érzékel mozgást...')
            time.sleep(1)
                
        elif GPIO.input(pir_pin) == True:
            print ('Mozgás érzékelve!\nRiasztás indítása...')
            video_capture()
            led_light()
            send_email()
            files_manager()
            time.sleep(5)


#Kilépés billenytűzettel

except KeyboardInterrupt:
    print ("Kézi megszakítás!")
    files_manager()
    GPIO.cleanup()

