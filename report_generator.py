# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime,timedelta
from pandas import Series, DataFrame, concat
import numpy as np
from bokeh.models import (Arrow, ColumnDataSource, CustomJS, Label,
                          NormalHead, SingleIntervalTicker, TapTool, DatetimeTickFormatter)
from bokeh.plotting import figure, show
from bokeh.resources import CDN
from bokeh.embed import file_html
import jinja2

def USB_Get_Lines_Loc(df):# df[Time, model_manufacturer,Type] #return [[x1,x2,y]]
    locs= []
    devicelist = df['model_manufacturer'].unique()
    dflist = []
    #split df using model_manufacturer
    for dev in devicelist : 
        dflist.append(df[df['model_manufacturer']==dev])

    for df_splitted in dflist:
        #sort by time 
        df_splitted = df_splitted.sort_values(by=['Time'])
        #checking connet-disconnect
        for i in range(len(df_splitted)-1):
            if df_splitted.iloc[i]['Type'] == 'Connection' and df_splitted.iloc[i+1]['Type'] == 'Disconnection':
                # y = type, x = time of i, i+1

                x_s = df_splitted.iloc[i]['Time']
                x_e = df_splitted.iloc[i+1]['Time']
                y = df_splitted.iloc[i]['model_manufacturer']
                locs.append([x_s,x_e,y])
    return locs


