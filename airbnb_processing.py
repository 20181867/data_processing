import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt

class preprocessing():
    def __init__(self):
        #get original dataframe
        #self.dataframe1 = pd.read_csv("Airbnb_Open_Data.csv", usecols = ['id','NAME', 'neighbourhood','price', 'room type'])
        
        #get dataframe with prices
        self.dataframe2 = pd.read_csv("airbnb-listingspublic.csv", on_bad_lines='skip', sep = ';',header=0, usecols = ['Name', 'Neighbourhood Cleansed','Bedrooms', 'Availability 30', 'Availability 60',
                                                                                                                       'Availability 90', 'Availability 365', 'Reviews per Month', 'Review Scores Rating', 'Price'])

        #get average rental prices per district 
        wikiurl="https://www.renthop.com/average-rent-in/new-york-ny"
        response=requests.get(wikiurl)
        if response.status_code == 200:
            table = BeautifulSoup(response.text, 'html.parser')
            tables_of_interest=table.find_all('table',{'class':"data-table"})[2]
            tables_of_interest=pd.read_html(str(tables_of_interest))
            self.rental_data=pd.DataFrame(tables_of_interest[0])

    def clean_data(self):
        # merge all dataframes and drop na values
        
        #use old data:
        #self.dataframe2 = self.dataframe2.rename(columns={"Name": "NAME"})
        #merged_data = pd.merge(self.dataframe1, self.dataframe2, how = 'inner', on='NAME')
        #merged_data = merged_data.dropna()

        #remove values not in neighborhood as defined by the rental prices table
        self.rental_data['Neighborhood'] = [re.split(',', x)[0] for x in self.rental_data['Neighborhood']]
        self.rental_data = self.rental_data.rename(columns={"Neighborhood": "Neighbourhood"})
        neighbourhoods = self.rental_data['Neighbourhood'].to_numpy()
        self.dataframe2 = self.dataframe2.rename(columns={"Neighbourhood Cleansed": "Neighbourhood"})
        #around 2000 columns drop, with for example neigbhourhood names such as 'china town'
        self.cleansed_data = self.dataframe2[self.dataframe2.Neighbourhood.isin(neighbourhoods)]

        merged_data = pd.merge(self.dataframe2, self.rental_data, how = 'inner', on='Neighbourhood')
        merged_data = merged_data.dropna()
        self.merged_data= merged_data

    
    def calculate_revenue(self):
        #expected revenue per month: (expected occupation days per month * price per day) - costs of renting in this neigborhood (for this amount of beds)

        #calculate average availability (as a score):
        #           average over all availabilities devided by 4 (since four columns) *30 (since monthly rent data)
        self.merged_data['Availability score'] = ((((self.merged_data['Availability 30']/30) + (self.merged_data['Availability 60']/60) +  
                    (self.merged_data['Availability 90']/90)  + (self.merged_data['Availability 365']/365))/4)*30)

        #calculate average popularity (as a score):
        self.merged_data['Popularity score'] =  self.merged_data['Reviews per Month'] * self.merged_data['Review Scores Rating']

        #normalize popularity score using min-max normalization
        self.merged_data['Popularity score'] = 1+ ((self.merged_data['Popularity score'] - self.merged_data['Popularity score'].min())/(self.merged_data['Popularity score'].max()- self.merged_data['Popularity score'].min()))

        #merge popularity score and availability score
        self.merged_data['AV/PO score'] =  self.merged_data['Availability score'] *  self.merged_data['Popularity score']

        #assumptions: no bedrooms = studio
        #             linear growth for more than 2 bedrooms
        #             an airbnb listing has no more than 6 seperate bedrooms (this is true for this dataset)
        self.merged_data['revenue studio'] = np.where(self.merged_data['Bedrooms']== 0.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                                                self.merged_data['Studio'].str.replace(",", "").str.replace("$", "").astype(int) , 0)
        
        self.merged_data['revenue 1 bed'] = np.where(self.merged_data['Bedrooms']== 1.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                                                self.merged_data['1 Bed'].str.replace(",", "").str.replace("$", "").astype(int) , 0)
        
        self.merged_data['revenue 2 beds'] = np.where(self.merged_data['Bedrooms']== 2.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                                        self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int) , 0)
        self.merged_data['revenue 3 beds'] = np.where(self.merged_data['Bedrooms']== 3.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                                        (((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int))
                                         - (self.merged_data['1 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))
                                         + ((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))
                                         ) , 0)
        self.merged_data['revenue 4 beds'] = np.where(self.merged_data['Bedrooms']== 4.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                                (((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int))
                                    - (self.merged_data['1 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))*2
                                    + ((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))
                                    ) , 0)
        self.merged_data['revenue 5 beds'] = np.where(self.merged_data['Bedrooms']== 5.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                        (((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int))
                            - (self.merged_data['1 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))*3
                            + ((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))
                            ) , 0)
        self.merged_data['revenue 6 beds'] = np.where(self.merged_data['Bedrooms']== 6.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                (((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int))
                    - (self.merged_data['1 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))*4
                    + ((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))
                    ) , 0)
        #7 or more occurs none of the time
        self.merged_data['revenue 7 beds'] = np.where(self.merged_data['Bedrooms']== 7.0, (self.merged_data['Price']*(self.merged_data['AV/PO score'])) -
                (((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int))
                    - (self.merged_data['1 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))*5
                    + ((self.merged_data['2 Bed'].str.replace(",", "").str.replace("$", "").astype(int)))
                    ) , 0)

        self.merged_data['revenue'] =  (self.merged_data['revenue studio'] + self.merged_data['revenue 1 bed'] +  self.merged_data['revenue 2 beds'] +
            self.merged_data['revenue 3 beds']+  self.merged_data['revenue 4 beds']+  self.merged_data['revenue 5 beds']+
            self.merged_data['revenue 6 beds']+  self.merged_data['revenue 7 beds'])




    def print_data(self):
        #the max bedrooms is 6
        #print(self.merged_data['Bedrooms'].max())

        print(self.merged_data)

        self.merged_data['revenue'].plot(kind='kde')
        plt.title("Revenue")
        plt.xlabel('Estimated revenue') 
        plt.show()
        plt.close()


        #plt.legend(bbox_to_anchor=(1.1, 1.05))
        #self.merged_data['Availability score'].plot(kind='kde')
        #self.merged_data['Availability 30'].plot(kind='kde')
        #plt.legend(['Availability score', 'Availability 30'], title='Legend')

        self.merged_data.boxplot(column='revenue',by='Neighbourhood')
        plt.xticks(rotation=90, fontsize=10, ha='right')
        plt.ylabel('Estimated revenue') 
        plt.title(" ")

pp = preprocessing()
pp.clean_data()
pp.calculate_revenue()
pp.print_data()
