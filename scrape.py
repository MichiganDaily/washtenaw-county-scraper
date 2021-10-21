import requests
from bs4 import BeautifulSoup
from json import dump


def num(n: str):
    return float(n.replace(",", "").replace("%", ""))


def get_canvass_report(url: str):
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    head = soup.find("div", attrs={"class": "gheader"}).find_all(
        "td", attrs={"align": "left"})

    table = soup.find_all("table")[1]

    precincts = table.find_all("tr")
    precincts.pop()
    precincts.pop(0)

    data = list()

    for precinct in precincts:
        datum = precinct.find_all("td")
        data.append({
            "Precinct": datum[0].text,
            "Yes": num(datum[1].text.strip()),
            "No": num(datum[2].text.strip())
        })

    return {
        "meta": {
            "title": soup.find("font", attrs={"class", "h2"}).text,
            "time": soup.find("font", attrs={"class": "h4"}).text[21:],
            "registered_voters": num(head[1].text),
            "ballots_cast": num(head[3].text),
            "voter_turnout": num(head[5].text),
            "total_precincts": num(head[7].text),
            "full_count_precincts": num(head[9].text),
            "full_count_precincts_percent": num(head[11].text),
            "partial_count_precincts": num(head[15].text)
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


def get_data(baseurl: str, indices: list):
    html = requests.get(f"{baseurl}/index.jsp").text
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    summary = tables[2].find_all("tr")

    print(len(summary))

    precincts_counted = tables[3]
    reported = dict()
    precincts = precincts_counted.find_all("tr")
    precincts.pop(0)
    for precinct in precincts:
        text = precinct.find("td").text.strip()
        pclass = precinct.find("td")["class"]
        if "red" in pclass:
            reported[text] = "not-counted"
        elif "blue" in pclass:
            reported[text] = "partially-counted"
        else:
            reported[text] = "fully-counted"

    data = list()

    for index in indices:
        details = summary[index * 3 + 1]
        name = details.find(
            "td", attrs={"class": "headertr", "colspan": "3"}).text
        canvass = details.find(
            "td", attrs={"class": "headertr", "colspan": "2"}).find("a")["href"]
        canvass = f"{baseurl}/{canvass}"

        yes = get_summary_row(summary[index * 3 + 2].contents)
        no = get_summary_row(summary[index * 3 + 3].contents)

        report = get_canvass_report(canvass)
        for i in range(len(report["data"])):
            report["data"][i]["counted"] = reported[report["data"][i]["Precinct"]]

        data.append({
            "name": name,
            "options": [yes, no],
            "report": report
        })

    return {
        "meta": {
            "title": soup.find("font", attrs={"class", "h2"}).text,
            "time": soup.find("font", attrs={"class": "h4"}).text[21:]
        },
        "data": data
    }


def main():
    url = "https://electionresults.ewashtenaw.org/electionreporting/nov2020"
    data = get_data(url, [325, 326, 327])
    with open("data.json", "w") as f:
        dump(data, f, indent=2)


if __name__ == "__main__":
    main()
