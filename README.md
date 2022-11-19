# Sterownik do kontrolera ONOS

## Uzycie

### /flows/add (POST)

- Tworzy wszystkie przepływy, dzięki którym mozna połączyć hosta nr 1 z hostem nr 2 i rezerwuje dla połączenia określoną ilość pasma
- *body*:
    - ip1 - ip hosta nr 1
    - ip2 - ip hosta nr 2
    - load - załozona wielkosc strumienia danych
```json
{
    "ip1": "0.0.0.0",
    "ip2": "0.0.0.1",
    "load": 30
}
```

### /flows/delete (DELETE)
- usuwa wszyskie poprzednio utworzone przepływy



## Objaśnienie kodu

### app.py - aplikacja (REST API)

```python
onosUrl = "http://192.168.192.160:8181/onos/v1/"


def initializeGraph():
    with open("links.json") as file:
        links = json.load(file)
        g = Graph()
        for link in links:
            g.add_edge(link["from"], link["to"], link["delay"])
            g.add_edge(link["to"], link["from"], link["delay"])
        return g

def getSwitches():
    with open("hosts.json") as file:
        return dict([(value, key) for key, value in json.load(file).items()])

graph = initializeGraph()
switches = getSwitches()

linksLoad = {}
```

- onosUrl - url styku REST ONOS API
- initializeGraph() - tworzy graf i wypełnia go danymi o łączach z pliku links.json (w pliku tym znajdują się informacje o opóźnieniach na poszczególnych łączach) Graf ten stowrzony jest dzięki bibliotece Dijkstar https://pypi.org/project/Dijkstar/
- getSwitches() - pobiera dane pliku hosts.json zwraca słownik w którym klucz jest adresem ip hosta, a wartość to identyfikator switcha do niego podłączonego
- linksLoad - słownik przetrzymujący informacje na temat łączy - w jaki sposób są obciązone (przepływności)

```python
@post("/flows/add")
def flowsAdd():
    data = request.json

    nodes = find_path(graph, switches[data["ip1"] + "/32"], switches[data["ip2"] + "/32"]).nodes

    unavailableFlows:list[str] = []

    for i in range(len(nodes) - 1):
        if nodes[i]+nodes[i+1] in linksLoad:
            if data["load"] + linksLoad[nodes[i]+nodes[i+1]] > 100:
                unavailableFlows.append(nodes[i]+nodes[i+1])

    if len(unavailableFlows) == 0:
        for i in range(len(nodes) - 1):
            linksLoad[nodes[i]+nodes[i+1]] = linksLoad[nodes[i]+nodes[i+1]] + data["load"] if nodes[i]+nodes[i+1] in linksLoad else data["load"]
            linksLoad[nodes[i + 1]+nodes[i]] = linksLoad[nodes[i+1]+nodes[i]] + data["load"] if nodes[i+1]+nodes[i] in linksLoad else data["load"]

    

    if(len(unavailableFlows) > 0):

        altGraph = initializeGraph()
        
        for flow in unavailableFlows:
            args = (flow[0:19], flow[19:])
            altGraph.remove_edge(*args)
        
        nodes = find_path(altGraph, switches[data["ip1"] + "/32"], switches[data["ip2"]] + "/32").nodes

        for i in range(len(nodes) - 1):
            linksLoad[nodes[i]+nodes[i+1]] = linksLoad[nodes[i]+nodes[i+1]] + data["load"] if nodes[i]+nodes[i+1] in linksLoad else data["load"]
            linksLoad[nodes[i + 1]+nodes[i]] = linksLoad[nodes[i+1]+nodes[i]] + data["load"] if nodes[i+1]+nodes[i] in linksLoad else data["load"]

        createDirectFlow(tuple(nodes))
        return "Added!"

    createDirectFlow(tuple(nodes))
    return "Added!"
```

