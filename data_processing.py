import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


class pre_processing():
    def __init__(self):
        self.dataframe = pd.read_csv("NYPD_Complaint_Data_Current__Year_To_Date_.csv")

    def select_columns(self):
        self.dataframe = self.dataframe.loc[:, ['BORO_NM','Latitude', 'Longitude']]
    
    def calculate_average_crime_per_area(self):
        #remove null values
        crime_per_area_df = self.dataframe[self.dataframe["BORO_NM"].str.contains("null") == False]
        #count crime
        crime_per_area = crime_per_area_df.groupby("BORO_NM").size()
        #format into python dict
        solution = {}
        for count, crime_number in enumerate(list(crime_per_area)):
            solution[list(crime_per_area.index)[count]] = crime_number
        #get average population per district (&subdistrict)
        wikiurl="https://www.health.ny.gov/statistics/cancer/registry/appendix/neighborhoodpop.htm"
        response=requests.get(wikiurl)
        if response.status_code == 200:
            table = BeautifulSoup(response.text, 'html.parser')
            tables_of_interest=table.find_all('table',{'class':"light_table"})[0]
            tables_of_interest=pd.read_html(str(tables_of_interest))
            population_data=pd.DataFrame(tables_of_interest[0])
        #force into dataframe (note that this is not straightforward, considering the special nan values)
        population_list = []
        area_list =[]
        for count, area in enumerate(list(population_data["Borough"])):
            new_area=False
            for area2 in list(solution.keys()):
                if (str(area2).upper() in str(area).upper()) or (str(area).upper() in str(area2).upper()):
                    new_area = True
            if (new_area):
                if count !=0:
                    population_list.append(sum_total)
                area_list.append(area)
                sum_total = population_data.loc[count]["Total Population"]
            elif (not new_area): 
                sum_total = sum_total+ population_data.loc[count]["Total Population"]
            #the last entry
            if (count == len(list(population_data["Borough"]))-1):
                population_list.append(sum_total)
        #merge lists into final solution
        #note: in this case the order of areas is the same, but this is not assumed in the code
        final_solution = {}
        for index, area in enumerate(area_list):
            found_match = False
            for area2 in solution.keys():
                if (str(area2).upper() in str(area).upper()) or (str(area).upper() in str(area2).upper()):
                    found_match = True
                    in_area= area2
            if found_match:
                crime_density = solution.get(in_area) / population_list[index]
                final_solution[in_area] = crime_density
        #return dictionary of areas and crime density
        self.average_crime_rates = final_solution
        return final_solution

    def print_data(self):
        print(self.dataframe)
    
    def print_average_crime_rates(self):
        self.average_crime_rates = self.calculate_average_crime_per_area()
        print(self.average_crime_rates)

pp = pre_processing()
pp.select_columns()
pp.print_average_crime_rates()
