import requests
from bs4 import BeautifulSoup
from json import dump
from pprint import pprint


def num(n: str):
    return float(n.replace(",", "").replace("%", ""))


def get_precinct_report(url: str):
    return


def get_canvass_report(url: str):
    req = requests.get(url)
    html = req.text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("font", attrs={"class", "h2"}).text
    time = soup.find("font", attrs={"class": "h4"}).text[21:]

    head = soup.find("div", attrs={"class": "gheader"}).find_all(
        "td", attrs={"align": "left"})

    registered_voters = num(head[1].text)
    ballots_cast = num(head[3].text)
    voter_turnout = num(head[5].text)
    total_precincts = num(head[7].text)
    full_count_precincts = num(head[9].text)
    full_count_precincts_percent = num(head[11].text)
    partial_count_precincts = num(head[15].text)

    table = soup.find_all("table")[1]
    precincts = table.find("tr", attrs={"class": "bb"})
    total = table.find("tr", attrs={"class": "bbeven"})

    _, total_yes, total_no = total.find_all("td")
    total_yes_num, _, total_yes_percent = total_yes.find("b").contents
    total_yes_num = num(total_yes_num)
    total_yes_percent = num(total_yes_percent)

    total_no_num, _, total_no_percent = total_no.find("b").contents
    total_no_num = num(total_no_num)
    total_no_percent = num(total_no_percent)

    print(
        registered_voters,
        ballots_cast,
        voter_turnout,
        total_precincts,
        full_count_precincts,
        full_count_precincts_percent,
        partial_count_precincts,
        total_yes_num,
        total_yes_percent,
        total_no_num,
        total_no_percent,
        sep="\n"
    )


def get_summary(index: int):
    return


def get_precincts_counted(precincts: list):
    return


def get_summary_row(row):
    row.pop(0)
    label = row[0]
    call = "bold" in label["class"]
    label: str = label.text.replace('\xa0', ' ').strip()
    precinct = num(row[1].text)
    absentee = num(row[2].text)
    total = num(row[3].text)
    percent = num(row[4].text)
    return {
        "label": label, 
        "call": call, 
        "in_precinct_votes": precinct, 
        "absentee_votes": absentee, 
        "total_votes": total, 
        "percent_votes": percent
    }


def get_data(baseurl: str, indices: list):
    req = requests.get(f"{baseurl}/index.jsp")
    html = req.text
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    summary = tables[2].find_all("tr")

    data = list()

    for index in indices:
        details = summary[index + 1]
        name = details.find(
            "td", attrs={"class": "headertr", "colspan": "3"}).text
        canvass_url = details.find(
            "td", attrs={"class": "headertr", "colspan": "2"}).find("a")["href"]
        canvass_url = f"{baseurl}/{canvass_url}"

        yes = get_summary_row(summary[index + 2].contents)
        no = get_summary_row(summary[index + 3].contents)


        data.append({
            "name": name,
            "canvass_url": canvass_url,
            "options": [yes, no]
        })
        print(name, canvass_url, yes, no, sep="\n")

    precincts_counted = tables[3]
    return data


def main():
    url = "https://electionresults.ewashtenaw.org/electionreporting/aug2021"
    data = get_data(url, [0])
    with open("data.json", "w") as f:
        dump(data, f, indent=2)


if __name__ == "__main__":
    main()
