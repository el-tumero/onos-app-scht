# Commands

## Add
```bash
curl -X POST "http://localhost:8000/flows/add" -d '{"ip1": "10.0.0.4", "ip2": "10.0.0.3", "load": 50}' -H "Content-Type: application/json" -H "Accept: application/json"
```

## Delete
```bash
curl -X DELETE "http://localhost:8000/flows/delete"
```