from addFlows import createDirectFlow

# madrid - cordoba 
route1 = ("of:0000000000000001", "of:0000000000000009", "of:000000000000000a")

# madrid - malaga
route2 = ("of:0000000000000001", "of:0000000000000008")

# madrid - sevilla
route3 = ("of:0000000000000001", "of:0000000000000009")

createDirectFlow(route1)
createDirectFlow(route2)
createDirectFlow(route3)
