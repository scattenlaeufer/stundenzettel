#!/usr/bin/python2

import caldav
import datetime
import config

week_hours = {}

print(config.contracts)

print(week_hours)
exit()

client = caldav.DAVClient(config.url)
principal = client.principal()
calendars = principal.calendars()

calendar = None

for cal in calendars:
    if config.calendar in str(cal):
        calendar = cal
        break

events = calendar.events()

def work_duration(event):
    data = event._data.split('BEGIN:VEVENT')[1].split('END:VEVENT')[0]
    vevent = data.split('\n')
    categories = []
    start_str = ''
    end_str = ''
    for line in vevent:
        if 'CATEGORIES:' in line:
            categories.append(line.split(':')[1])
        elif 'DTSTART' in line:
            start_str = line.split(':')[1]
        elif 'DTEND' in line:
            end_str = line.split(':')[1]
    if config.category in categories:
        start = datetime.datetime.strptime(start_str, '%Y%m%dT%H%M%S')
        end = datetime.datetime.strptime(end_str, '%Y%m%dT%H%M%S')
        return start, end

hours = {}

for event in events:
    work_time = work_duration(event)
    if work_time:
        work_dur = work_time[1] - work_time[0]
        week =  work_time[0].strftime('%Y-%W')
        if week in hours.keys():
            hours[week] += work_dur
        else:
            hours[week] = work_dur

total_overtime = 0

weeks = hours.keys()
weeks.sort()

work_statistic = []

for week in weeks:
    dur = hours[week]
    worktime = dur.total_seconds() / 3600
    overtime = worktime - 19
    total_overtime += overtime
    week_stat = (week, worktime, overtime)
    work_statistic.append(week_stat)
    print(week_stat)
print(total_overtime)
