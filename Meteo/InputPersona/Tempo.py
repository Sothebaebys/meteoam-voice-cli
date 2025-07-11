import requests
from datetime import datetime
import difflib
import pyttsx3
from geopy.distance import distance

engine = pyttsx3.init()
engine.setProperty('rate',165)

urlMeteoAM="https://www.meteoam.it/it/meteo-citta/"

#region FUNZIONI

def CoordMixd(lat,long,margine=0.357):
    return (f"{float(long)-margine},{float(lat)-margine},{float(long)+margine},{float(lat)+margine}")

def DirezioneVento(direzione):
    DictDirezioni= {
        "N-NE":"nord, nord est",
        "N-NW":"nord, nord ovest",
        "S-SE":"sud, sud est",
        "S-SW":"sud, sud ovest",
        "W-SW":"ovest, sud ovest",
        "W-NW":"ovest, nord ovest",
        "E-NE":"est, nord est",
        "E-SE":"est, sud est",
        "N" : "nord",
        "NW": "nord ovest",
        "NE": "nord est",
        "W" : "ovest",
        "E" : "est",
        "S" : "sud",
        "SW": "sud ovest",
        "SE": "sud est"
    } 
    if str(direzione) in DictDirezioni.keys():
        return DictDirezioni[str(direzione)]
    else :
        print ("Nessuna corrispondenza trovata")
        return 

def OraURL():
    oralocale = datetime.now().strftime("%Y-%m-%dT%H:")
    oralocale = (f"{oralocale}00:00.000")
    return oralocale

def RequestMeteoAM(URL,DataOra,CoordinateFormattate):

    params = {"service": "OWS" ,
      "request" : "GetForecast",
      "layers"  : "point_fcs",
      "format"  : "application/json",
      "version" : "1.1.1",
      "time"    : (DataOra+"Z"),
      "srs"     : "EPSG:4326",
      "bbox"    : CoordinateFormattate,
      "zoom"    : "11"
      }

    headers= { "Accept"          : "application/json",""
               "accept-encoding" : "gzip, deflate, br, zstd",
               "user-agent"      : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            }
    response = requests.get(url=URL,params=params,headers=headers)
    dati = response.json()
    if dati:
        return dati
    else:
        print("Nessuna corrispondenza.")
        return

def CoordinateLocalita(inputCitta):

    urlCoordinate = "https://nominatim.openstreetmap.org/search"
    
    inputCitta.lower()

    params = {"q": inputCitta,"polygon_geojson": 1,"format": "jsonv2"}

    headers = {"User-Agent" : ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/136.0.0.0 Safari/537.36"
                "(MyCoordsBot/1.0; contact: mail@******.***)"
                )
            }

    response = requests.get(url=urlCoordinate,params=params,headers=headers)  
    dati = response.json()
    if dati:
        for result in dati:
            if result.get('addresstype') in ['city','town','village']:
                lon = result['lon']
                lat = result['lat']
                print (f"Trovata una corrispondenza per {inputCitta} di tipo {result['addresstype']} : {result['display_name']}")
                return lat,lon
        print ( "Nessun risultato di tipo città trovato, potrebbe essere impreciso")
        result = dati[0]
        lat = result['lat']
        lon = result['lon']
        return  lat,lon
    else:
        print("Nessun risultato trovato.")
        return None

def ConfrontoStringheCittà (strInput,strJson):
    '''
        args:
            inserire le stringhe da comparare e ritorna una boleana dove True corrisponde alla nostra città altrimenti nessun risultato
            Solo nel caso in cui ci sia una corrispondenza superiore al 65%
    '''
    corrispondenza = difflib.get_close_matches(strInput.lower(),[strJson.lower()],n=1, cutoff=0.65)
    if len(corrispondenza)>0:
        return True
    else:
        return False

def RicercaCoordinateJson(coordinate,jsonFeatures):
    puntoPiùVicino = None
    distanzaMin = float('inf')
    for feature in jsonFeatures:
        coords = feature["geometry"]["coordinates"]
        if coords:
            punto = (coords[1],coords[0])
            
            dist = distance(coordinate,punto).km

            if dist < distanzaMin:
                distanzaMin=dist
                puntoPiùVicino= feature

    return puntoPiùVicino

def RicercaCurrentNameJson(jsonFeatures,inputCittà):
    for feature in jsonFeatures:
        NomeCittà = feature["properties"]["cn"]
        if ConfrontoStringheCittà(inputCittà,NomeCittà):
            DatiCittà = feature["properties"]
            return DatiCittà
    return None

