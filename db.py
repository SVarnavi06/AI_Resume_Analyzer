import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="varnavi06@12",
    database="ai_resume_analyzer"
)

cursor = connection.cursor()