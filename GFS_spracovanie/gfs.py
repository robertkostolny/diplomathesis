#-------------------------------------------------------------------------------
# Name:        spracovanie dat MEDARD
# Purpose:     Diplomova praca - Moznosti modelovania zloziek oneskoreni signalu z vyuzitim NWP
#
# Author:      Kostolny Robert
#
# Created:     20/10/2016
# Copyright:   (c) Robko 2016
# Licence:     VSB - TUO, Institut geoinformatiky
#-------------------------------------------------------------------------------

import os
from datetime import date
import utility
import re
import shutil

#mazanie suborov
##pathMET = os.path.join("c:\\Users\\Robko\\Desktop\\skola\\DP\\MEDARD_spracovanie\\02temp\\myMeteo")
##shutil.rmtree(pathMET)
##os.mkdir(pathMET, 0755);

#pathIWV = os.path.join("c:\\Users\\Robko\\Desktop\\skola\\DP\\MEDARD_spracovanie\\03results\\IWV")
#shutil.rmtree(pathIWV)
#os.mkdir(pathIWV, 0755);

#stanice, ktore budu filtrovane
##stations = ['BISK','VSBO','LYSH','PLZE','KUNZ','GOPE','TUBO','VACO','MARJ','WTZR','DRES','ZYWI','KATO','MOPI']
##
###...............................................................................
###funkcia pre filtraciu atmosferickych dat pre stanice
###ktore vstupia do porovnania a zapis do noveho dokumentu
###...............................................................................
##def medardtATM(metMEDARD, myMEDARD):
##    chyba = 0
##    if len(os.listdir(metMEDARD)) > 0:
##        for file in os.listdir(metMEDARD):
##            f = open(metMEDARD+'/'+file, 'r',)
##            myLines = f.readlines()
##            f.close()
##
##        Body = myLines[1:]
##        Body2 = []
##        for radek in Body:
##            dd = radek.split()
##            if dd[4] in stations:
##                Body2.append(dd)
##
##        for r in Body2:
##            pressure = float(r[8])
##            press = pressure*10
##            temperature = r[5]
##            meteo_high = r[9]
##            myStationName = r[4]
##            time = r[1][0:2] + r[1][3:5]
##            date = r[0][2:4] + r[0][5:7] + r[0][8:10]
##            myLineNew = myStationName + ' ' + date + ' ' + time + ' ' + str(press) + ' ' +str(temperature) + ' ' +str(meteo_high)
##            if os.path.exists(myMEDARD+'/'+myStationName+date+'.MET'):
##                subor = os.path.join(myMEDARD+'/'+myStationName+date+'.MET')
##                subor2 = open(subor, 'a')
##                subor2.write(myLineNew + '\n')
##                subor2.close()
##            else:
##                subor3 = open(myMEDARD+'/'+myStationName+date+'.MET', 'w')
##                subor3.write(myLineNew + '\n')
##                subor3.close()
##
##    else:
##        print '==============================='
##        print 'konverzia neprebehla v poriadku'
##        print '==============================='
##        chyba = 1
##        sys.exit()
##
##    if chyba == 0:
##        print '===================================================================='
##        print 'konverzia dat modelu MEDARD do vlastneho formatu prebehla v poriadku'
##        print '===================================================================='

