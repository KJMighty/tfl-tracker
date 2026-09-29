import requests

url = "https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line/Status"
r = requests.get(url, timeout=10)
r.raise_for_status()
lines = r.json()

print(len(lines))
print(lines[0])

for line in lines:
    if len(line["lineStatuses"]) > 1:
        print(line["name"], len(line["lineStatuses"]))

for line in lines:
    for status in line["lineStatuses"]:
        if status["statusSeverity"] != 10:
            print(line["name"], status["statusSeverity"], status["statusSeverityDescription"], status.get("reason"))