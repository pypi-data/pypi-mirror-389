
# Utility start CSV TO HORUS
import pandas as pd

inputfile = r""
inputData = pd.read_csv(inputfile, encoding='latin-1')
print("Input Data ============================")
print(inputData)
print("=======================================")

# processing
ProcessData = inputData.copy()
ProcessData.drop('ISO-2-CODE', axis=1, inplace=True)
ProcessData.drop('ISO-3-Code', axis=1, inplace=True)
ProcessData.rename(columns={'Country': 'CountryName'}, inplace=True)
ProcessData.rename(columns={'ISO-M49': 'CountryNumber'}, inplace=True)
ProcessData.set_index('CountryNumber', inplace=True)
ProcessData.sort_values('CountryName', axis=0, ascending=False, inplace=True)
print("Processed Data =========================")
print(ProcessData)
print("========================================")

# Output
soutputfile = r""
ProcessData.to_csv(soutputfile, index=False)
print('CSV to HORUS Done')



# Utility Start: JSON to HORUS
import pandas as pd

# Input
sInputFile = r""
InputData = pd.read_json(sInputFile, orient='index')
print("Input Data ============================")
print(InputData)
print("=======================================")

# Processing
ProcessData = InputData.copy()
ProcessData.drop(['ISO-2-CODE', 'ISO-3-Code'], axis=1, inplace=True)
ProcessData.rename(columns={
    'Country': 'CountryName',
    'ISO-M49': 'CountryNumber'
}, inplace=True)
ProcessData.set_index('CountryNumber', inplace=True)
ProcessData.sort_values('CountryName', ascending=False, inplace=True)
print("Processed Data =========================")
print(ProcessData)
print("========================================")

# Output
sOutputFile = r"F:\ADS Practical\Prac 2\HORUS-JSON-Country.csv"
ProcessData.to_csv(sOutputFile, index=False)

print("JSON to HORUS Done")


# Utility Start: IMAGE to HORUS
from skimage import io
import pandas as pd
import matplotlib.pyplot as plt

# Input Agreement
sInputFile = r""
data = io.imread(sInputFile)

plt.imshow(data)
plt.title("Input Image")
plt.axis('off')
plt.show()

print('Input Data')
print('Height (X):', data.shape[0])
print('Width (Y):', data.shape[1])
print('Channels:', data.shape[2])

# Processing Rules
height, width, channels = data.shape
rows = []

for x in range(height):
    for y in range(width):
        if channels == 4:
            r, g, b, a = data[x, y]
        else:
            r, g, b = data[x, y]
            a = 255  # Default alpha if not present
        rows.append((x, y, r, g, b, a))

process = pd.DataFrame(rows, columns=['XAxis', 'YAxis', 'Red', 'Green', 'Blue', 'Alpha'])
print(process.head())
print('Rows:', process.shape[0])
print('Columns:', process.shape[1])

# Output Agreement
sOutputFile = r""
process.to_csv(sOutputFile, index=False)

print('Image to HORUS Done')


# Utility Start AUDIO to HORUS

from scipy.io import wavfile
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Input
file = r""
print('Processing:', file)

InputRate, InputData = wavfile.read(file)

# Processing
if InputData.ndim == 2 and InputData.shape[1] == 2:
    ProcessData = pd.DataFrame(InputData, columns=['Ch1', 'Ch2'])
else:
    ProcessData = pd.DataFrame(InputData, columns=['Ch1'])

print("First few records (HORUS Audio Format):")
print(ProcessData.head())

# Output
OutputFile = r""
ProcessData.to_csv(OutputFile, index=False)
print('Audio to HORUS - Done')

# Utility End