- flowsAdd()
    - na podstawie parametrów podanych wewnątrz BODY zapytania POST - tworzy przepływy umozliwiajace przesył strumienia danych między dwoma hostami, według algorytmu wyznaczania najkrótszej ściezki zwracjac uwagę na to czy któreś z łączy nie jest przeciązone, wtedy algorytm ustala trase na podstawie drugiej w kolejnosci najkrótszej sciezki

```python
@delete("/flows/delete")
def flowsDelete():
    r = requests.delete(onosUrl + "flows/application/org.onosproject.rest", auth=HTTPBasicAuth("onos","rocks"))
    return str(r.status_code)
```

- flowsDelete()
    - usuwa wszystkie przepływy stworzone przez aplikacje 


### addFlows.py - algorytm tworzenia przepływów

#### Inicjacja
```python
import requests
from requests.auth import HTTPBasicAuth
import json

onosUrl = "http://192.168.192.160:8181/onos/v1/"

def getTemplate():
    with open("flow.json") as file:
        return json.load(file)

def getHosts():
    with open("hosts.json") as file:
        return json.load(file)

def getLinks():
    r = requests.get(onosIp+"links", auth=HTTPBasicAuth("onos", "rocks"))
    return r.json()["links"]

template = getTemplate()

hosts = getHosts()

links = getLinks()

ports = {}
```

- Zainicjowanie niezbędnych elementów do poprawnego działania skryptu:
    - import bibliotek
    - onosUrl -  url styku REST ONOS API
    - ```getTemplate()``` zwraca wczytany z pliku "szablon" - przykładową zawartość BODY w zapytaniu POST pod punkt końcowy styku REST ONOS API /flows/{deviceId}
    - ```getHosts()``` zwraca wczytany z pliku słownik w którym klucz jest identyfikatorem switcha np. "of:0000000000000001" a wartością ip hosta do niego podłączonego np. "10.0.0.4/32"
    - ```getLinks()``` wysyła zapytanie GET do styku REST ONOS API pod punkt końcowy /links aby pobrać informacje na temat łączy - między jakimi switchami występują oraz które porty switchy są do nich podlączone lub który port na danym switchu jest podlączony do hosta

#### Przekształcanie danych o łączach

```python
def savePortsOfDevice(deviceId:str):
    for link in links:
        if link["src"]["device"] == deviceId:
            if deviceId not in ports:
                ports[deviceId] = {}

            # output of that device and input of second device
            ports[deviceId][link["dst"]["device"]] = {"output": link["src"]["port"], "input": link["dst"]["port"]}
```

- ```savePortsOfDevice()``` dla switcha o podanej nazwie identyfikacyjnej zostaje dodany nowy rekord do słownika ```ports```
- Przykładowy słownik ```ports```:

```python
    {
        "of:0000000000000001": {
            "of:0000000000000003": {
                "output": 3,
                "input": 4
            },
            "of:0000000000000002": {
                "output": 2,
                "input": 2
            },
        }
    }
```

Dane w tym słowniku mozna interpretowac w sposób następujący: ```"of:0000000000000001"``` jest podlączony do ```"of:0000000000000003"```, łącze jest podłączone do portu nr 3 switcha ```"of:0000000000000001"``` oraz do portu nr 4 switcha ```"of:0000000000000003"```. Do switcha ```"of:0000000000000001"``` podłączony jest równiez switch ```"of:0000000000000002"```, wartości pól "output" oraz "input" traktujemy w sposób analogiczny.

#### Tworzenie reguł przepływu

```python
def addFlow(deviceId:str, inputPort:str, outputPort:str, ipDest:str):
    template["deviceId"] = deviceId
    template["treatment"]["instructions"][0]["port"] = outputPort
    template["selector"]["criteria"][0]["port"] = inputPort
    template["selector"]["criteria"][2]["ip"] = ipDest

    r = requests.post(onosUrl + "flows/" + deviceId, json=template, auth=HTTPBasicAuth("onos", "rocks"))
```

- addFlow() - poprzednio utworzony szablon przetrzymywany w słowniku ```template``` jest wypełniany za pomocą argumentów ```deviceId```, ```inputPort```, ```outputPort``` oraz ```ipDest```. Wysyłane zostaje zapytanie POST do styku REST na punkt końcowy flows/{deviceId} z danymi wymaganymi do stworzenia przepływu wewnątrz BODY.

