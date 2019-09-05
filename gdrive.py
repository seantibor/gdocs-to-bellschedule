from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
from bs4 import BeautifulSoup
from bell_schedule import BellSchedule, Period
import pandas as pd
from dateutil import tz, parser
import datetime as dt
import requests
import click

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
timezone = tz.gettz("US/Eastern")

url = "https://docs.google.com/document/d/1fgqkw8NBPCSManhffpcNCqfdMcMPY5ZezRxQKxc5Weg/edit"
post_url = ""


def get_id_from_url(url):
    import urllib

    path = urllib.parse.urlparse(url).path
    return path.split("/")[3]


def extract_schedule(url):
    id = get_id_from_url(url)
    downloaded = drive.CreateFile({"id": id})
    title = downloaded["title"].strip()
    content = downloaded.GetContentString("text/html")
    soup = BeautifulSoup(content, "lxml")  # Parse the HTML as a string
    table = soup.find_all("table")[0]  # Grab the first table
    data_table = []
    for row in table.find_all("tr"):
        data_table.append(
            [column.find_all("span")[0].get_text() for column in row.find_all("td")]
        )

    return title, data_table


def period_table_to_schedule(
    title, schedule, schedule_date=dt.datetime.today(), header_row=True
):
    bs = BellSchedule(title, schedule_date=schedule_date, timezone=timezone)
    assumed_hour_for_am_pm = 7
    if header_row:
        schedule = schedule[1:]
    for name, start, end in schedule:
        if start == "":
            start = end
        if int(start.split(":")[0]) >= assumed_hour_for_am_pm:
            start += " AM"
        else:
            start += " PM"
        if int(end.split(":")[0]) >= assumed_hour_for_am_pm:
            end += " AM"
        else:
            end += " PM"
        start_time = parser.parse(start, default=schedule_date)
        end_time = parser.parse(end, default=schedule_date)
        bs.add_period(period_name=name, start_time=start_time, end_time=end_time)
    return bs


@click.command()
@click.argument('date', type=click.DateTime(formats=['%Y-%m-%d']))
@click.argument('url', type=click.STRING)
def add_schedule_from_url(date: str, url: str):
    try:
        date = date.replace(tzinfo=timezone)
    except ValueError:
        click.echo("Could not parse date. Please re-enter in YYYY-MM-DD format")
    click.echo("Extracting Schedule from Google Doc")
    title, schedule = extract_schedule(url)
    click.echo(f"Found schedule {title} in Google Doc")
    sched = period_table_to_schedule(title, schedule, schedule_date=date)
    click.echo(f"Uploading schedule for {date.strftime('%Y-%m-%d')}")
    post_url = f"https://pcbellschedule.azurewebsites.net/api/ftl/middleschool/schedule/{date.strftime('%Y-%m-%d')}"
    headers = {"content-type": "application/json", "x-functions-key": "7KqIaSZv2LuOp/pxkll13Eth0BG2zwHAVI9wDo1iD1AfJG4EWnOGTA=="}
    r = requests.post(
        url=post_url, data=sched.to_json(), headers=headers
    )
    if r.ok:
        click.echo(f"{title} schedule posted for date {date.strftime('%Y-%m-%d')}")
    else:
        click.echo(f"{title} schedule not posted correctly.")
