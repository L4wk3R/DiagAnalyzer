# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime,timedelta
import report_generator

def mstime2dt(timestamp):
    timestamp = timestamp /10
    return datetime(1601,1,1) + timedelta(microseconds=timestamp)

def GetDeviceInfo(f):
    conn = sqlite3.connect(f,isolation_level=None)
    c = conn.cursor()
    #SELECT payload FROM events_persisted WHERE payload LIKE '%ext%' AND payload LIKE '%os%' AND payload LIKE '%device%' AND payload LIKE '%protocol%' AND payload LIKE '%user%' AND payload LIKE '%loc%' AND payload LIKE '%name%' AND payload LIKE '%ver%' AND payload LIKE '%localId%' AND payload LIKE '%devMake%' AND payload LIKE '%devMake%' AND payload LIKE '%devModel%' AND payload LIKE '%tz%' 
    c.execute("SELECT payload FROM events_persisted WHERE payload LIKE '%"+"ext%' AND payload LIKE '%"+"os%' AND payload LIKE '%"+"device%' AND payload LIKE '%protocol%' AND payload LIKE '%"+"user%' AND payload LIKE '%"+"loc%' AND payload LIKE '%name%' AND payload LIKE '%ver%' AND payload LIKE '%"+"localId%' AND payload LIKE '%"+"devMake%' AND payload LIKE '%"+"devMake%' AND payload LIKE '%"+"devModel%' AND payload LIKE '%tz%' ")
    
    payload = json.loads(c.fetchone()[0])
    OSname = payload['ext']['os']['name']
    OSver = payload['ext']['os']['ver']
    devID = payload['ext']['device']['localId']
    devClass = payload['ext']['device']['deviceClass']
    devMake = payload['ext']['protocol']['devMake']
    devModel = payload['ext']['protocol']['devModel']
    userLocalId = payload['ext']['user']['localId']
    timezone = payload['ext']['loc']['tz']
    
    deviceinfo_dict = {
        "OSname" : OSname,
        "OSver" : OSver,
        "devID" : devID,
        "devClass" : devClass,
        "devMake" : devMake,
        "devModel" : devModel,
        "userLocalId" : userLocalId,
        "timezone" : timezone
    }
    return [deviceinfo_dict]


def VerifyUrl(f, CorrelationGuid):
    conn = sqlite3.connect(f,isolation_level=None)
    c = conn.cursor()
    c.execute("SELECT full_event_name,payload FROM events_persisted WHERE payload LIKE  '%"+CorrelationGuid+"%'")
    #get event names
    eventnames = []
    for e in c.fetchall():
        eventnames.append(e[0].split('Microsoft.')[1])
    if 'WebBrowser.HistoryJournal.HJ_HistoryAddUrl' not in eventnames :
        return False
    elif 'WebBrowser.HistoryJournal.HJ_NavigateCompleteExtended' not in eventnames : 
        return False
    elif 'WebBrowser.HistoryJournal.HJ_HistoryAddUrlEx' not in eventnames :
        return False
    else : 
        return True

def GetBrowserHistory(f):

    conn = sqlite3.connect(f,isolation_level=None)
    c = conn.cursor()
    c.execute("SELECT payload FROM events_persisted WHERE full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_BeforeNavigateExtended%' ")


    print("\n\n\n[+]Browser History\n")
    print("time,timezone,app,appver,conntype,url,Title")
    for e in c.fetchall():
        payload = json.loads(e[0])
        CorrelationGuid = payload['data']['CorrelationGuid']
        
        if VerifyUrl(f,CorrelationGuid) == True : 
            c2 = conn.cursor()
            c2.execute("SELECT payload FROM events_persisted WHERE payload LIKE  '%"+CorrelationGuid+"%' AND full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_HistoryAddUrlEx%'")
            #get event for get page title
            payload2 = json.loads(c2.fetchone()[0])
        
            time = payload['data']['Timestamp']
            #timezone = payload['ext']['loc']['tz']
            app = payload['ext']['app']['name']
            appver = payload['ext']['app']['ver']
            conntype = payload['data']['ConnectionType']
            url = payload['data']['navigationUrl']
            Title = payload2['data']['PageTitle']
            print([time,timezone,app,appver,conntype,url,Title])

