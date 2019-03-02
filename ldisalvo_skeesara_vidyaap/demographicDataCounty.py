"""
CS504 : demographicData.py
Team : Vidya Akavoor, Lauren DiSalvo, Sreeja Keesara
Description : Retrieval of demographic data by county using census.gov

February 28, 2019
"""

import datetime
import json
import uuid
import pandas as pd

import dml
import prov.model
import urllib.request

from ldisalvo_skeesara_vidyaap.helper.constants import TEAM_NAME, COUNTY_URL, MA_COUNTY_LIST, DEMOGRAPHIC_DATA_COUNTY, \
    DEMOGRAPHIC_DATA_COUNTY_NAME


class demographicDataCounty(dml.Algorithm):
    contributor = TEAM_NAME
    reads = []
    writes = [DEMOGRAPHIC_DATA_COUNTY_NAME]

    @staticmethod
    def execute(trial=False):
        """
            Retrieve demographic data by country from census.gov and insert into collection
            ex)
             { "Barnstable County, Massachusetts":
                "Population estimates, July 1, 2017,  (V2017)": "213,444",
                "Population estimates base, April 1, 2010,  (V2017)": "215,868",
                "Population, percent change - April 1, 2010 (estimates base) to July 1, 2017,  (V2017)": "-1.1%",
                "Population, Census, April 1, 2010": "215,888",
                "Persons under 5 years, percent": "3.6%",
                "Persons under 18 years, percent": "15.1%",
                ..........................
            }
        """
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate(TEAM_NAME, TEAM_NAME)

        # Retrieve data from census.gov for each county (note: retrieval generates csv with max of 6 locations)
        county_divisions = [MA_COUNTY_LIST[:6], MA_COUNTY_LIST[6:12], MA_COUNTY_LIST[12:14]]
        all_dfs= []
        for divisions in county_divisions:
            counties = ""
            for county in divisions:
                counties += (county.lower() + "massachusetts,").replace(" ", "")
            counties = counties[:-1]
            url = COUNTY_URL[:43] + counties + COUNTY_URL[43:]
            df = pd.read_csv(urllib.request.urlopen(url))
            df = df.drop(df.index[-20:])
            df.set_index("Fact", inplace=True)
            df = df.transpose()
            df = df[~df.index.str.contains("Note")]
            cols = list(df)
            all_dfs.append(df)

        for df in all_dfs:
            df.columns = cols

        joined_df = pd.concat(all_dfs)
        df = joined_df.dropna(axis=1, how='all')
        df = df.reset_index()
        df = df.rename(columns={'index': 'Town'})

        records = []
        for x in df.to_dict(orient='records'):
            records += [x]

        # Insert rows into collection
        repo.dropCollection(DEMOGRAPHIC_DATA_COUNTY)
        repo.createCollection(DEMOGRAPHIC_DATA_COUNTY)
        repo[DEMOGRAPHIC_DATA_COUNTY_NAME].insert_many(records)
        repo[DEMOGRAPHIC_DATA_COUNTY_NAME].metadata({'complete': True})
        print(repo[DEMOGRAPHIC_DATA_COUNTY_NAME].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}


    @staticmethod
    def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('alice_bob', 'alice_bob')
        doc.add_namespace('alg',
                          'http://datamechanics.io/algorithm/')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat',
                          'http://datamechanics.io/data/')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont',
                          'http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:alice_bob#example',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'],
                                 'ont:Extension': 'py'})
        resource = doc.entity('bdp:wc8w-nujj', {'prov:label': '311, Service Requests',
                                                prov.model.PROV_TYPE: 'ont:DataResource',
                                                'ont:Extension': 'json'})
        get_found = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        get_lost = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_found, this_script)
        doc.wasAssociatedWith(get_lost, this_script)
        doc.usage(get_found, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=Animal+Found&$select=type,latitude,longitude,OPEN_DT'
                   }
                  )
        doc.usage(get_lost, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=Animal+Lost&$select=type,latitude,longitude,OPEN_DT'
                   }
                  )

        lost = doc.entity('dat:alice_bob#lost', {prov.model.PROV_LABEL: 'Animals Lost',
                                                 prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        found = doc.entity('dat:alice_bob#found', {prov.model.PROV_LABEL: 'Animals Found',
                                                   prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(found, this_script)
        doc.wasGeneratedBy(found, get_found, endTime)
        doc.wasDerivedFrom(found, resource, get_found, get_found, get_found)

        repo.logout()

        return doc

'''
# This is example code you might use for debugging this module.
# Please remove all top-level function calls before submitting.
example.execute()
doc = example.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))
'''

## eof


