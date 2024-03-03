import csv


with open('FPL_and_odds_data_numeric.csv', 'r') as csvfile:
    datareader = csv.reader(csvfile)

    total_count = 0
    over4count = 0
    for i in datareader:
        total_count +=1
        if i[-1] == '1':
            over4count += 1
    print(total_count)
    print(over4count)