def ConversioneJSON (Json,inputCittà,lat,lon):
    frase=""
    if not Json["features"]:
        frase = ("Non ho trovato corrispondenze. Mi dispiace")
        print (frase)
    else:
        features= Json["features"]
        if len(features) >1:
            DatiCittà=RicercaCurrentNameJson(features,inputCittà)
            if DatiCittà is None:
                coordinate = lat,lon
                DistanzaMin=RicercaCoordinateJson(coordinate,features)
                DatiCittà=DistanzaMin["properties"]
                frase= ("La località da te scelta non è disponibile. Procedo con la località più vicina disponibile..\n")
        else:
            DatiCittà = Json["features"][0]["properties"]
        if DatiCittà:
            iconaMeteo = DatiCittà["ICON"]
            temperaturaMin = DatiCittà["TMIN"]
            temperaturaMax = DatiCittà["TMAX"]
            temperaturaPercepita = DatiCittà["T2MC"]
            umiditàRelativa = DatiCittà["RH"]
            direzioneDelVento = DatiCittà["WDC"]
            velocitàDelVento = DatiCittà["WSKTS"]
            nomeLocalità = DatiCittà["cn"]

            icon=Icone(iconaMeteo)
            vento=DirezioneVento(direzioneDelVento)
            frase += (f"Secondo il meteo dell'aeronautica militare, a {nomeLocalità}. per ora si prevede:\n- {icon}\n- Temperature che oscillano tra: {temperaturaMin} e {temperaturaMax} gradi, con temperature percepite di {temperaturaPercepita} gradi centigradi.\n- Umidità al {umiditàRelativa}%.\n- Venti di {velocitàDelVento} kilometri orari in direzione {vento}.")
            print((f"Secondo meteoam le previsioni per {nomeLocalità} ad ora per oggi prevedono:\n- {icon}\n- Temperature che oscillano tra {temperaturaMin}° e {temperaturaMax}°, con temperature percepite di {temperaturaPercepita}.\n- Umidità al {umiditàRelativa}%.\n- Venti di {velocitàDelVento} kmh in direzione {direzioneDelVento}"))
    engine.say(frase)
    engine.runAndWait()

def Icone (strIcona):
    DictIcon= { "01":  "Sereno con cielo terso.",
            "02" :  "Parzialmente velato con nubi alte e molto sottili.", 
            "03" :  "Velato con nubi traslucide che coprono totalmente il cielo.",
            "04" :  "Poco nuvoloso con nubi medie e basse che coprono una porzione limitata del cielo.",
            "05" :  "Molto nuvoloso con nubi medie e basse che coprono quasi totalmente il cielo.",
            "07" :  "Cielo coperto interamente dalle nubi.",
            "08" :  "Deboli rovesci di pioggia.",
            "09" :  "Forti rovesci di pioggia.",
            "10" :  "Temporali con presenza contestuale di precipitazioni, tuoni e fulmini.",
            "11" :  "Precipitazioni che gelano al contatto col suolo creando ghiacciate sparse.",
            "16" :  "Precipitazioni solide in fiocchi di neve.",
            "31" :  "Serata serena con cielo stellato."
    } 
    if str(strIcona) in DictIcon.keys():
        return DictIcon[str(strIcona)]
    else :
        print ("Nessuna corrispondenza trovata")
        return 

def Avvio():
    
    global urlMeteoAM
    
    oraURL = OraURL()
    print ("Benevuto!")
    while True:
        inputCitta=input("Scrivi la città di riferimento:\n-")

        coordinate = CoordinateLocalita(inputCitta)

        #Se troviamo delle coordinate le impostiamo per la ricerca
        if coordinate:
            latitudine= coordinate[0]
            longitudine = coordinate[1]
            coordinateFormattate=CoordMixd(latitudine,longitudine)

            URL_API_Meteoam=(f"https://api.meteoam.it/deda-ows/ows?service=OWS&request=GetForecast&layers=point_fcs&styles=&format=application/json&version=1.1.1&time={oraURL}Z&srs=EPSG:4326&bbox={coordinateFormattate}&zoom=11")
            
            datiRichiesta=RequestMeteoAM(URL_API_Meteoam,oraURL,coordinateFormattate)
            ConversioneJSON(datiRichiesta,inputCitta,latitudine,longitudine)
            ContinuaEsci = input("Premi iun tasto per continuare, altrimenti 'E' per uscire:\n")
            if ContinuaEsci=="E" or ContinuaEsci=="e":
                print("A presto!")
                return False
        else:
            print("Non sono state trovate le coordinate per la località selezionata magari per un refuso, ritenta oppure inserisci una nuova località")
            continue

#endregion


if __name__ == "__main__":

    Avvio()
