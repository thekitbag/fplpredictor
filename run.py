from predictions import predict_gameweek
from models import train_and_save_XGBoost_classifier_model, save_model, tune_XGBoost_model, test_model



predict_gameweek(30)

#train_and_save_XGBoost_classifier_model()
#tune_XGBoost_model('./processed_data/training_data.csv')
#test_model('./trained_models/trained_XGBoost_model.pkl','./processed_data/testing_data.csv')