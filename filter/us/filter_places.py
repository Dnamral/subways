import pandas as pd
#Year,StateAbbr,StateDesc,LocationName,DataSource,Category,Measure,Data_Value_Unit,Data_Value_Type,Data_Value,Data_Value_Footnote_Symbol,Data_Value_Footnote,Low_Confidence_Limit,High_Confidence_Limit,TotalPopulation,TotalPop18plus,Locat       ionID,CategoryID,MeasureId,DataValueTypeID,Short_Question_Text,Geolocation

# === INPUT ===
input_csv = 'PLACES_County_Data_2024.csv'  # replace with your downloaded file
output_csv = 'obesity_by_county.csv'

# === Step 1: Load data ===
df = pd.read_csv(input_csv)

# Check available measures
print("Available measures:")
print(df['Measure'].unique())

# === Step 2: Filter for obesity measure ===
target_measure = 'Obesity among adults'
#target_measure = 'Binge drinking among adults'
filtered = df[df['Measure'] == target_measure]

# === Step 3: Keep only needed columns ===
# CountyFIPS → GEOID, Data_Value → value
filtered = filtered[['LocationID', 'Data_Value']].rename(
    columns={'LocationID': 'GEOID', 'Data_Value': 'value'}
)

# Ensure GEOID is zero-padded (should be 5-digit strings)
filtered['GEOID'] = filtered['GEOID'].apply(lambda x: f"{int(x):05d}")

# === Step 4: Save to new CSV ===
filtered.to_csv(output_csv, index=False)

print(f"Saved filtered obesity data to {output_csv}")
print(f"Sample rows:\n{filtered.head()}")
