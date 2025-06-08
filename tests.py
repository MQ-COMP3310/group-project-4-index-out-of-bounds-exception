import os
import sys
from importlib import reload
from flask import Flask, render_template, redirect, request, url_for

#Security Tests

def pathtraversal(path):
#Test that attempts of path traversal will cause an error to be shown instead of displaying the page
#Check for "..", "/", "|" which are symbols used for path traversal

def validname(username):
#Test that the regex for the username works
#Check that the regex successfully eliminates and removes symbols with example name "testusername123/|.."

def token(session):
#Test that a new token is generated every session


#Functional Tests

def hintdisplay():
#Test that hints show up on the screen correctly

def themetoggletestcss():
#Test that the proper CSS is loaded on toggle

def persistence():
#Test that the theme stays the same across all pages


