# Parking App

We are going to build an app to track when TAPS (parking enforcement) is at a certain parking structure. It will have 2 main components: manual "I saw TAPS at _____" + "I parked at _____" buttons and a temporal model that predicts the likelihood of TAPS being at any particular lot that we have available. Each of these features will be separated into two tabs at the bottom.

## Overview

UI will be retro style, gamified/pixelated buttons. App should be as easy as possible for the user to use. We will be using swiftUI and Python FastAPI backend with a Postgres DB. Create a Dockerfile so I can run this on Docker. DO NOT CREATE/MODIFY ANY XCODE PROJECT FILES!!!! I WILL DO THIS FOR YOU, PLEASE ASK IF NEEDED. We will start out with only tracking one parking structure, Hutchinson Parking Structure. Eventually we will expand to others. 

## Buttons

The two buttons will be on top of each other. The "I saw TAPS" button will be red, the other one will be green.

### I saw TAPS button

Red. One user clicking it will notify everyone who marked themselves as parked at this lot (via the other button). Require confirmation pop-up before clicking this button, saying that it's going to notify everyone.

### I parked at _____ Button

Green initially. Once pressed, this user is added to the list of people to be notified if/when TAPS is spotted at the parking strucutre they selected. Also once pressed, the button transforms to be yellow and says "I am leaving _____". The user will click this button when they leave, and they will be removed from the notification list. Send a reminder after 3 hours of initial button press if they have not clicked the button again to "check out"

## Probability

We need some sort of AI-based tool (regression model?) to calculate the probability that TAPS is present in the currently selected parking garage. 