#...............................................................................
#funkcia pre konverziu ZTD na IWV
#...............................................................................
def konverziaZTD_na_IWV(myGFS,ZTD_TRP,STA,result_IWV):

    flag_error = 0

    soubor=[]

    stations_coord_meteo = []

    #otvorenie suboru s udajmi o referencnej stanici(zem.sirka, elipsoidicka vyska stanice,
    #vyska kde boli odobrane atm. veliciny-medard_vyska(prepocitana na elipsoidicku)
    d = open(STA+'/meteo.STA', 'r')
    metSTAlines = d.readlines()
    for radek in metSTAlines[1:]:
        meteo_sour = []
        radek_coord = re.split('\s+',radek.strip(' '))
        meteo_sour.append(radek_coord[0])
        meteo_sour.append(float(radek_coord[1]))
        meteo_sour.append(float(radek_coord[2]))
        meteo_sour.append(float(radek_coord[3]))
        meteo_sour.append(float(radek_coord[4]))
        stations_coord_meteo.append(meteo_sour)

    stations_list_meteo = []
    station_dictionary = {}

    #vyber nazvov stanic do zoznamu s ktorymi sa pracuje + datum na stanici
    if len(os.listdir(myGFS)) > 0:
        for file in os.listdir(myGFS):
            stations_list_meteo.append(file[0:10])
            station_dictionary.update({file[0:10]:file})

    #nacitanie TRP suborov, so ZTD zlozkou
    if len(os.listdir(ZTD_TRP)) > 0:
        for file in os.listdir(ZTD_TRP):
            f = open(ZTD_TRP+'/'+file, 'r',)
            myLines = f.readlines()
            f.close()

            #odstrihnutie hlavicky z TRP suboru a zapisanie do Body
            for myline in myLines:
                if not re.search('SIGMA_E', myline) == None:
                    myHeaderFla = myLines.index(myline)

            Body = myLines[myHeaderFla+1:]

            #vyber riadkov podla stanic zapisanych v zozname vytvorenom v prvom kroku tejto funkcie
            Body2 = []
            for radek in Body:
                if radek[1:5] + radek[26:28] + radek[29:31] + radek[32:34] in stations_list_meteo:
                    Body2.append(radek)

            #vytvorenie premennej pre den v roku s ktorym sa pracuje
            den_roku = int(Body[1][32:34])

            for station in stations_list_meteo:

                #priprava suborov pre zapis vysledkov
                zapis = open(result_IWV+'/'+station+'.IWV', 'a')

                linesMeteo = []
                MeteoKey = {}

                #nacitanie meteo dat pre stanicu s ktorou sa aktualne pracuje
                soubor = station_dictionary[station]
                g = open(myGFS+'/'+soubor, 'r',)
                linesMeteo = g.readlines()
                g.close()

                #zistenie vsetkych intervalov pre ktore su v meteo subore udaje
                # a zapisanie do slovniku MEteoKey(index riadku suboru: cas zazanamu)
                #sluzi k nablizsiemu vyberu meteo merania pre ZTD zaznam
                for i in range (0,len(linesMeteo)):
                    MeteoKey.update({i:linesMeteo[i][12:16]})

                #ziskanie udajov o ref. stanici pre aktualne spracovavanu stanicu
                for k in range(len(stations_coord_meteo)):
                    if stations_coord_meteo[k][0] == station[0:4]:
                        coord_meteo = stations_coord_meteo[k]

                #vypocet H_delta pre kazdu stanicu
                height_difference = coord_meteo[4] - coord_meteo[2]

                #prechadzanie riadkov v troposferickom subore
                for lineZTD in Body2:
                    if lineZTD[1:5] + lineZTD[26:28] + lineZTD[29:31] + lineZTD[32:34] == station:
                        year = int('20'+lineZTD[26:28])
                        month = int(lineZTD[29:31])
                        doy = int(lineZTD[32:34])

                        #reseni situace s poslednim zaznamem v ZTD, ktery ma datum pro nasledujici den a hodinu 00:00
                        #nahradi se stavajicim dnem a casem 24:00 (meteo RINEX obsahuji posledni zaznam 23:59)
                        if den_roku != doy:
                            date_ztd = (date.fromordinal(date(year, month, 1).toordinal() + doy - 1)).strftime("%y%m%d")
                            time_ztd = 2400
                        else:
                            date_ztd = (date.fromordinal(date(year, month, 1).toordinal() + doy - 1)).strftime("%y%m%d")
                            time_ztd_seconds1 = int(lineZTD[35:37])*60*60
                            time_ztd_seconds2 = int(lineZTD[38:40])*60
                            time_ztd_seconds = int(time_ztd_seconds1) + int(time_ztd_seconds2)
                            time_ztd_60 = utility.seconds_to_hours_minutes(time_ztd_seconds) #volanie funkcie pre prevod casu v s
                            hodiny = int(time_ztd_60[0:2])*100
                            minuty = int((float(time_ztd_60[2:4])/60)*100)
                            time_ztd = hodiny + minuty

                        #vyber zaznamu ktory je najblizsi ZTD hodnote
                        minDelta = 84600
                        for klic, hodnota in MeteoKey.iteritems():
                            hodiny_met = int(hodnota[0:2])*100
                            minuty_met = int((float(hodnota[2:4])/60)*100)
                            time_met = hodiny_met + minuty_met
                            time_delta = int(time_ztd) - time_met

                            if abs(time_delta) < minDelta:
                                minDelta = time_delta
                                memKey = klic

                        radek_ztd_pole = re.split('\s+',lineZTD.strip(' '))
                        radek_meteo_pole = re.split('\s+',linesMeteo[memKey].strip(' '))

                        #volanie funkcie pre vypocet ZHD, ZWD, IWV
                        IWV_pole = utility.computeIWV(coord_meteo[1],coord_meteo[2],height_difference,float(radek_meteo_pole[3]),float(radek_meteo_pole[4]),float(radek_ztd_pole[12]))
        ##                print str(station),coord_meteo[1],coord_meteo[2],height_difference,float(radek_meteo_pole[3]),float(radek_meteo_pole[4]),float(radek_ztd_pole[12])
       ##                 print IWV_pole
                        zapis.write(str(station) + ' ' + str(IWV_pole[0]) + ' ' + str(IWV_pole[1]) + ' ' + str(IWV_pole[2]) + ' ' + str(IWV_pole[3]) + ' ' + str(IWV_pole[4]) + '\n')

                zapis.close()

            if flag_error == 0:
                print '============================================================================='
                print "prebehol vypocet zloziek ZHD, ZWD, IWV; vysledky su ulozene v: "+result_IWV
                print '============================================================================='

#input01

myGFS = '02temp/myGFS'
ZTD_TRP = '01input/TRP'

#temp02
STA = '01input/STA'

#result03
result_IWV = '03results/IWV'

##medardtATM(metMEDARD, myMEDARD)
konverziaZTD_na_IWV(myGFS,ZTD_TRP,STA,result_IWV)