def USB_Draw_Graph(usb_time_dicts,usb_data):

    fill_color = { "Connection": "#00518E", "Disconnection": "#953735" }
    line_color = { "Connection": "#17375E", "Disconnection": "#3B1615" }

    df_c = df_d = DataFrame(columns=('Type','deviceGuid', 'serialNumber', 'productId', 'vendorId', 'diskCapacityBytes', 'bytesPerSector', 'manufacturer', 'model', 'diskId' , 'registryId', 'FileSystem','Time','VolumePath','surpriseRemoval','fill_color','line_color'))

    #merge usb data 
    usb_total_dicts = {}
    for guid in usb_time_dicts[0]:
        for data in usb_data: 
            if data['deviceGuid'] == guid : 
                for con_evt in usb_time_dicts[0][guid]:
                    df_c = df_c.append({
                        'Type' : "Connection",
                        'deviceGuid': guid, 
                        'serialNumber': data['serialNumber'], 
                        'productId': data['productId'], 
                        'vendorId': data['vendorId'], 
                        'diskCapacityBytes': data['diskCapacityBytes'], 
                        'bytesPerSector': data['bytesPerSector'], 
                        'manufacturer': data['manufacturer'], 
                        'model': data['model'], 
                        'diskId': data['diskId'], 
                        'registryId': data['registryId'], 
                        'FileSystem': data['FileSystem'],
                        'Time':con_evt[0],
                        'when':con_evt[0].strftime("%Y-%m-%d %H:%M:%S"),
                        'VolumePath':con_evt[1],
                        'model_manufacturer':data['model']+"("+data['manufacturer']+")"
                        }               
                    , ignore_index=True)

    for guid in usb_time_dicts[1]:
        for data in usb_data: 
            if data['deviceGuid'] == guid : 
                for con_evt in usb_time_dicts[1][guid]:
                    df_d = df_d.append({
                        'Type' : "Disconnection",
                        'deviceGuid': guid, 
                        'serialNumber': data['serialNumber'], 
                        'productId': data['productId'], 
                        'vendorId': data['vendorId'], 
                        'diskCapacityBytes': data['diskCapacityBytes'], 
                        'bytesPerSector': data['bytesPerSector'], 
                        'manufacturer': data['manufacturer'], 
                        'model': data['model'], 
                        'diskId': data['diskId'], 
                        'registryId': data['registryId'], 
                        'FileSystem': data['FileSystem'],
                        'Time':con_evt[0],
                        'when':con_evt[0].strftime("%Y-%m-%d %H:%M:%S"),
                        'VolumePath':"",
                        'surpriseRemoval':con_evt[1],
                        'model_manufacturer':data['model']+"("+data['manufacturer']+")"
                        }               
                    , ignore_index=True)

    df = concat([df_c,df_d])

    ## interactive annotation을 위해 Datetime이 str 형태로 저장된 정보 저장스
    #df_c['when'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in df_c['Time']]
    #df_d['when'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in df_d['Time']]
    #df = DataFrame.join(df_c,df_d)


    tooltips = [
            ('Eventtype','USB @Type'),
            ('deviceGuid','@deviceGuid'),
            ('Datetime','@when'),
            ('manufacturer','@manufacturer'),
            ('model','@model'),        
            ('vendorId','@vendorId'),        
            ('productId','@productId'),
            ('serialNumber','@serialNumber'),
            ('diskCapacityBytes','@diskCapacityBytes'),
            ('bytesPerSector','@bytesPerSector'),
            ('diskId','@diskId'),
            ('registryId','@registryId'),
            ('FileSystem','@FileSystem'),
            ('VolumePath','@VolumePath'),
            ('surpriseRemoval','@surpriseRemoval')        
    ]

    
    x_space = (df['Time'].max()-df['Time'].min())/20
    plot = figure(width=1000, height=600, x_range=(df['Time'].min()-x_space, df['Time'].max()+x_space),y_range=df['model_manufacturer'].unique(),
                #toolbar_location=None, 
                outline_line_color=None,
                y_axis_location="left", x_axis_type="datetime",tooltips=tooltips)
    

    renderer_c = plot.circle(x="Time", y="model_manufacturer", size=10, source=df_c, level="overlay",legend_label="Connect",
                        fill_color=fill_color["Connection"], line_color=line_color["Connection"], fill_alpha=1)
    renderer_d = plot.circle(x="Time", y="model_manufacturer", size=10, source=df_d, level="overlay",legend_label="Disconnect",
                        fill_color=fill_color["Disconnection"], line_color=line_color["Disconnection"], fill_alpha=1)

    plot.hover.renderers = [renderer_c,renderer_d]

    line_locs = USB_Get_Lines_Loc(df)
    for loc in line_locs :
        plot.line([loc[0], loc[1]], [loc[2],loc[2]], line_width=0.85,color="black")

    plot.title.text = "USB Connection Timeline within the Eventtranscript.db"
    plot.title.text_font_size = "19px"
    plot.title.align = "center"

    plot.legend.location = "top_right"
    plot.legend.click_policy="hide"

    plot.xaxis.axis_label = 'TimeStamp'
    plot.xaxis.axis_line_color = "gray"
    plot.xgrid.grid_line_color = None

    plot.xaxis.formatter=DatetimeTickFormatter(
        seconds=["%H:%M:%S.%3N"],
        minutes=["%H:%M:%S"],
        hours=["%H:%M\n%d/%b/%Y"],
        days=["%d/%b/%Y"],
        months=["%d/%b/%Y"],
        years=["%d/%b/%Y"],
    )

    plot.yaxis.axis_label = 'Model\n(Manufacturer)'
    #plot.yaxis.axis_line_color = None
    plot.ygrid.grid_line_dash = "dashed"
    #plot.ygrid.grid_line_color = None


    plot.text(x="Time", y="deviceGuid", x_offset=10, y_offset=-5,
            text="VolumePath", text_align="left", text_baseline="middle",
            text_font_size="12px", source=df)
    #df['Time'].min.strftime("%Y-%m-%d %H:%M:%S")

    disclaimer = Label(x=0, y=0, x_units="screen", y_units="screen",
                    text_font_size="12px", text_color="silver",
                    text='The chart from '+df['Time'].min().strftime("%Y-%m-%d %H:%M:%S")+" to "+df['Time'].max().strftime("%Y-%m-%d %H:%M:%S")+'.')
    plot.add_layout(disclaimer, "below")
    html = file_html(plot, CDN, "usb_plot")
    return html

def USB_Make_Html_Report(devinfo_data, usb_data, graph_html):
    df_usb = DataFrame(usb_data)
    df_dev = DataFrame(devinfo_data)

    styler_usb = df_usb.style.hide_index()
    styler_dev = df_dev.style.hide_index()
    # Template handling
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=''))
    template = env.get_template('./template/usb_report_template.html')
    html = template.render(dev_table = styler_dev.render(), usb_graph = graph_html, usb_table=styler_usb.render())

    # Write the HTML file
    with open('./report/USB_Analysis_Report.html', 'w') as f:
        f.write(html)

