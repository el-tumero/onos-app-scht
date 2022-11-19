from mininet.topo import Topo
from mininet.link import TCLink
from math import sin, cos, sqrt, atan2, radians

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

def calculateDelay(city1:str, city2:str) -> str:
    distance = calculateDistance(city1, city2)
    return f"{ distance * sqrt(2) / 200000 * 1000}ms"


class SpanishCitiesTopo(Topo):

    def __init__(self, *args, **params):
        self.switchesCities = {}
        self.switchesCounter = 1
        super().__init__(*args, **params)

    def createHostsAndSwitches(self):
        for city in locations.keys():
            cityHost = self.addHost(city)
            citySwitch = self.addSwitch(f"s{self.switchesCounter}")
            self.addLink(cityHost, citySwitch)
            self.switchesCities[city] = citySwitch
            self.switchesCounter += 1

    def build(self):

        self.createHostsAndSwitches()

        madridS = self.switchesCities["madrid"]
        valladolidS = self.switchesCities["valladolid"]
        bilbaoS = self.switchesCities["bilbao"]
        barcelonaS = self.switchesCities["barcelona"]
        zaragozaS = self.switchesCities["zaragoza"]
        valenciaS = self.switchesCities["valencia"]
        murciaS = self.switchesCities["murcia"]
        malagaS = self.switchesCities["malaga"]
        sevillaS = self.switchesCities["sevilla"]
        cordobaS = self.switchesCities["cordoba"]

        #base
        self.addLink(madridS, sevillaS, cls=TCLink, bw=100, delay=calculateDelay("madrid", "sevilla"))
        self.addLink(madridS, valenciaS, cls=TCLink, bw=100, delay=calculateDelay("madrid", "valencia"))
        self.addLink(madridS, barcelonaS, cls=TCLink, bw=100, delay=calculateDelay("madrid", "barcelona"))
        self.addLink(madridS, bilbaoS, cls=TCLink, bw=100, delay=calculateDelay("madrid", "bilbao"))
        self.addLink(bilbaoS, valladolidS, cls=TCLink, bw=100, delay=calculateDelay("bilbao", "valladolid"))
        self.addLink(barcelonaS, zaragozaS, cls=TCLink, bw=100, delay=calculateDelay("barcelona", "zaragoza"))
        self.addLink(valenciaS, murciaS, cls=TCLink, bw=100, delay=calculateDelay("valencia", "murcia"))
        self.addLink(sevillaS, cordobaS, cls=TCLink, bw=100, delay=calculateDelay("sevilla", "cordoba"))
        self.addLink(sevillaS, malagaS, cls=TCLink, bw=100, delay=calculateDelay("sevilla", "malaga"))

        #orange
        self.addLink(madridS, malagaS, cls=TCLink, bw=100, delay=calculateDelay("madrid", "malaga"))
        self.addLink(malagaS, murciaS, cls=TCLink, bw=100, delay=calculateDelay("malaga", "murcia"))
        self.addLink(murciaS, madridS, cls=TCLink, bw=100, delay=calculateDelay("murcia", "madrid"))

        #blue
        self.addLink(madridS, valladolidS, cls=TCLink, bw=100, delay=calculateDelay("madrid", "valladolid"))
        self.addLink(bilbaoS, zaragozaS, cls=TCLink, bw=100, delay=calculateDelay("bilbao", "zaragoza"))
        self.addLink(barcelonaS, valenciaS, cls=TCLink, bw=100, delay=calculateDelay("barcelona", "valencia"))
        self.addLink(madridS, zaragozaS, cls=TCLink, bw=100, delay=calculateDelay("madrid", "zaragoza"))



        
topos = {"spaintopo": (lambda: SpanishCitiesTopo())}