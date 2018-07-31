#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
import caldav
import datetime
import config
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# urlaub: 20min / stunde und monat

sys.setrecursionlimit(10000)

time_sheet_start = datetime.date(2018, 01, 01)
time_sheet_end = datetime.date.today()
# time_sheet_end = datetime.date(2018, 05, 31)

month_name = {
        1: 'Januar',
        2: 'Februar',
        3: 'März',
        4: 'April',
        5: 'Mai',
        6: 'Juni',
        7: 'Juli',
        8: 'August',
        9: 'September',
        10: 'Oktober',
        11: 'November',
        12: 'Dezember'}

week_hours = {}
time_sheet_dir = {}

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

def date_string(date):
    return '{}.{}.{}'.format(date[6:], date[4:6], date[:4])

contracts_table = '\\begin{tabular}{l|l|r}\n\tStart & Ende & Stunden\\\\\n\t\\hline\n\t\\hline\n\t'
contracts_str_list = []
for contract in config.contracts:
    contracts_str_list.append('{} & {} & {}'.format(date_string(contract[0]), date_string(contract[1]), contract[2]))

contracts_table += ' \\\\\n\t\\hline\n\t'.join(contracts_str_list) + '\n\\end{tabular}'

try:
    with open('events_pickle', 'r') as events_file:
        events = pickle.load(events_file)
except IOError:
    client = caldav.DAVClient(config.url)
    principal = client.principal()
    calendars = principal.calendars()

    calendar = None

    for cal in calendars:
        if config.calendar in str(cal):
            calendar = cal
            break

    events = calendar.events()
    # print(type(events))
    # with open('events_pickle', 'w') as events_file:
    #     pickle.dump(events, events_file)

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
            #if not week_number in week_hours.keys:
            #    week_hours[week_number] = 0
            week_hours[week_number] = week_hours[week_number] - week_hours[week_number] / 5.
        return start, end, categories
    if config.category in categories:
        start = datetime.datetime.strptime(start_str, '%Y%m%dT%H%M%S')
        end = datetime.datetime.strptime(end_str, '%Y%m%dT%H%M%S')
        return start, end, categories

hours = {}

for event in events:
    work_time = work_duration(event)
    if work_time:
        if config.category in work_time[2]:
            work_dur = work_time[1] - work_time[0]
            week =  work_time[0].strftime('%Y-%W')
            if week in hours.keys():
                hours[week] += work_dur
            else:
                hours[week] = work_dur
        if time_sheet_start <= work_time[0].date() and time_sheet_end >= work_time[1].date() and not config.free in work_time[2]:
            year = work_time[0].year
            month = work_time[0].month
            if not year in time_sheet_dir.keys():
                time_sheet_dir[year] = {}
            if not month in time_sheet_dir[year].keys():
                time_sheet_dir[year][month] = {}
            time_sheet_dir[year][month][work_time[0]] = {
                    'start': work_time[0],
                    'end': work_time[1],
                    'comment': work_time[2]}

time_sheet = '\\section{Arbeitszeit vom ' + time_sheet_start.strftime('%d.%m.%Y') + ' bis zum ' + time_sheet_end.strftime('%d.%m.%Y') + '}\n'
year_keys = time_sheet_dir.keys()
year_keys.sort()
total_work_time = 0.
for year_key in year_keys:
    time_sheet += '\\subsection{' + str(year_key) + '}\n'
    month_keys = time_sheet_dir[year_key].keys()
    month_keys.sort()
    for month_key in month_keys:
        time_sheet += '\\subsubsection{' + month_name[month_key] + '}\n'
        time_sheet += '\\begin{tabular}{c|l|l|c|l}\n\tKW & Start & Ende & Dauer [h] & Kommentar \\\\ \\hline \\hline \n'
        day_keys = time_sheet_dir[year_key][month_key].keys()
        day_keys.sort()
        for day_key in day_keys:
            start = time_sheet_dir[year_key][month_key][day_key]['start']
            end = time_sheet_dir[year_key][month_key][day_key]['end']
            comment = time_sheet_dir[year_key][month_key][day_key]['comment']
            duration = end - start
            time_sheet += '\t' + start.strftime('%W') + ' & '
            time_sheet += '\t' + start.strftime('%d.%m.%Y %H:%M') + ' & '
            time_sheet += end.strftime('%d.%m.%Y %H:%M') + ' & '
            time_sheet += '{0:.2f}'.format(duration.total_seconds()/3600) + ' & '
            if not config.category in comment:
                time_sheet += ', '.join(comment) + ' '
            else:
                total_work_time += duration.total_seconds()/3600
            time_sheet +='\\\\\n'
        time_sheet += '\\end{tabular}'

print('total work time: ' + str(total_work_time))
total_overtime = 0
overtime_list = []
week_list = []

weeks = hours.keys()
weeks.sort()

work_statistic = []

total_week_stat = 0.

for week in weeks:
    dur = hours[week]
    worktime = dur.total_seconds() / 3600
    overtime = worktime - week_hours[week]
    total_overtime += overtime
    week_stat = (week, round(worktime, 2), round(overtime, 2))
    work_statistic.append(week_stat)
    week_list.append(datetime.datetime.strptime(week+'-0', "%Y-%W-%w"))
    overtime_list.append(total_overtime)
    if '2018' in week:
        print(week_stat)
        total_week_stat += week_stat[1]
overtime_h = int(total_overtime)
overtime_m = int((total_overtime-overtime_h)*60)
# print('{}h {:0>2}\''.format(overtime_h, overtime_m))

print(total_week_stat)

for i, week in enumerate(week_list):
    if week.strftime('%Y') == '2018':
        print overtime_list[i-1]
        break

fig = plt.figure()
ax = fig.add_subplot(111)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%W'))
ax.plot_date(week_list, overtime_list, ls='-', marker='')
ax.set_title(u'Überstundenentwicklung')
ax.set_ylabel(u'Überstunden [h]')
ax.set_xlabel('Kalenderwoche')
ax.grid(True)
fig.autofmt_xdate(rotation=45)
fig.tight_layout()
plt.savefig('overtime_fig.eps', format='eps')

overtime_section = '\\section{Überstunden}\n'
overtime_section += 'Aktuelle Überstunden: ' + '{0:.2f}'.format(total_overtime) + '\n\n'
overtime_section += '\\includegraphics{overtime_fig}\n'

tex_file_header = "\\documentclass[paper=a4]{scrartcl}\n\\usepackage[margin=2.5cm]{geometry}\n\\usepackage{epsfig}\n\\begin{document}"
tex_file_title = '\n\n{\\center \\huge{\\textbf{Stundenzettel Björn Guth}}}'
tex_file_footer = "\n\\end{document}"

tex_file_str = tex_file_header
tex_file_str += tex_file_title
tex_file_str += '\n\n\\section{Verträge}\n'
tex_file_str += contracts_table + '\n'
tex_file_str += overtime_section + '\n'
tex_file_str += time_sheet + '\n'
tex_file_str += tex_file_footer
with open('time_sheet.tex', 'w+') as tex_file:
    tex_file.write(tex_file_str)
