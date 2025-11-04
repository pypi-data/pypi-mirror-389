# Pract 2a - Removing Leading & Trailing Spaces
print("Chirag:255605")

data = "   Data Science !!!   "
print('>', data, '<')
cleandata = data.strip()
print('>', cleandata, '<')

# Pract 2b - Removing Non-Printable String
print("Chirag:255605")

import string
data = "Data\x00Science and\x02 ML is \x10fun!!!"
clean = ''.join(filter(lambda x: x in string.printable, data))
print(clean)

# Pract 2c - Formatting Date
print("Chirag:255605")

import datetime as dt
date = dt.date(2025, 7, 2)
date = format(date, '%Y-%m-%d')
print(date)

fdate = dt.datetime.strptime(date, '%Y-%m-%d')
fdate = format(fdate, '%d %B %Y')
print(fdate)
