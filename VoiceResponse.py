# VoiceResponse.py
# Application that will accept webhook requests from api.ai, communicate with the car through the Tesla API, and give back appropriate responses
#
# Matt Dyson (matt@thedysons.net)
# 09/04/17

import logging
import teslajson
import Credentials
import web
import sys
import json
import time

log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] %(levelname)8s: %(message)s')
stream.setFormatter(formatter)

log.addHandler(stream)

urls = (
   '/webhook', 'webhook',
)

globalTesla = None
class setRangeParameter:
   def __init__(self, tesla):
      self.tesla = tesla

   def parse(self, param, range):
      params = {
         'charge limit': self.chargeLimit,
      }

      if param not in params:
         return "I'm sorry, I don't know how to set that"

      return params[param](range)

   def chargeLimit(self,range):
      range = range.replace("%","")
      data = { "percent": range }
      response = self.tesla.command("set_charge_limit", data)["response"]
      if response["result"]==True:
         return "Charge limit has been set to %s percent" % (range)
      else:
         log.info("Bad response from request to set charge limit to [%s]: %s" % (range, response))
         return "Sorry, I couldn't set the charge limit"

class setTemperatureParameter:
   def __init__(self, tesla):
      self.tesla = tesla
   
   def parse(self, param, temp):
      params = {
         'temperature': self.temperature,
      }

      if param not in params:
         return "I'm sorry, I don't know how to change the temperature on that"

      return params[param](temp)

   def temperature(self, temp):
      value = temp["amount"]
      data = { "driver_temp": value, "passenger_temp": value }
      response = self.tesla.command("set_temps", data)["response"]
      if response["result"]==True:
         log.info("Temperature set by request, now attempting to turn on preconditioning")
         response = self.tesla.command("auto_conditioning_start")["response"]
         if response["result"]==True:
            return "Temperature has been set to %s degrees and the air conditioning is running" % (value)
         else:
            log.info("Bad response from request to start AC: %s" % (response))
            return "I'm sorry, the air conditioning could not be started"
      else:
         log.info("Bad response from request to set temperature to [%s]: %s" % (value, response))
         return "Sorry, I couldn't set the temperature"

class setBooleanParameter:
   def __init__(self, tesla):
      self.tesla = tesla

   def parse(self, param, level):
      params = {
         'charge state': self.chargeState,
         'charge port': self.chargePort,
         #'doors': self.doors, # Not yet implemeted
         'temperature': self.temperature,
         'lights': self.lights,
         'horn': self.horn,
      }

      if param not in params:
         return "I'm sorry, I don't know how to switch that"

      return params[param](level)

   def lights(self,level):
      if level=="1":
         response = self.tesla.command("flash_lights")["response"]
         if response["result"]==True:
            return "Okay, I've flashed the lights"
         else:
            log.info("Bad response from request to flash lights: %s" % (response))
            return "Sorry, I couldn't flash the lights"
      else:
         return "You can't turn the lights off remotely, try asking me to flash the lights instead"

   def horn(self,level):
      if level=="1":
         response = self.tesla.command("honk_horn")["response"]
         if response["result"]==True:
            return "Honk honk!"
         else:
            log.info("Bad response from request to honk horn: %s" % (response))
            return "Sorry, I couldn't honk the horn"
      else:
         return "Sorry, I can't turn the horn off, try asking me to honk the horn"

   def chargeState(self,level):
      if level=="1":
         response = self.tesla.command("charge_start")["response"]
         if response["result"]==True:
            return "Charging has started"
         else:
            log.info("Bad response from request to start charging: %s" % (response))
            return "I'm sorry, charging could not be started"
      elif level=="0":
         response = self.tesla.command("charge_stop")["response"]
         if response["result"]==True:
            return "Charging has been stopped"
         else:
            log.info("Bad response from request to stop charging: %s" % (response))
            return "I'm sorry, charging could not be stopped"
      else:
         return "Sorry, you can only set charging to on or off"

   def chargePort(self,level):
      if level=="1":
         response = self.tesla.command("charge_port_door_open")["response"]
         if response["result"]==True:
            return "Charge port door has been opened"
         else:
            log.info("Bad response from request to open charge port door: %s" % (response))
            return "I'm sorry, I couldn't open the charge port door"
      else:
         return "Sorry, you can't close the charge port door remotely"

   def temperature(self,level):
      if level=="1":
         response = self.tesla.command("auto_conditioning_start")["response"]
         if response["result"]==True:
            return "Air conditioning has started"
         else:
            log.info("Bad response from request to start AC: %s" % (response))
            return "I'm sorry, the air conditioning could not be started"
      elif level=="0":
         response = self.tesla.command("auto_conditioning_stop")["response"]
         if response["result"]==True:
            return "Air conditioning has been stopped"
         else:
            log.info("Bad response from request to stop AC: %s" % (response))
            return "I'm sorry, the air conditioning could not be stopped"
      else:
         return "I couldn't decide if you wanted that on or off, try saying a temperature you want me to set"


