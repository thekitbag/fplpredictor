from predictions import predict_gameweek
from models import train_and_save_XGBoost_classifier_model, save_model, tune_XGBoost_model, test_model
from processors import create_data_for_gameweeks


predict_gameweek(26)

#train_and_save_XGBoost_classifier_model()

#tune_XGBoost_model('./processed_data/training_data.csv')

#test_model('./trained_models/trained_XGBoost_model.pkl','./processed_data/testing_data.csv')

#create_data_for_gameweeks(21,26,'x.csv')