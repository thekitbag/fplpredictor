from predictions import predict_gameweek
from models import train_and_save_XGBoost_classifier_model, save_model, tune_XGBoost_model, test_model
from processors import create_data_for_gameweeks

from random import randint


while True:
    a = input("Choose an option \n 1. predict gameweek \n 2. train_model \n 3. test_model \n 4. tune model \n 5. create data \n\n")

    if a == "1":
        a2 = input("which gameweek?")
        predict_gameweek(int(a2))  
    elif a == "2":
        train_and_save_XGBoost_classifier_model()
    elif a == "3":
        test_model('./trained_models/trained_XGBoost_model.pkl','./processed_data/testing_data.csv')
    elif a == "4":
        tune_XGBoost_model('./processed_data/testing_data.csv')
    elif a == "5":
        a2 = input("Enter start gameweek: ")
        a3 = input("Enter end gameweek: ")
        a4 = input("Enter filename: ")
        create_data_for_gameweeks(int(a2), int(a3), a4)
    else:
        print("Invalid input. Please try again.") 
        continue  # Skip back to the beginning of the loop

    # Optional: Offer an exit option 
    exit_choice = input("Perform new action?: ")
    if exit_choice.lower() != 'y':
        break