class queryParameter:
   def __init__(self, tesla):
      self.tesla = tesla

   def parse(self, param):
      params = {
         'charge state': self.chargeState,
         'charge level': self.chargeLevel,
         'charge port': self.chargePort,
         'distance': self.distance,
         'temperature': self.temperature,
         'doors': self.doors,
      }

      if param not in params:
         return "I'm sorry, I don't know how to query that"

      return params[param]()

   def chargeState(self):
      state = self.tesla.data_request("charge_state")
      if state["charging_state"]=="Charging":
         return "The car is currently charging, with %s left until charged" % (state["time_to_full_charge"])
      elif state["charging_state"]=="Complete":
         return "Charging has been completed"
      return "The charge status is %s" % (state["charging_state"])

   def chargeLevel(self):
      state = self.tesla.data_request("charge_state")
      return "The charge level is currently %s percent" % (state["battery_level"])

   def chargePort(self):
      state = self.tesla.data_request("charge_state")
      return "The charge port is currently %s" % ("open" if state["charge_port_door_open"]==True else "closed")

   def distance(self):
      state = self.tesla.data_request("charge_state")
      return "The estimated battery range is currently %s miles" % (state["est_battery_range"])

   def temperature(self):
      state = self.tesla.data_request("climate_state")
      if state["inside_temp"] is not None and state["outside_temp"] is not None:
         return "It's currently %s degrees inside, and %s degrees outside" % (state["inside_temp"],state["outside_temp"])
      elif state["inside_temp"] is not None:
         return "It's currently %s degrees inside" % (state["inside_temp"])
      else:
         return "Sorry, I don't have any temperature data at the moment"

   def doors(self):
      state = self.tesla.data_request("vehicle_state")
      return "The car is currently %s" % ("locked" if state["locked"]==True else "unlocked")

class webhook:
   def GET(self):
      return self.POST()

   def POST(self):
      web.header("Content-type", "application/json")

      reqStart = time.time()

      request = json.loads(web.data())
      connection = teslajson.Connection(Credentials.TESLA_EMAIL, Credentials.TESLA_PASSWORD)
      tesla = connection.vehicles[0]

      speechReturn = ""

      try: # Try/catch around any request to Tesla, so we can send an appropriate response
         tesla.wake_up()

         intent = request["result"]["metadata"]["intentName"]
         param = request["result"]["parameters"]["carParam"]

         log.info("Received intent %s with params: %s" % (intent, request["result"]["parameters"]))

         if intent=="Query parameter":
            qp = queryParameter(tesla)
            speechReturn = qp.parse(param)
         elif intent=="Set generic parameter":
            if request["result"]["parameters"]["level"]:
               bp = setBooleanParameter(tesla)
               speechReturn = bp.parse(param,request["result"]["parameters"]["level"])
            elif request["result"]["parameters"]["percentage"]:
               rp = setRangeParameter(tesla)
               speechReturn = rp.parse(param,request["result"]["parameters"]["percentage"])
            elif request["result"]["parameters"]["temperature"] is not "":
               tp = setTemperatureParameter(tesla)
               speechReturn = tp.parse(param,request["result"]["parameters"]["temperature"])
         else:
            speechReturn = "I'm sorry, I couldn't work out how to do %s" % (request["result"]["metadata"]["intentName"])
      except:
         log.error("Exception talking to Tesla servers", exc_info=True)
         speechReturn = "I'm sorry, there was a problem communicating with the Tesla servers"

      response = { }
      response["speech"] = speechReturn
      response["displayText"] = speechReturn
      response["source"] = "Wattson" # TODO: Swap with actual name

      log.debug("Response processed in %s seconds" % (time.time()-reqStart))

      return json.dumps(response)

if __name__ == '__main__':
   log.info("Starting up Tesla VoiceResponse")
   
   try:
      log.info("Testing Tesla connection")
      tesla = teslajson.Connection(Credentials.TESLA_EMAIL, Credentials.TESLA_PASSWORD)
      v = tesla.vehicles[0]
      log.info("Credentials seem okay")
   except:
      log.error("Exception talking to Tesla servers", exc_info=True)
      sys.exit(0)

   log.debug("Starting up web server")
   app = web.application(urls, globals())
   app.internalerror = web.debugerror
   web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", 7800))
   log.debug("Web server has stopped")
