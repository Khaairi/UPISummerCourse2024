import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from flask import Flask, render_template, jsonify



# Load data
# data = data[data['Province'].isin(province_to_analyze)]
years = [2019, 2020, 2021]
data_dir = 'data'

data = pd.DataFrame()
try:
    for year in years:
        file_path = os.path.join(data_dir, f'data_{year}.xlsx')
        if not os.path.exists(file_path):
            raise Exception(f'File {file_path} not found')
        df = pd.read_excel(file_path, header=1)
        df['Year'] = year
        data = pd.concat([data, df], ignore_index=True)
except Exception as e:
    raise Exception(f'Error reading file: {str(e)}')

# Preprocess the data
data.rename(columns={
    'Tahun': 'Year',
    'Provinsi': 'Province',
    'Kabupaten/Kota': 'City',
    'Timbulan Sampah Harian(ton)': 'Daily Waste (tons)',
    'Timbulan Sampah Tahunan(ton)': 'Annual Waste (tons)'
}, inplace=True)


# Export the concatenated data to a CSV file
export_file_path = os.path.join(data_dir, 'concatenated_data.csv')
data.to_csv(export_file_path, index=False)
# Print the columns to debug
print("Columns in the loaded data:", data.columns)
# Remove any duplicate column names that may have been added during concatenation
data = data.loc[:, ~data.columns.duplicated()]

# Analysis
# 1. Total annual waste generation in each province each year
annual_waste = data.groupby(['Province', 'Year'])['Annual Waste (tons)'].sum().reset_index()

# 2. Average total annual waste generation in each province for all years
average_annual_waste = annual_waste.groupby('Province')['Annual Waste (tons)'].mean().reset_index()

# 3. Province with the most and least annual waste generation each year
most_waste = annual_waste.loc[annual_waste.groupby('Year')['Annual Waste (tons)'].idxmax()].reset_index(drop=True)
least_waste = annual_waste.loc[annual_waste.groupby('Year')['Annual Waste (tons)'].idxmin()].reset_index(drop=True)

def categorize_province(row):
    if row['Annual Waste (tons)'] <= 100000:
        return 'GREEN'
    if row['Annual Waste (tons)'] <= 700000:
        return 'ORANGE'
    else:
        return 'RED'
    
average_annual_waste['Category'] = average_annual_waste.apply(categorize_province, axis=1)

# Generate and save graphs
# 1. Total annual waste generation in each province each year
top_n = 10  
average_waste_by_province = annual_waste.groupby('Province')['Annual Waste (tons)'].mean().reset_index()
top_provinces = average_waste_by_province.nlargest(top_n, 'Annual Waste (tons)')['Province']
filtered_annual_waste = annual_waste[annual_waste['Province'].isin(top_provinces)]

# Generate and save graphs
# 1. Total annual waste generation in top N provinces each year
plt.figure(figsize=(14, 7))
sns.set_palette("tab20")  # Use a distinct color palette with more colors
sns.barplot(data=filtered_annual_waste, x='Year', y='Annual Waste (tons)', hue='Province', dodge=True)
plt.title(f'Total Annual Waste Generation in Top {top_n} Provinces Each Year', fontsize=16, fontweight='bold')
plt.xlabel('Year', fontsize=14)
plt.ylabel('Annual Waste (tons)', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(title='Province', title_fontsize='13', fontsize='12', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout(rect=[0, 0, 0.85, 1]) 
plt.savefig('static/total_annual_waste.png')

# 2. Average total annual waste generation in each province for all years
plt.figure(figsize=(14, 7))
sns.barplot(data=average_annual_waste, x='Province', y='Annual Waste (tons)', hue='Category', dodge=False, palette={'GREEN': 'green', 'ORANGE': 'orange', 'RED': 'red'})
plt.title('Average Total Annual Waste Generation in Each Province for All Years')
plt.xlabel('Province')
plt.ylabel('Average Annual Waste (tons)')
plt.legend(title='Category')
plt.xticks(rotation=45, ha='right')  
plt.grid(True)
plt.tight_layout() 
plt.savefig('static/average_annual_waste.png')

# 3. Province with the most annual waste generation each year
plt.figure(figsize=(14, 7))
sns.barplot(data=most_waste, x='Year', y='Annual Waste (tons)', hue='Province')
plt.title('Province with Most Annual Waste Generation Each Year')
plt.xlabel('Year')
plt.ylabel('Annual Waste (tons)')
plt.legend(title='Province')
plt.grid(True)
plt.savefig('static/most_annual_waste.png')

# 4. Province with the least annual waste generation each year
plt.figure(figsize=(14, 7))
sns.barplot(data=least_waste, x='Year', y='Annual Waste (tons)', hue='Province')
plt.title('Province with Least Annual Waste Generation Each Year')
plt.xlabel('Year')
plt.ylabel('Annual Waste (tons)')
plt.legend(title='Province')
plt.grid(True)
plt.savefig('static/least_annual_waste.png')

# 5. Graph of the total annual amount of waste in each province from year to year
plt.figure(figsize=(14, 7))
sns.lineplot(data=annual_waste, x='Year', y='Annual Waste (tons)', hue='Province', marker='o')
plt.title('Total Annual Amount of Waste in Each Province from Year to Year')
plt.xlabel('Year')
plt.ylabel('Waste (tons)')
plt.legend(title='Province')
plt.grid(True)
plt.savefig('static/annual_waste_trend.png')

# 6. Categorized visualization of average annual waste generation
plt.figure(figsize=(14, 7))
sns.countplot(data=average_annual_waste, x='Category', palette={'GREEN': 'green', 'ORANGE': 'orange', 'RED': 'red'})
plt.title('Categorization of Average Annual Waste Generation in Each Province for All Years', fontsize=16, fontweight='bold')
plt.xlabel('Category', fontsize=14)
plt.ylabel('Number of Provinces', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig('static/average_annual_waste_category.png')



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data/annual_waste')
def get_annual_waste():
    return jsonify(annual_waste.to_dict(orient='records'))

@app.route('/data/average_annual_waste')
def get_average_annual_waste():
    return jsonify(average_annual_waste.to_dict(orient='records'))

@app.route('/data/most_waste')
def get_most_waste():
    return jsonify(most_waste.to_dict(orient='records'))

@app.route('/data/least_waste')
def get_least_waste():
    return jsonify(least_waste.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)