#### Tworzenie "trasy: przepływów na podstawie podanych identyfikatorów switchy

```python
def createDirectFlow(nodes:tuple(str)):

    device1 = nodes[0]
    device2 = nodes[-1]

    ip1 = hosts[device1]
    ip2 = hosts[device2]

    route = nodes[1:-1]

    savePortsOfDevice(device1)
    savePortsOfDevice(device2)

    if len(route) == 0:
        addFlow(device1, "1", ports[device1][device2]["output"], ip2)
        addFlow(device1, ports[device1][device2]["output"], "1", ip1)

        addFlow(device2, "1", ports[device2][device1]["output"], ip1)
        addFlow(device2, ports[device2][device1]["output"], "1", ip2)


    if len(route) > 0:

        firstStop = route[0]
        lastStop = route[len(route) - 1]

        addFlow(device1, "1", ports[device1][firstStop]["output"], ip2)
        addFlow(device1, ports[device1][firstStop]["output"], "1", ip1)

        addFlow(device2, "1", ports[device2][lastStop]["output"], ip1)
        addFlow(device2, ports[device2][lastStop]["output"], "1", ip2)

        for device in route:
            savePortsOfDevice(device)

        for i in range(len(route)):
            device = route[i]
            if device == firstStop and device == lastStop:
                addFlow(device, ports[device1][device]["input"], ports[device][device2]["output"], ip2)
                addFlow(device, ports[device2][device]["input"], ports[device][device1]["output"], ip1)
                break

            if device == firstStop:
                nextDevice = route[i+1]
                addFlow(device, ports[device1][device]["input"], ports[device][nextDevice]["output"], ip2)
                addFlow(device, ports[nextDevice][device]["input"], ports[device][device1]["output"], ip1)
            if device == lastStop:
                lastDevice = route[i-1]
                addFlow(device, ports[lastDevice][device]["input"], ports[device][device2]["output"], ip2)
                addFlow(device, ports[device2][device]["input"], ports[device][lastDevice]["output"], ip1)
```

- createDirectFlow() - argumentem jest krotka złozona z indentyfikatorów wszystkich switchy które zostaną wykorzystane przy tworzeniu przeływów, z czego pierwszy oraz ostatni switch (w krotce) są podłączone do hostów między którymi chcemy uzyskać przepływ danych.
    - (przykład) jeśli do ```"of:0000000000000001"``` jest podłączony host ```10.0.0.1```, a do ```"of:0000000000000002"``` host ```10.0.0.2``` i chcemy uzyskać mozliwosc przesyłu danych między nimi nalezy wywołać funkcję: ```createDirectFlow(("of:0000000000000001", ""of:0000000000000002"))```, jeśli na drodze tej występował by jeszcze switch ```"of:0000000000000003"``` to wywołalibyśmy funkcję ```createDirectFlow(("of:0000000000000001", "of:0000000000000003","of:0000000000000002"))```
    - funkcja korzysta ze wczesniej zaimplementowanych metod oraz parametrow
    - upraszcza w znaczny sposób definiowanie przepływów
    
### getDelays.py - wyznaczanie opóźnień na łączach

```python
def saveLinksDelay():
    switches = getSwitches()
    output = []
    for link in links:
        city1, city2 = link.split("-")
        output.append({
            "from": switches[city1],
            "to": switches[city2],
            "delay": calculateDelay(city1, city2)
        })
    with open("links.json", "w") as file:
        json.dump(output, file, indent=4)
```

- saveLinksDelay() - pobiera informacje o tym które switche są podłączone do których hostów, wylicza opóźnienie dla kazdego łącza wynikającego z prędkości propagacji przewodu światłowodowego. Zapisuje informacje o opóźnieniach dla kazdego łącza w pliku links.json()

## Autorzy
Łukasz Tumiński, Alicja Turzyńska