def GetBrowserActions_Main(f): # This func return Dataframe Objects. sorted by timestamp
    conn = sqlite3.connect(f,isolation_level=None)
    c = conn.cursor()

    list_browser_action = []
    #Get Open Events
    c.execute("SELECT timestamp FROM events_persisted WHERE full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_BrowserLaunchInfo%'")
    for e in c.fetchall():
        list_browser_action.append({'Action':'Browser Started','Time':mstime2dt(e[0])})
    
    #Get Open Tab Events
    c.execute("SELECT timestamp FROM events_persisted WHERE full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_TabCreated%'")
    for e in c.fetchall():
        list_browser_action.append({'Action':'Tab Created','Time':mstime2dt(e[0])})
    
    #Get Closed Tab Events
    c.execute("SELECT timestamp,full_event_name,payload FROM events_persisted WHERE full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_TabClosed%'")
    for e in c.fetchall():
        list_browser_action.append({'Action':'Tab Closed','Time':mstime2dt(e[0])})
            
    #Get Browser Closed Events
    c.execute("SELECT timestamp,full_event_name,payload FROM events_persisted WHERE full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_TabAllClosed%'")
    for e in c.fetchall():
        list_browser_action.append({'Action':'Browser Closed','Time':mstime2dt(e[0])})
    
    #Get Browsing History
    c.execute("SELECT timestamp, payload FROM events_persisted WHERE full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_BeforeNavigateExtended%' ")

    for e in c.fetchall():
        payload = json.loads(e[1])
        CorrelationGuid = payload['data']['CorrelationGuid']
        
        if VerifyUrl(f,CorrelationGuid) == True : 
            c2 = conn.cursor()
            c2.execute("SELECT payload FROM events_persisted WHERE payload LIKE  '%"+CorrelationGuid+"%' AND full_event_name LIKE '%Microsoft.WebBrowser.HistoryJournal.HJ_HistoryAddUrlEx%'")
            #get event for get page title
            payload2 = json.loads(c2.fetchone()[0])
        
            time = mstime2dt(e[0])
            app = payload['ext']['app']['name']
            appver = payload['ext']['app']['ver']
            conntype = payload['data']['ConnectionType']
            url = payload['data']['navigationUrl']
            Title = payload2['data']['PageTitle']
            
            list_browser_action.append({
                'Action':'Visit',
                'Time': time,
                'Application': app,
                'Application Version' : appver,
                'Connection Type' : conntype,
                'Url' : url,
                'Title' : Title
            })

    report_generator.Make_Browser_Html_Report(GetDeviceInfo(f), list_browser_action)

def GetUSBConnectTime(c):
    dict_conn= {}
    dict_disconn = {}

    #get connection time 
    c.execute("SELECT timestamp,payload FROM events_persisted WHERE full_event_name='Microsoft.Windows.Storage.Classpnp.DeviceGuidGenerated'")
    events = c.fetchall()
    for e in events:
        conntime = mstime2dt(e[0])
        deviceguid = json.loads(e[1])['data']['deviceGuid']        
        #get where device mounted
        c.execute("SELECT timestamp,payload FROM events_persisted WHERE full_event_name = 'Microsoft.Windows.Storage.StorageService.SdCardStatus'")
        e2 = c.fetchone()
        if e2 != None and e2[0] - e[0] < 30000000: 
            VolumePath = json.loads(e2[1])['data']['VolumePath']    
        else : 
            VolumePath = ""

        if deviceguid not in dict_conn : 
            dict_conn[deviceguid]=[[conntime,VolumePath]]
        else : 
            dict_conn[deviceguid].append([conntime,VolumePath])
    
    #get disconnection time (surprise removed is not appended yet)
    c.execute("SELECT timestamp,payload FROM events_persisted WHERE full_event_name LIKE '%Microsoft.Windows.Storage.Classpnp.DeviceRemoved%'")     
    for e in c.fetchall():
        disconntime = mstime2dt(e[0])
        deviceguid = json.loads(e[1])['data']['deviceGuid']   
        surprised = json.loads(e[1])['data']['surpriseRemoval']     
        if deviceguid not in dict_disconn : 
            dict_disconn[deviceguid]=[[disconntime,surprised]]
        else : 
            dict_disconn[deviceguid].append([disconntime,surprised])

    return dict_conn, dict_disconn 

