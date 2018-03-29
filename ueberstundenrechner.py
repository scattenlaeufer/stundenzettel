#!/usr/bin/python2

import caldav
import datetime
import config

# urlaub: 20min / stunde und monat

week_hours = {}

for contract in config.contracts:
    start = datetime.datetime.strptime(contract[0], '%Y%m%d')
    start_week = start.strftime('%Y-%W')
    start_day_number = int(start.strftime('%w'))
    if start_day_number > 0 and start_day_number < 6:
        work_hours_first_week = contract[2] * (6 - float(start_day_number)) / 5
    else:
        work_hours_first_week = 0
    if start_week in week_hours.keys():
        week_hours[start_week] += work_hours_first_week
    else:
        week_hours[start_week] = work_hours_first_week
    end = datetime.datetime.strptime(contract[1], '%Y%m%d')
    end_week = end.strftime('%Y-%W')
    end_day_number = int(end.strftime('%w'))
    if end_day_number > 0 and end_day_number < 6:
        work_hours_last_week = contract[2] * float(end_day_number) / 5
    else:
        work_hours_last_week = contract[2]
    if end_week in week_hours.keys():
        week_hours[end_week] += work_hours_last_week
    else:
        week_hours[end_week] = work_hours_last_week
    if end.strftime('%Y') == start.strftime('%Y'):
        for week in range(int(start.strftime('%W'))+1, int(end.strftime('%W'))):
            week_hours[end.strftime('%Y')+'-'+'%02d'%(week,)] = contract[2]
    else:
        for year in range(int(start.strftime('%Y')), int(end.strftime('%Y'))+1):
            if year == int(start.strftime('%Y')):
                loop_start = int(start.strftime('%W')) + 1
                loop_end = 54
            elif year == int(end.strftime('%Y')):
                loop_start = 0
                loop_end = int(end.strftime('%W'))
            else:
                loop_start = 0
                loop_end = 54
            for week in range(loop_start, loop_end):
                week_hours[str(year)+'-'+'%02d'%(week)] = contract[2]

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
    if config.sick in categories or config.vacation in categories or config.free in categories:
        start = datetime.datetime.strptime(start_str, '%Y%m%d')
        end = datetime.datetime.strptime(end_str, '%Y%m%d')
        duration = end - start
        if duration.total_seconds() == 60 ** 2 * 24:
            week_number = start.strftime('%Y') + '-' + '%02d'%(int(start.strftime('%W')))
            week_hours[week_number] = week_hours[week_number] - week_hours[week_number] / 5.
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
    overtime = worktime - week_hours[week]
    total_overtime += overtime
    week_stat = (week, round(worktime, 2), round(overtime, 2))
    work_statistic.append(week_stat)
    print(week_stat)
overtime_h = int(total_overtime)
overtime_m = int((total_overtime-overtime_h)*60)
print('{}h {:0>2}\''.format(overtime_h, overtime_m))
