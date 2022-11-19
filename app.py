import json
from bottle import delete, post, run, request
import requests
from requests.auth import HTTPBasicAuth
from dijkstar import Graph, find_path

from addFlows import createDirectFlow


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
        
        nodes = find_path(altGraph, switches[data["ip1"] + "/32"], switches[data["ip2"] + "/32"]).nodes

        for i in range(len(nodes) - 1):
            linksLoad[nodes[i]+nodes[i+1]] = linksLoad[nodes[i]+nodes[i+1]] + data["load"] if nodes[i]+nodes[i+1] in linksLoad else data["load"]
            linksLoad[nodes[i + 1]+nodes[i]] = linksLoad[nodes[i+1]+nodes[i]] + data["load"] if nodes[i+1]+nodes[i] in linksLoad else data["load"]

        createDirectFlow(tuple(nodes))
        return "Added! " + str(tuple(nodes))

    createDirectFlow(tuple(nodes))
    return "Added!" + str(tuple(nodes))


@delete("/flows/delete")
def flowsDelete():
    r = requests.delete(onosUrl + "flows/application/org.onosproject.rest", auth=HTTPBasicAuth("onos","rocks"))
    linksLoad = {}
    return str(r.status_code)


run(host="localhost", port=8000)