def Draw_Browser_Graph(list_browser_action):
    df = DataFrame(list_browser_action)
    df=df.sort_values(by=['Time'])

    fill_color = { "Browser Started": "#00518E", "Tab Created": "#31859C", "Tab Closed": "#948A54", "Browser Closed": "#953735", "Visit": "#4F6228" }
    line_color = { "Browser Started": "#17375E", "Tab Created": "#163C46", "Tab Closed": "#1E1C11", "Browser Closed": "#3B1615", "Visit": "#283214" }


    ## interactive annotation을 위해 Datetime이 str 형태로 저장된 정보 저장
    df['when'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in df['Time']]

    #df 5개로 나눔
    actionlist = df['Action'].unique()
    groups = df.groupby(df.Action)
    df_bs = df_tcr = df_tcl = df_bcl = df_v = DataFrame()
    if "Browser Started" in actionlist : 
        df_bs = groups.get_group("Browser Started")
    if "Tab Created" in actionlist : 
        df_tcr = groups.get_group("Tab Created")
    if "Tab Closed" in actionlist : 
        df_tcl = groups.get_group("Tab Closed")
    if "Browser Closed" in actionlist : 
        df_bcl = groups.get_group("Browser Closed")
    if "Visit" in actionlist : 
        df_v = groups.get_group("Visit")


    tooltips = [
            ('Datetime','@when'),
            ('Action','@Action'),
            ('Url','@Url'),
            ('Title','@Title'),
            ('Application','@Application'),        
            ('Application Version','@Application Version'),        
            ('Connection Type','@Connection Type'),
    ]



    x_space = (df['Time'].max()-df['Time'].min())/20
    yrange_dir = ["Browser Started","Tab Created","Visit","Tab Closed","Browser Closed"]
    plot = figure(width=1600, height=600, x_range=(df['Time'].min()-x_space, df['Time'].max()+x_space),y_range=yrange_dir,
                #toolbar_location=None, 
                outline_line_color=None,
                y_axis_location="left", x_axis_type="datetime",tooltips=tooltips)

    renderer_bs = plot.circle(x="Time", y="Action", size=10, source=df_bs, level="overlay",legend_label="Browser Started",
                        fill_color=fill_color["Browser Started"], line_color=line_color["Browser Started"], fill_alpha=1)

    renderer_tcr = plot.circle(x="Time", y="Action", size=10, source=df_tcr, level="overlay",legend_label="Tab Created",
                        fill_color=fill_color["Tab Created"], line_color=line_color["Tab Created"], fill_alpha=1)

    renderer_tcl = plot.circle(x="Time", y="Action", size=10, source=df_tcl, level="overlay",legend_label="Tab Closed",
                        fill_color=fill_color["Tab Closed"], line_color=line_color["Tab Closed"], fill_alpha=1)

    renderer_bcl = plot.circle(x="Time", y="Action", size=10, source=df_bcl, level="overlay",legend_label="Browser Closed",
                        fill_color=fill_color["Browser Closed"], line_color=line_color["Browser Closed"], fill_alpha=1)

    renderer_v = plot.circle(x="Time", y="Action", size=10, source=df_v, level="overlay",legend_label="Visit",
                        fill_color=fill_color["Visit"], line_color=line_color["Visit"], fill_alpha=1)
                


    plot.hover.renderers = [renderer_bs,renderer_tcr,renderer_tcl,renderer_bcl,renderer_v]

    plot.title.text = "Timeline of the Web Browser Actions within the Eventtranscript.db"
    plot.title.text_font_size = "19px"
    plot.title.align = "center"

    plot.legend.location = "top_right"
    plot.legend.click_policy="hide"

    plot.xaxis.axis_label = 'TimeStamp'
    plot.xaxis.axis_line_color = "gray"
    plot.xgrid.grid_line_color = None

    plot.xaxis.formatter=DatetimeTickFormatter(
        seconds=["%H:%M:%S.%3N"],
        minutes=["%H:%M:%S"],
        hours=["%H:%M\n%d/%b/%Y"],
        days=["%d/%b/%Y"],
        months=["%d/%b/%Y"],
        years=["%d/%b/%Y"],
    )

    plot.yaxis.axis_label = 'Actions '
    #plot.yaxis.axis_line_color = None
    plot.ygrid.grid_line_dash = "dashed"

    
    #plot.text(x="Time", y="Action", x_offset=10, y_offset=-5,
    #        text="Title", text_align="left", text_baseline="middle",
    #        text_font_size="12px", source=df)
    #df['Time'].min.strftime("%Y-%m-%d %H:%M:%S")

    disclaimer = Label(x=0, y=0, x_units="screen", y_units="screen",
                    text_font_size="12px", text_color="silver",
                    text='The chart from '+df['Time'].min().strftime("%Y-%m-%d %H:%M:%S")+" to "+df['Time'].max().strftime("%Y-%m-%d %H:%M:%S")+'.')
    plot.add_layout(disclaimer, "below")

    
    html = file_html(plot, CDN, "browser_plot")
    return html

