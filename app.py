from flask import Flask, render_template, request, jsonify
import requests
import numpy as np

app = Flask(__name__)

API_URL = 'https://ws.audioscrobbler.com/2.0/'
API_KEY = ''


