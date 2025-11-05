
# # Practical 4A  Implement Basic Logging (Process Status Tracking)



# import logging

# # Setup logging
# logging.basicConfig(
#     filename='basic_logging.log',
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# def run_process():
#     logging.info("Process started.")
#     try:
#         # Simulated data loading
#         data = [1, 2, 3]
#         logging.info("Data loaded successfully.")
        
#         # Simulated processing
#         result = [x**2 for x in data]
#         logging.info(f"Processing complete: {result}")
        
#     except Exception as e:
#         logging.error(f"Error during processing: {e}")
#     finally:
#         logging.info("Process finished.")
    
#     print("Logging completed")

# run_process()


# Practical 4A


# import logging

# logging.basicConfig(filename='basic_logging.log', level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

# try:
#     data = [1, 2, 3]
#     result = [x**2 for x in data]
#     logging.info(f"Processing complete: {result}")
# except Exception as e:
#     logging.error(e)
# finally:
#     print("Logging completed")

# Practical 4A


import logging
logging.basicConfig(filename='basic_logging.log', level=logging.INFO)

data = [1, 2, 3]
logging.info(f"Squares: {[x**2 for x in data]}")

print("Logging completed")


# # Practical 4B  Implement Data Provenance (Track Data Transformations)


# import pandas as pd
# from datetime import datetime
# # Simulated data
# df=pd.DataFrame({
#      'Customer_ID': [101, 102, 103],
#     'Tenure': [12, 24, 36]
# })

# # Record original source
# provenance_log = []
# # Transformation
# df ['tenure bucket'] = pd.cut (df ['Tenure'], bins=[0, 18, 36], labels=['Short', 'Medium' ])

# # Record provenance
# for col in ['tenure bucket']:
#     provenance_log.append({
#             'Data Entity': col,
#             'Source Table': 'Customer Data',
#             'Transformation_Step': 'Binning from numeric column',
#             'Timestamp': datetime.now()
#     })
# # Display final transformed DataFrame
# print (" Final Transformed Data: ")
# print (df)

# # Save final data to CSV
# df.to_csv("transformed_customer_data.csv", index=False)

# #Output provenance log as DataFrame
# provenance_df = pd.DataFrame(provenance_log)
# print ("\n Provenance Log: ")
# print (provenance_df)

# # Save provenance log to CSV
# provenance_df.to_csv ("provenance_log.csv", index=False)


# Practical 4B


import pandas as pd
from datetime import datetime

df = pd.DataFrame({'Customer_ID':[101,102,103],'Tenure':[12,24,36]})
df['Tenure_Bucket'] = pd.cut(df['Tenure'], bins=[0,18,36], labels=['Short','Medium'])

prov = pd.DataFrame([{'Data Entity':'Tenure_Bucket','Source':'Customer Data',
                      'Step':'Binning','Time':datetime.now()}])

print("Final Data:\n", df, "\n\nProvenance Log:\n", prov)