def Make_Browser_Html_Report(devinfo_data, list_browser_action):
    graph_html = Draw_Browser_Graph(list_browser_action)

    df = DataFrame(list_browser_action)
    df_dev = DataFrame(devinfo_data)
    
    groups = df.groupby(df.Action)
    df_visit = groups.get_group("Visit")[['Time','Title','Url','Connection Type']]
    df_browser = df[['Application','Application Version']].drop_duplicates()

    styler_browser = df_browser.style.hide_index()
    styler_visit = df_visit.style.hide_index()
    styler_dev = df_dev.style.hide_index()

    # Template handling
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=''))
    template = env.get_template('./template/web_browser_report_template.html')
    html = template.render(dev_table = styler_dev.render(), browser_graph = graph_html, browser_table=styler_browser.render(),visit_table=styler_visit.render())

    # Write the HTML file
    with open('./report/Web_Browser_Analysis_Report.html', 'w') as f:
        f.write(html)

def WiFi_Get_Lines_Loc(df):
    locs= []
    #devicelist = df['model_manufacturer'].unique()
    ssidlist = df['ssid'].unique()
    dflist = []
    #split df using ssid
    for s in ssidlist : 
        dflist.append(df[df['ssid']==s])

    for df_splitted in dflist:
        #sort by time 
        df_splitted = df_splitted.sort_values(by=['Time'])
        #checking connet-disconnect
        for i in range(len(df_splitted)-1):
            if df_splitted.iloc[i]['Action'] == 'Connection Succeed' and df_splitted.iloc[i+1]['Action'] == 'Disconnection':
                # y = type, x = time of i, i+1
                x_s = df_splitted.iloc[i]['Time']
                x_e = df_splitted.iloc[i+1]['Time']
                y = df_splitted.iloc[i]['ssid']
                locs.append([x_s,x_e,y])
    return locs

