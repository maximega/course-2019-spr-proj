# Growing Voter Engagement in Communities of Color

For this project, we are working with Amplify Latinx and BU Spark! to analyze Massachusetts voting and demographic data to suggest where they should focus their voter turnout efforts in order to get more people of color out to vote.

We are starting with 5 data sets, one of which is public that we found through our own research, and four private data sets which were provided by Amplify Latinx:

1. Demographics by Towns (public)
2. Massachusetts Early Voting Data
3. Registered Voter Demographics
    a) Senate District
    b) Precinct
    c) Congressional District
4. Non-Registered Voter Demographics
    a) Senate District
    b) Precinct
    c) Congressional District
5. Voter Turnout Percentages (1948-2016)

We are combining these data sets to analyze where people are voting, who is turning out to vote, and extrapolating where voter registration efforts are going to be effective. Ultimately, our goal is to identify which elections are such that more voters showing up would change the result and provide Amplify Latinx with an interactive, embeddable heat map of Massachusetts.

To start, we isolated race and ethnicity data from Registered (3a) and Non-Registered (4a)Voter Demographics by Senate District, and then aggregating those data sets. From this, we produced a coefficient that we plan to further develop for Amplify Latinx to use to strategize. Additionally, we used Demographics by Town (1) and early voting data (2) to compare voter registration percentages with percentages of people of color. This transformation will also be used to suggest where to apply GOTV efforts. For example, if we can identify towns where there is a correlation between low voter registration and high percentage of people of color, we would suggest GOTV efforts there. Finally, we used the Google Geocoding API to transform Demographics by Towns (1) into the geocoding information necessary to use in the map.

## course-2019-spr-proj

In this project, you will implement platform components that can obtain a some data sets from web services of your choice, and platform components that combine these data sets into at least two additional derived data sets. These components will interact with the backend repository by inserting and retrieving data sets as necessary. They will also satisfy a standard interface by supporting specified capabilities (such as generation of dependency information and provenance records).

**This project description will be updated as we continue work on the infrastructure.**

## MongoDB infrastructure

### Setting up

We have committed setup scripts for a MongoDB database that will set up the database and collection management functions that ensure users sharing the project data repository can read everyone's collections but can only write to their own collections. Once you have installed your MongoDB instance, you can prepare it by first starting `mongod` _without authentication_:
```
mongod --dbpath "<your_db_path>"
```
If you're setting up after previously running `setup.js`, you may want to reset (i.e., delete) the repository as follows.
```
mongo reset.js
```
Next, make sure your user directories (e.g., `alice_bob` if Alice and Bob are working together on a team) are present in the same location as the `setup.js` script, open a separate terminal window, and run the script:
```
mongo setup.js
```
Your MongoDB instance should now be ready. Stop `mongod` and restart it, enabling authentication with the `--auth` option:
```
mongod --auth --dbpath "<your_db_path>"
```

### Working on data sets with authentication

With authentication enabled, you can start `mongo` on the repository (called `repo` by default) with your user credentials:
```
mongo repo -u alice_bob -p alice_bob --authenticationDatabase "repo"
```
However, you should be unable to create new collections using `db.createCollection()` in the default `repo` database created for this project:
```
> db.createCollection("EXAMPLE");
{
  "ok" : 0,
  "errmsg" : "not authorized on repo to execute command { create: \"EXAMPLE\" }",
  "code" : 13
}
```
Instead, load the server-side functions so that you can use the customized `createCollection()` function, which creates a collection that can be read by everyone but written only by you:
```
> db.loadServerScripts();
> var EXAMPLE = createCollection("EXAMPLE");
```
Notice that this function also prefixes the user name to the name of the collection (unless the prefix is already present in the name supplied to the function).
```
> EXAMPLE
alice_bob.EXAMPLE
> db.alice_bob.EXAMPLE.insert({value:123})
WriteResult({ "nInserted" : 1 })
> db.alice_bob.EXAMPLE.find()
{ "_id" : ObjectId("56b7adef3503ebd45080bd87"), "value" : 123 }
```
If you do not want to run `db.loadServerScripts()` every time you open a new terminal, you can use a `.mongorc.js` file in your home directory to store any commands or calls you want issued whenever you run `mongo`.

## Other required libraries and tools

You will need the latest versions of the PROV, DML, and Protoql Python libraries. If you have `pip` installed, the following should install the latest versions automatically:
```
pip install prov --upgrade --no-cache-dir
pip install dml --upgrade --no-cache-dir
pip install protoql --upgrade --no-cache-dir
```
If you are having trouble installing `lxml` in a Windows environment, you could try retrieving it [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/).

Note that you may need to use `python -m pip install <library>` to avoid issues if you have multiple versions of `pip` and Python on your system.

## Formatting the `auth.json` file

The `auth.json` file should remain empty and should not be submitted. When you are running your algorithms, you should use the file to store your credentials for any third-party data resources, APIs, services, or repositories that you use. An example of the contents you might store in your `auth.json` file is as follows:
```
{
    "services": {
        "cityofbostondataportal": {
            "service": "https://data.cityofboston.gov/",
            "username": "alice_bob@example.org",
            "token": "XxXXXXxXxXxXxxXXXXxxXxXxX",
            "key": "xxXxXXXXXXxxXXXxXXXXXXxxXxxxxXXxXxxX"
        },
        "mbtadeveloperportal": {
            "service": "http://realtime.mbta.com/",
            "username": "alice_bob",
            "token": "XxXX-XXxxXXxXxXXxXxX_x",
            "key": "XxXX-XXxxXXxXxXXxXxx_x"
        }
    }
}
```
To access the contents of the `auth.json` file after you have loaded the `dml` library, use `dml.auth`.

## Running the execution script for a contributed project.

To execute all the algorithms for a particular contributor (e.g., `alice_bob`) in an order that respects their explicitly specified data flow dependencies, you can run the following from the root directory:
```
python execute.py alice_bob
```
To execute the algorithms for a particular contributor in trial mode, use the `-t` or `--trial` option:
```
python execute.py alice_bob --trial
