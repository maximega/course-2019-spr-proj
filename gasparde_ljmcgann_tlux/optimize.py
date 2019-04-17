from shapely.geometry import Polygon, Point
import dml
import prov.model
import datetime
import codecs
import uuid
import random
from scipy.cluster.vq import kmeans
import matplotlib.pyplot as pyplt

class optimize(dml.Algorithm):
    contributor = 'gasparde_ljmcgann_tlux'
    reads = [contributor + ".Neighborhoods", contributor + ".ParcelsCombined", contributor + ".Statistics"]
    writes = [contributor + ".KMeans"]

    @staticmethod
    def health_score(row):
        average = (float(row["obesity"]) + float(row["low_phys"]) + float(row["asthma"])) // 3
        if average > 20:
            return 100
        elif average > 15:
            return 10
        else:
            return 1
    @staticmethod
    def distance_score(distance_score, stdev, mean):
        z_score = (distance_score - mean)/(stdev)
        if z_score > 1.5:
            return 100
        elif z_score > .75:
            return 10
        else:
            return 1
    @staticmethod
    def geojson_to_polygon(geom):
        """

        :return: list of shapely polygons corresponding to the geojson object
        """
        polys = []
        if geom['type'] == 'Polygon':
            shape = []
            coords = geom['coordinates']
            for i in coords[0]:
                shape.append((i[0], i[1]))
            polys.append(Polygon(shape))
        if geom['type'] == 'MultiPolygon':
            coords = geom['coordinates']
            for i in coords:
                shape = []
                for j in i:
                    for k in j:
                        # need to change list type to tuple so that shapely can read it
                        shape.append((k[0], k[1]))
                poly = Polygon(shape)
                polys.append(poly)
        return polys


    @staticmethod
    def execute(trial=False):
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate(optimize.contributor, optimize.contributor)
        # read in neighborhoods to get the list of their names
        neighborhoods = list(repo[optimize.contributor + ".Neighborhoods"].find())
        # load in parcels as we will iterate kmeans from this data
        parcels = repo[optimize.contributor + ".ParcelsCombined"]
        stats = repo[optimize.contributor + ".Statistics"]
        repo.dropCollection(optimize.contributor + ".KMeans")
        repo.createCollection(optimize.contributor + ".KMeans")
        for i in range(len(neighborhoods)):
            name = neighborhoods[i]["properties"]["Name"]
            neighborhood = list(parcels.find({"Neighborhood":name}))
            distance_kmeans = []
            health_score_kmeans = []
            if stats.find_one({"Neighborhood":name, "variable": "distance_score"}) is not None:
                dist_mean = float(stats.find_one({"Neighborhood": name, "variable": "distance_score", "statistic": "mean"})["value"])
                dist_stdev = float(stats.find_one({"Neighborhood": name, "variable": "distance_score", "statistic": "std_dev"})["value"])
                for j in range(len(neighborhood)):

                    shape = optimize.geojson_to_polygon(neighborhood[j]["geometry"])[0]
                    # out of order, want [latitude, longitude]
                    coords = [shape.centroid.coords[0][1], shape.centroid.coords[0][0]]
                    # do weighted kmeans by adding additional points

                    dist_weight = optimize.distance_score(neighborhood[j]["distance_score"], dist_stdev, dist_mean)
                    health_weight = optimize.health_score(neighborhood[j])
                    for _ in range(dist_weight):
                        distance_kmeans.append([coords[0], coords[1]])
                    for _ in range(health_weight):
                        #health_score_kmeans.append([coords[0], coords[1]])
                        #this was for purpose of making our scatterplots
                        #look nicer, not needed for kmeans to function properly

                        health_score_kmeans.append([coords[0], coords[1]])


            if len(distance_kmeans) > 0:
                dist_output = kmeans(distance_kmeans, 5)[0].tolist()
                repo[optimize.contributor + ".KMeans"].insert_one({"Neighborhood": name,"type":"distance","means": dist_output})
                health_output = kmeans(health_score_kmeans, 5)[0].tolist()
                repo[optimize.contributor + ".KMeans"].insert_one({"Neighborhood": name, "type": "health", "means": health_output})

        repo[optimize.contributor + ".KMeans"].metadata({'complete': True})



    @staticmethod
    def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):
        return 0