def Draw_WiFi_Graph(list_wifi_action):
    df = DataFrame(list_wifi_action)
    df=df.sort_values(by=['Time'])

    fill_color = { "Connection Succeed": "#00518E", "Connection Failed": "#948A54", "Disconnection": "#953735", "Scan": "#4F6228" }
    line_color = { "Connection Succeed": "#17375E", "Connection Failed": "#1E1C11", "Disconnection": "#3B1615", "Scan": "#283214" }

    df['when'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in df['Time']]

    #df 5개로 나눔
    actionlist = df['Action'].unique()
    
    groups = df.groupby(df.Action)
    df_cs = df_cf = df_d = df_s = DataFrame()
    if "Connection Succeed" in actionlist : 
        df_cs = groups.get_group("Connection Succeed")
    if "Connection Failed" in actionlist : 
        df_cf = groups.get_group("Connection Failed")
    if "Disconnection" in actionlist : 
        df_d = groups.get_group("Disconnection")
    if "Scan" in actionlist : 
        df_s = groups.get_group("Scan")

    tooltips = [
        ("Action" , "@Action"),
        ("Time" , "@Time"), 
        ("ssid" , "@ssid"),
        ("bssid" , "@bssid"),
        ("wlanStatusCode" , "@wlanStatusCode"),
        ("detailedStatusCode" , "@detailedStatusCode"),
        ("isAUserLoggedIn" , "@isAUserLoggedIn"),
        ("isHidden" , "@isHidden"),
        ("authAlgo" , "@authAlgo"),
        ("cipherAlgo" , "@cipherAlgo"),
        ("phyType" , "@phyType"),        
        ("disconnectReason" , "@disconnectReason"),
        ("connectionMode" , "@connectionMode"),
        ("interfaceGuid" , "@interfaceGuid"),
        ("interfaceType" , "@interfaceType"),
        ("interfaceDescription" , "@interfaceDescription")  
    ]

    
    x_space = (df['Time'].max()-df['Time'].min())/20
    plot = figure(width=1000, height=600, x_range=(df['Time'].min()-x_space, df['Time'].max()+x_space),y_range=df['ssid'].unique(),
                #toolbar_location=None, 
                outline_line_color=None,
                y_axis_location="left", x_axis_type="datetime",tooltips=tooltips)
    

    renderer_cs = plot.circle(x="Time", y="ssid", size=10, source=df_cs, level="overlay",legend_label="Connection Succeed",
                        fill_color=fill_color["Connection Succeed"], line_color=line_color["Connection Succeed"], fill_alpha=1)
    renderer_cf = plot.circle(x="Time", y="ssid", size=10, source=df_cf, level="overlay",legend_label="Connection Failed",
                    fill_color=fill_color["Connection Failed"], line_color=line_color["Connection Failed"], fill_alpha=1)
    renderer_d = plot.circle(x="Time", y="ssid", size=10, source=df_d, level="overlay",legend_label="Disconnection",
                    fill_color=fill_color["Disconnection"], line_color=line_color["Disconnection"], fill_alpha=1)
    renderer_s = plot.circle(x="Time", y="ssid", size=10, source=df_s, level="overlay",legend_label="Scan",
                    fill_color=fill_color["Scan"], line_color=line_color["Scan"], fill_alpha=1)
    
    plot.hover.renderers = [renderer_cs,renderer_cf,renderer_d,renderer_s]

    line_locs = WiFi_Get_Lines_Loc(concat([df_cs,df_d]))
    for loc in line_locs :
        plot.line([loc[0], loc[1]], [loc[2],loc[2]], line_width=0.85,color="black")

    plot.title.text = "WiFi-Related Behavior Timeline within the Eventtranscript.db"
    plot.title.text_font_size = "19px"
    plot.title.align = "center"

    plot.legend.location = "top_right"
    plot.legend.click_policy="hide"

    plot.xaxis.axis_label = 'TimeStamp'
    plot.xaxis.axis_line_color = "gray"
    plot.xgrid.grid_line_color = None

    plot.xaxis.formatter=DatetimeTickFormatter(
        seconds=["%H:%M:%S.%3N"],
        minutes=["%H:%M:%S"],
        hours=["%H:%M\n%d/%b/%Y"],
        days=["%d/%b/%Y"],
        months=["%d/%b/%Y"],
        years=["%d/%b/%Y"],
    )

    plot.yaxis.axis_label = 'ssid'
    #plot.yaxis.axis_line_color = None
    plot.ygrid.grid_line_dash = "dashed"
    #plot.ygrid.grid_line_color = None

    """
    plot.text(x="Time", y="ssid", x_offset=10, y_offset=-5,
            text="ssid", text_align="left", text_baseline="middle",
            text_font_size="12px", source=df)
    """
    #df['Time'].min.strftime("%Y-%m-%d %H:%M:%S")

    disclaimer = Label(x=0, y=0, x_units="screen", y_units="screen",
                    text_font_size="12px", text_color="silver",
                    text='The chart from '+df['Time'].min().strftime("%Y-%m-%d %H:%M:%S")+" to "+df['Time'].max().strftime("%Y-%m-%d %H:%M:%S")+'.')
    plot.add_layout(disclaimer, "below")
    html = file_html(plot, CDN, "wifi_plot")
    return html

def WiFi_Make_Html_Report(devinfo_data, wifi_data):
    graph_html = Draw_WiFi_Graph(wifi_data)

    df_wifi = DataFrame(wifi_data)
    df_dev = DataFrame(devinfo_data)

    styler_wifi = df_wifi.style.hide_index()
    styler_dev = df_dev.style.hide_index()
    # Template handling
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=''))
    template = env.get_template('./template/wifi_report_template.html')
    html = template.render(dev_table = styler_dev.render(), wifi_graph = graph_html)
    with open('./report/WiFi_Analysis_Report.html', 'w') as f:
        f.write(html)

