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

def is_good_service(line):
    return all(status["statusSeverity"] == 10 for status in line["lineStatuses"])

def status_summary(line):
    return "; ".join(s["statusSeverityDescription"] for s in line["lineStatuses"])

for line in lines:
    print(line["name"], is_good_service(line), status_summary(line))

def parse(line):
    return {
        "line_id": line["id"],
        "line_name": line["name"],
        "mode": line["modeName"],
        "is_good": is_good_service(line),
        "status_description": status_summary(line),
    }

print(parse(lines[0]))
for line in lines:
    if line["name"] in ("Metropolitan", "Victoria"):
        print(parse(line))