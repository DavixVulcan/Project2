# Project 2: Microservice-based architecture

A microservice-based web app serving a sales website.

The following functional requirements have been met:

The user must be able to
1. Register and log in to an account
2. See their stored cart
3. Browse the site, with features such as filtering and sorting
4. See product listings with price
5. Add and delete items from their cart
6. Check out their cart, clearing their order, allowing them to start a new order

There are six containers running in this service, each dedicated to a specific function regarding the site. The nodes all communicate with the main web app provider using gRPC, except for the image microservice, which its only purpose is to serve images. 

In order to run this web app, use the following commands: 

`docker compose build`

`docker compose up`

The added `redocontainer.bat` file is used to restart select containers, or the entire project, should no argument be used