import os
import sys
from importlib import reload
from flask import Flask, render_template, redirect, request, url_for

#Security Tests

def pathtraversal(path):
#Test that attempts of path traversal will cause an error to be shown instead of displaying the page

def validname(username):
#Test that the regex for the username works

def token(session):
#Test that a new token is generated every session

#Functional Tests

def hintdisplay():
#Test that hints show up on the screen correctly

def themetoggletestcss():
#Test that the proper CSS is loaded on toggle

def persistence():
#Test that the theme stays the same across all pages


