from analyzer import *
from report_generator import * 
from argparse import ArgumentParser
import os


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-i','--infile',type=str,required=True,help = "input file path", default = ".\\Eventtranscript.db")
    parser.add_argument('-o','--option',type=str,required=True,help = "option for analysis (usb,browser,wifi)", default = "usb")
    args = parser.parse_args()

    #create report directory
    try : 
        if not os.path.exists(".\\report\\") :
            os.makedirs(".\\report\\")
    except OSError : 
        print ('[-]Error: Creating directory .\\report\\ ')

    #check file exists
    if not os.path.exists(args.infile) :
        print('[-]Error : Input file does not exist.')
        exit(1)

    if args.option == 'usb':
        GetUSBConnectInfoMain(args.infile)
    elif args.option == 'browser':
        GetBrowserActions_Main(args.infile)
    elif args.option == 'wifi':
        GetWiFiConnectInfo(args.infile)
    else : 
        print('[-]Error : Invalild option. Use one of usb, browser, or wifi')