def GetUSBInfo(c,guid):
    c.execute("SELECT payload FROM events_persisted WHERE payload LIKE '%"+guid+"%'")
    events = c.fetchall()

    #initialize
    serialNumber = productId = vendorId = diskCapacityBytes = bytesPerSector = manufacturer = model = serialNumber = diskId = registryId = FileSystem = ""
    for e in events:
        payload = json.loads(e[0])
        #get information using guid
        event_name = payload['name']    
        if event_name == "Microsoft.Windows.Storage.Classpnp.DeviceDescriptorData" :
            serialNumber = payload['data']['serialNumber']
            productId = payload['data']['productId']
            vendorId = payload['data']['vendorId']
            diskCapacityBytes = payload['data']['diskCapacityBytes']
        elif event_name == "Microsoft.Windows.Storage.Classpnp.DeviceAccessAlignment" :
            bytesPerSector = payload['data']['bytesPerSector'] 
        elif event_name == "Microsoft.Windows.Storage.Partmgr.DiskDiscovery" :
            bytesPerSector = payload['data']['bytesPerSector']
            diskCapacityBytes = payload['data']['capacityBytes']
            manufacturer = payload['data']['manufacturer']
            model = payload['data']['model']
            serialNumber = payload['data']['serial']
            diskId = payload['data']['diskId']
            registryId = payload['data']['registryId']
        
    #get additional information using serial number
    if len(serialNumber) > 0 : 
        c.execute("SELECT payload FROM events_persisted WHERE payload LIKE '%"+serialNumber+"%' AND full_event_name = 'Microsoft.Windows.Storage.StorageService.UsbDiskArrival'")
        payload2 = c.fetchone()
        if payload2 != None : 
            payload2 = json.loads(payload2[0])
            FileSystem = payload2['data']['FileSystem']

    data_structured = {
        'deviceGuid': guid,
        'serialNumber' : serialNumber,
        'productId' : productId,
        'vendorId' : vendorId,
        'diskCapacityBytes' : diskCapacityBytes,
        'bytesPerSector': bytesPerSector,
        'manufacturer' : manufacturer,
        'model' : model,
        'serialNumber' : serialNumber,
        'diskId' : diskId,
        'registryId' : registryId,
        'FileSystem' : FileSystem
    }
    return data_structured
            
def GetUSBConnectInfoMain(f):

    conn = sqlite3.connect(f,isolation_level=None)
    c = conn.cursor()
    usb_time_dicts = GetUSBConnectTime(c)
    guid_list = set(list(usb_time_dicts[0].keys())+list(usb_time_dicts[1].keys()))
    
    #get usb info
    usb_data = []
    for guid in guid_list:
        usb_data.append(GetUSBInfo(c,guid))
    
    #Get Analyzed Device Info
    devinfo_data = GetDeviceInfo(f)
    #report_generator 
    graph_html = report_generator.USB_Draw_Graph(usb_time_dicts,usb_data)
    report_generator.USB_Make_Html_Report(devinfo_data, usb_data, graph_html)

def GetInstalledApplication(f): #will be updated
    conn = sqlite3.connect(f,isolation_level=None)
    c = conn.cursor()
    app_events = []
    #Get Application Events
    c.execute("SELECT payload FROM events_persisted WHERE full_event_name LIKE '%Microsoft.Windows.Inventory.Core.InventoryApplicationAdd%'")    
    for e in c.fetchall():
        payload = json.loads(e[0])
        Name = payload['data']['Name']
        Version = payload['data']['Version']
        Publisher = payload['data']['Publisher']
        #language = payload['data']['Language']
        Source = payload['data']['Source']
        type_ = payload['data']['Type']
        #storeapptype = payload['data']['StoreAppType']
        #msiproductcode = payload['data']['MsiProductCode']
        #msipackagecode = payload['data']['MsiPackageCode']
        msiintalldata = payload['data']['MsiInstallDate']
        hiddenarp = payload['data']['HiddenArp']
        packagefullname = payload['data']['PackageFullName']
        installdate = payload['data']['InstallDate']
        installdatemsi = payload['data']['InstallDateMsi']
        installdatefromlinkfile = payload['data']['InstallDateFromLinkFile']
        installdatearplastmodified = payload['data']['InstallDateArpLastModified']        

