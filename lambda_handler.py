from json import dump, dumps
from datetime import datetime
from zoneinfo import ZoneInfo
from os import environ

import requests
from bs4 import BeautifulSoup
from boto3 import client


def num(n: str):
    return float(n.replace(",", "").replace("%", ""))


def get_canvass_report(url: str, time: str):
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    head = soup.find("div", attrs={"class": "gheader"}).find_all(
        "td", attrs={"align": "left"})

    table = soup.find_all("table")[1]

    precincts = table.find_all("tr")
    precincts.pop()
    headers = precincts.pop(0).text.split("\n")[2:-1]

    data = list()

    total_precincts = 0.0

    for precinct in precincts:
        datum = precinct.find_all("td")
        total_precincts += 2 if "&" in datum[0].text else 1
        item = {
            "Precinct": datum[0].text,
        }

        j = 0
        for header in headers:
            h = header
            if (header.find("(") != -1):
                h = header[:header.find("(")]
            item[h] = num(datum[j + 1].text.strip())
            j+= 1
        data.append(item)

    return {
        "meta": {
            "title": soup.find("font", attrs={"class", "h2"}).text,
            # "time": soup.find("font", attrs={"class": "h4"}).text[21:],
            "time": time,
            "registered_voters": num(head[1].text),
            "ballots_cast": num(head[3].text),
            "voter_turnout": num(head[5].text),
            "total_precincts": total_precincts,
            # "total_precincts": num(head[7].text),
            # "full_count_precincts": num(head[9].text),
            # "full_count_precincts_percent": num(head[11].text),
            # "partial_count_precincts": num(head[15].text)
        },
        "data": data
    }


def get_summary_row(row):
    label = row[1]
    return {
        "label": label.text.replace('\xa0', ' ').strip(),
        "call": "bold" in label["class"],
        "in_precinct_votes": num(row[2].text),
        "absentee_votes": num(row[3].text),
        "total_votes": num(row[4].text),
        "percent_votes": num(row[5].text)
    }


def get_data(baseurl: str, time: str, races):
    NOT_COUNTED = "not-counted"
    PARTIALLY_COUNTED = "partially-counted"
    FULLY_COUNTED = "fully-counted"

    html = requests.get(f"{baseurl}/index.jsp").text
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")

    precincts_counted = tables[3]
    reported = dict()
    precincts = precincts_counted.find_all("tr")
    precincts.pop(0)

    for precinct in precincts:
        text = precinct.find("td").text.strip()
        pclass = precinct.find("td")["class"]
        font = precinct.find("td").find("font")
        if not font is None:
            pclass = font["color"]
        if "red" in pclass:
            reported[text] = NOT_COUNTED
        elif "blue" in pclass:
            reported[text] = PARTIALLY_COUNTED
        else:
            reported[text] = FULLY_COUNTED

    data = list()

    summary = tables[2].find_all("tr")
    summary.pop(0)

    item = {
      "name": "",
      "options": [],
      "report": None
    }

    skip = False

    index = 0
    while index < len(summary):
        details = summary[index]
        name = details.find("td", attrs={"class": "headertr", "colspan": "3"})
        canvass = details.find(
            "td", attrs={"class": "headertr", "colspan": "2"})
        if name and canvass:
            if len(item["name"]) > 0:
                if len(data) == 0:
                    data.append({k: v for k, v in item.items()})
                elif (len(data) > 0 and item["name"] != data[-1]["name"]):
                    data.append({k: v for k, v in item.items()})
            name = name.text

            if name in races:
                skip = False
                canvass = f"{baseurl}/{canvass.find('a')['href']}"
                report = get_canvass_report(canvass, time)

                item = {
                  "name": name,
                  "options": [],
                  "report": report
                }

                full_count_precincts: float = 0.0
                partial_count_precincts: float = 0.0

                for i in range(len(report["data"])):
                    count = reported[report["data"][i]["Precinct"]]
                    report["data"][i]["counted"] = count
                if count == FULLY_COUNTED:
                    full_count_precincts += 1
                elif count == PARTIALLY_COUNTED:
                    partial_count_precincts += 1

                report["meta"]["full_count_precincts"] = full_count_precincts
                report["meta"]["full_count_precincts_percent"] = full_count_precincts / \
                report["meta"]["total_precincts"] * 100
                report["meta"]["partial_count_precincts"] = partial_count_precincts
            else:
                skip = True
        elif not skip:
            item["options"].append(get_summary_row(summary[index].contents))
        index+=1
    return {
        "meta": {
            "title": soup.find("font", attrs={"class", "h2"}).text,
            "time": time
        },
        "data": data
    }


def lambda_handler(event, context):
    east = ZoneInfo("America/New_York")
    time = datetime.now(tz=east).strftime("%A, %b %d, %Y %I:%M:%S %p")
    url = "https://electionresults.ewashtenaw.org/electionreporting/nov2022"

    races = [
        "Governor and Lieutenant Governor",
        "State Proposal 22-1",
        "State Proposal 22-2",
        "State Proposal 22-3",
        "Ann Arbor Mayor",
        "City of Ann Arbor Proposal 1"
    ]

    data = get_data(url, time, races)

    if environ["ENVIRONMENT"] == "local":
        with open("data.json", "w") as f:
            dump(data, f, indent=2)
    elif environ["ENVIRONMENT"] == "production":
        s3 = client("s3")
        s3.put_object(
            Bucket=environ["BUCKET"],
            Key=environ["KEY"], Body=dumps(data),
            ContentType="application/json",
            ACL='public-read', CacheControl='max-age=300'
        )
