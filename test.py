import pandas as pd
import re

def main():
	df = pd.read_csv("formula_D_D-1_2-00003_2-00544.csv", sep=';')
	df = df[["Signature"]]
	values = df.values
	results = []
	
	for i in values:
		numbers = re.findall(r'\d+', str(i))
		result = [int(num) for num in numbers]
		results.append(result)
	print(results)
		
	# with open("circulant_2d/optimal.csv", "w") as f:
		# df.to_csv(f, mode="w")

main()