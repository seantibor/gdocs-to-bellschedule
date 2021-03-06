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

url = "https://docs.google.com/document/d/1fgqkw8NBPCSManhffpcNCqfdMcMPY5ZezRxQKxc5Weg/edit"
post_url = ""
DEFAULT_TIMEZONE="America/New_York"

def get_id_from_url(url):
    import urllib

    path = urllib.parse.urlparse(url).path
    return path.split("/")[3]


def extract_schedule(url):
    schedule_id = get_id_from_url(url)
    downloaded = drive.CreateFile({"id": schedule_id})
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
    title, schedule, schedule_date=dt.datetime.today(), header_row=True, tzname=DEFAULT_TIMEZONE
):
    bs = BellSchedule(title, schedule_date=schedule_date, tzname=tzname)
    assumed_hour_for_am_pm = 7
    if header_row:
        schedule = schedule[1:]
    for name, start, end in schedule:
        if start == "":
            start = end
        start_hour = int(start.split(":")[0])
        end_hour = int(end.split(":")[0])
        if start_hour != 12 and start_hour >= assumed_hour_for_am_pm:
            start += " AM"
        else:
            start += " PM"
        if end_hour != 12 and end_hour >= assumed_hour_for_am_pm:
            end += " AM"
        else:
            end += " PM"
        start_time = parser.parse(start, default=schedule_date)
        end_time = parser.parse(end, default=schedule_date)
        print(f"Added period {name}: {start_time} to {end_time}")
        bs.add_period(period_name=name, start_time=start_time, end_time=end_time)
    return bs


@click.command()
@click.option('--campus', type=click.Choice(['ftl','boca']), prompt=True)
@click.option('--division', type=click.Choice(['middleschool','upperschool']), prompt=True)
@click.argument('date', type=click.DateTime(formats=['%Y-%m-%d']))
@click.argument('url', type=click.STRING)
@click.option('--tzname', type=click.STRING, help="The schedule timezone (if not the same as your local time)", default=DEFAULT_TIMEZONE)
@click.option('--showcsv', is_flag=True)
def add(date: dt.datetime, url: str, campus: str, division: str, tzname: str=DEFAULT_TIMEZONE, showcsv: bool=False):
    timezone = tz.gettz(tzname)
    date = date.replace(tzinfo=timezone)
    click.echo("Extracting Schedule from Google Doc")
    title, schedule = extract_schedule(url)
    click.echo(f"Found schedule {title} in Google Doc")
    sched = period_table_to_schedule(title, schedule, schedule_date=date, tzname=tzname)
    sched.campus = campus
    sched.division = division
    click.echo(f"Uploading schedule for {date.strftime('%Y-%m-%d')}")
    post_url = f"http://pcbellschedule.azurewebsites.net/api/{campus}/{division}/schedule/{date.strftime('%Y-%m-%d')}"
    headers = {"content-type": "application/json", "x-functions-key": "7KqIaSZv2LuOp/pxkll13Eth0BG2zwHAVI9wDo1iD1AfJG4EWnOGTA=="}
    r = requests.post(
        url=post_url, data=sched.to_json(), headers=headers
    )
    if r.ok:
        click.echo(f"{title} schedule posted for date {date.strftime('%Y-%m-%d')}")
    else:
        click.echo(f"{title} schedule not posted correctly.")
        click.echo(f"Error code {r.status_code}: {r.text}")

    if showcsv:
        filename = f"{campus}_{division}.csv"
        click.echo(f"Writing csv schedule to {filename}")
        sched.to_csv(filename)

@click.command()
@click.option('--campus', type=click.Choice(['ftl','boca']), prompt=True)
@click.option('--division', type=click.Choice(['middleschool','upperschool']), prompt=True)
@click.argument('date', type=click.DateTime(formats=['%Y-%m-%d']))
@click.argument('title', type=click.STRING)
@click.option('--tzname', type=click.STRING, help="The schedule timezone (if not the same as your local time)", default=DEFAULT_TIMEZONE)
def noschool(date: dt.datetime, campus: str, division: str, title:str, tzname: str=DEFAULT_TIMEZONE):
    timezone = tz.gettz(tzname)
    date = date.replace(tzinfo=timezone)
    click.echo(f"Setting {date.strftime('%B %d %Y')} to No School for {title}")
    sched = BellSchedule(name=f"No Classes - {title}", tzname=tzname, \
                         schedule_date=date, campus=campus, division=division)
    
    click.echo(f"Uploading schedule for {date.strftime('%Y-%m-%d')}")
    post_url = f"http://pcbellschedule.azurewebsites.net/api/{campus}/{division}/schedule/{date.strftime('%Y-%m-%d')}"
    headers = {"content-type": "application/json", "x-functions-key": "7KqIaSZv2LuOp/pxkll13Eth0BG2zwHAVI9wDo1iD1AfJG4EWnOGTA=="}
    r = requests.post(
        url=post_url, data=sched.to_json(), headers=headers
    )
    if r.ok:
        click.echo(f"{title} schedule posted for date {date.strftime('%Y-%m-%d')}")
    else:
        click.echo(f"{title} schedule not posted correctly.")
        click.echo(f"Error code {r.status_code}: {r.text}")

@click.group()
def cli():
    pass


cli.add_command(noschool)
cli.add_command(add)
