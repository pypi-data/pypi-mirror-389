# iRODS environments for Utrecht University YoDa servers

This repository can be used to create an iRODS environment json that is needed to connect to the Utrecht University YoDa servers. 


## Step 1: Install the plugin
Type the following on the command line (in your virtual environment if you use one):

```sh
pip install ibridges-servers-uu
```

## Step 2: Find the right server

On the command line run the following command:

```sh
ibridges setup --list
```

This shows you all the names of the YoDa servers available.

## Step 3: Create your irods_environment.json

In the following examples, we use the `uu-its` server, replace it with the server that is available to your faculty.

```sh
ibridges setup uu-its
```

This will ask for your email address. After filling it in, a file will be created in the default location for the irods environment file (`~/.irods/irods_environment.json` on Linux and MacOS). You can modify this location adding the `--output SOME_NEW_LOCATION` flag to the above command.

## Step 4: Start using iBridges

For the main documentation on how to use iBridges, see the iBridges main [repository](https://github.com/UtrechtUniversity/iBridges).

```sh
ibridges init
```

which will ask you for your data access password, which you can obtain through the YoDa portal.
