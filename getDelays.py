from math import sin, radians, atan2, cos, sqrt
import json

locations = {
    "madrid": (40.416820, -3.703880),
    "valladolid": (41.651968, -4.724606),
    "bilbao": (43.262896, -2.935092),
    "barcelona": (41.38268, 2.17702),
    "zaragoza": (41.64760, -0.88577),
    "valencia": (39.16961, -0.373191),
    "murcia": (37.98300, -1.13028),
    "malaga": (36.71997, -4.41484),
    "sevilla": (37.38874, -5.99399),
    "cordoba": (37.88519, -4.77600)
}

links = [
    "madrid-sevilla",
    "madrid-valencia",
    "madrid-barcelona",
    "madrid-bilbao",
    "bilbao-valladolid",
    "barcelona-zaragoza",
    "valencia-murcia",
    "sevilla-cordoba",
    "sevilla-malaga",
    "madrid-malaga", #orange
    "malaga-murcia",
    "murcia-madrid",
    "madrid-valladolid", #blue
    "bilbao-zaragoza",
    "barcelona-valencia",
    "madrid-zaragoza"
]

def calculateDistance(city1:str, city2:str) -> float:

    coords1 = locations[city1]
    coords2 = locations[city2]

    R = 6373.0

    lat1 = radians(coords1[0])
    lon1 = radians(coords1[1])
    lat2 = radians(coords2[0])
    lon2 = radians(coords2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def calculateDelay(city1:str, city2:str) -> float:
    distance = calculateDistance(city1, city2)
    return distance * sqrt(2) / 200000 * 1000

def getSwitches():
    with open("switches.json") as file:
        return json.load(file)

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

saveLinksDelay()