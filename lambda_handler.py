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
    headers = precincts.pop(0).text.split("\n")[2:-3]

    data = list()

    total_precincts = 0.0

    for precinct in precincts:
        datum = precinct.find_all("td")
        total_precincts += 2 if "&" in datum[0].text else 1
        item = {
            "Precinct": datum[0].text,
            # "Yes": num(datum[1].text.strip()),
            # "No": num(datum[2].text.strip())
        }

        j = 0
        for header in headers:
            item[header] = num(datum[j + 1].text.strip())
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


def get_data(baseurl: str, time: str, indices: list):
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

            if name.startswith("Ann Arbor Mayor") or name.startswith("Ann Arbor Council") or name == "AAATA Proposal":
                # print(data[-1]["name"], "not skipping")
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
    url = "https://electionresults.ewashtenaw.org/electionreporting/aug2022"
    data = get_data(url, time, [1,5,13,17,22,28,32,36,41,45,49,54,59,68,72,76,80,84,89,94,99,103,108,112,116,121,125,129,133,137,141,147,151,156,160,164,168,172,176,180,184,189,192,197,200,206,209,214,217,223,226,231,234,237,241,244,248,252,256,261,264,267,271,277,281,284,287,291,295,299,302,309,312,315,318,321,324,327,330,333,336,339,342,345,348,351,354,358,361,364,367,370,373,376,379,383,386,389,392,399,404,407,412,415,418,422,426,429,432,435,438,443,446,453,456,459,463,468,471,474,480,483,486,489,492,495,498,501,505,509,513,517,521,525,528,535,538,544,547,550,555,558,561,564,567,570,573,576,579,582,585,589,593,599,602,606,609,612,616,619,622,625,628,631,634,637,641,644,647,650,656,660,664,668,672,675,678,681,684,690,694,697,700,703,706,709,712,716,724,727,732,735,738,741,744,747,750,753,756,759,762,765,769,773,778,781,786,789,792,797,801,805,810,814,817,822,825,828,832,835,838,841,844,847,850,854,858,863,872,875,879,883,887,890,894,897,902,905,911,914,921,924,932,935,938,942,949,952,962,965,971,975,983,986,990,993,999,1002,1011,1014,1020,1023,1027,1034,1039,1043,1057,1061,1067,1071,1075,1078,1082,1087,1092,1095,1099,1102,1106,1111,1117,1121,1124,1127,1132,1136,1139,1142,1146,1152,1157,1162,1170,1173,1176,1179,1189,1192,1200,1203,1208,1211,1214,1217,1220,1223,1229,1232,1236,1240,1245,1248,1254,1258,1261,1266,1272,1275,1278,1282,1290,1294,1300,1304,1310,1313,1316,1319,1322,1325,1332,1335,1345,1348,1352,1356,1361,1364,1368,1371,1380,1383,1387,1391,1394,1397,1400,1403,1406,1410,1413,1417,1420,1424,1429,1434,1437,1440,1443,1446,1451,1457,1461,1465,1468,1473,1476,1480,1483,1486,1489,1492,1496,1501,1510,1513,1518,1523,1526,1529,1534,1539])

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