def GetWiFiConnectInfo(f):
    """
    Scan, Connect, Disconnect 
    """
    list_wifi_action = []
    conn = sqlite3.connect(f,isolation_level=None)
    c = conn.cursor()
    #scan result
    c.execute("SELECT timestamp, payload FROM events_persisted WHERE full_event_name LIKE 'WlanMSM.WirelessScanResults'")
    for e in c.fetchall():
        time = mstime2dt(e[0])
        payload = json.loads(e[1])
        scanresults = payload['data']['ScanResults'].split("\n")
        for s in scanresults : 
            s=s.split('\t')
            if len(s)>2 : 
                ssid = s[0]
                bssid = s[2]
                list_wifi_action.append({
                    "Action" : "Scan",
                    "Time" : time, 
                    "ssid" : ssid,
                    "bssid" : bssid
                })
    #connection 
    c.execute("SELECT timestamp, payload FROM events_persisted WHERE full_event_name == 'Microsoft.OneCore.NetworkingTriage.GetConnected.WiFiConnectedEvent'")
    for e in c.fetchall():
        time = mstime2dt(e[0])
        payload = json.loads(e[1])
        
        wlanStatusCode = payload['data']['wlanStatusCode']
        detailedStatusCode = payload['data']['detailedStatusCode']
        isAUserLoggedIn = payload['data']['isAUserLoggedIn']

        ssid = payload['data']['ssid']
        bssid = payload['data']['bssid']
        isHidden = payload['data']['isHidden']
        authAlgo = payload['data']['authAlgo']
        cipherAlgo = payload['data']['cipherAlgo']

        interfaceGuid = payload['data']['interfaceGuid']
        interfaceType = payload['data']['interfaceType']
        interfaceDescription = payload['data']['interfaceDescription']

        if "0x0 " in wlanStatusCode :
            action = "Connection Succeed"
        else : 
            action = "Connection Failed"
        
        list_wifi_action.append({
                "Action" : action,
                "Time" : time, 
                "ssid" : ssid,
                "bssid" : bssid,
                "wlanStatusCode" : wlanStatusCode,
                "detailedStatusCode" : detailedStatusCode,
                "isAUserLoggedIn" : isAUserLoggedIn,
                "isHidden" : isHidden,
                "authAlgo" : authAlgo,
                "cipherAlgo" : cipherAlgo,
                "interfaceGuid" : interfaceGuid,
                "interfaceType" : interfaceType,
                "interfaceDescription" : interfaceDescription
        })

    #disconnection
    c.execute("SELECT timestamp, payload FROM events_persisted WHERE full_event_name == 'Microsoft.OneCore.NetworkingTriage.GetConnected.WiFiDisconnectedEvent'")
    for e in c.fetchall():
        time = mstime2dt(e[0])
        payload = json.loads(e[1])

        disconnectReason = payload['data']['disconnectReason']
        connectionMode = payload['data']['connectionMode']    

        ssid = payload['data']['ssid']
        bssid = payload['data']['bssid']
        authAlgo = payload['data']['authAlgo']
        cipherAlgo = payload['data']['cipherAlgo']
        phyType = payload['data']['phyType']
        
        interfaceGuid = payload['data']['interfaceGuid']
        interfaceType = payload['data']['interfaceType']
        
        list_wifi_action.append({
                "Action" : 'Disconnection',
                "Time" : time, 
                "ssid" : ssid,
                "bssid" : bssid,
                "disconnectReason" : disconnectReason,
                "connectionMode" : connectionMode,
                "phyType" : phyType,
                "authAlgo" : authAlgo,
                "cipherAlgo" : cipherAlgo,
                "interfaceGuid" : interfaceGuid,
                "interfaceType" : interfaceType
        })
    #report_generator.Draw_WiFi_Graph(list_wifi_action)
    report_generator.WiFi_Make_Html_Report(GetDeviceInfo(f), list_wifi_action)

