# TeslaVoice
## Introduction

Project to allow interacting with the [Telsa API](http://docs.timdorr.apiary.io/) through [Google Home](https://madeby.google.com/home/).

This requires two components - an [API.AI](http://api.ai) project (contained within one directory here), and a web server that makes appropriate queries against the Telsa API.

More project details, and a video of the project in action, can be found at http://mattdyson.org/projects/teslavoice

## Getting started
### Web Server
The web server (VoiceResponse.py) is designed to be run as a [supervisord](http://supervisord.org/) service, and will listen for requests on `/webhook` that meet the format passed by [API.AI](http://api.ai), returning an appropriately formatted response.

An additional file named Credentials.py is also required in the same directory, containing two variables - `TESLA_EMAIL` and `TESLA_PASSWORD`, which must match your MyTesla account

For integration with Google Home, this web server must be accessible through HTTPS (HTTP requests are not allowed)

### API.AI project
Insert the URL of the above web server into `apiai/agent.json` in the appropriate place, then ZIP the entire folder and upload through the 'Export and Import' function found in an API.AI project.

You should then be able to publish the test version for local usage through the method described [on this page](https://medium.com/google-cloud/how-to-create-a-custom-private-google-home-action-260e2c512fc) to create a permanent private action on Google Home.
