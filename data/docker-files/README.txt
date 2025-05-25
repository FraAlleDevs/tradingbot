## How to use this Docker Container 

First of all the password for the postgres instance in the docker container is stored in a ".env" file in the same directory as the compose.yaml file. 

You can create your own `.env` to store your crendentials. In the `.env` you need to add a line as follows:

```
POSTGRES_PASSWORD={YOUR PASSWORD HERE}
```

Once the setup is complete, meaning you have created and filled your `.env` file and you have added the `.csv` file into the `/dataset/` directory you can run the container using:

`docker-compose -f compose.yaml up -d`

Check the container is running with  `docker ps`, you should be able to see it is available on port 5432. If that fails,  you can also see if postgres is running using
`ss -lt` 

Once it is running you can talk to the database through 2 main methods:

### 1) Using psql - The Postgres Interactive Terminal. 

First you need to have psql installed. This is usually done by just having PostgreSQL installed. 

To connect to the database you run the following command:

```
psql -h localhost -p 5432 -d bitcoin_db -U root
```

-h stands for Host.
-p stands for port.
-d stands for DB_name. 
-U stands for User.

You will then be prompted to give the password, this will be what is stored in the .env you create. 

Once connected you will be in an interactive shell where you can Query the DB using SQL. 

first run `\dt` in the shell, this will show you the name of the Table. This stands for "Describe Table"

when you see the list, query the table you want. For example to select all items from the bitcoin historical table, do:

```
SELECT * FROM btc_historical;
```


#### 2) Accessing the DB through Code Libraries. Example python. 

Take a look at the `python-example-script.py`, you can run it by using `python3 python-example-script.py`. 
Just make sure you have the `Psycopg2` package installed. This package is a popular python package for querying with PostgreSQL. 

The current script will print out all data in the database, its a lot so it will take a sec. Make any other python script using Psycopg2 to query the database as you wish. 





