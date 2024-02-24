import io
import os
import re
import csv
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

class Config:

	__template_path = "config_v1.yml"
	__y = ["Network throughput (flits/cycle)", "Global average delay (cycles)"]
	__x = {
		"packet_injection_rate": None # here we will have a position of param in config file
	}

	params_range = {
		"topology_args": {
			"MESH":  (2, 10, 2),
			"TORUS": (2, 10, 2),
			"CIRCULANT": None
		},
		"routing_algorithm": {
			"MESH":  ["TABLE_BASED", "MESH_XY"],
			"TORUS": ["TABLE_BASED", "MESH_XY"],
			"CIRCULANT": ["TABLE_BASED", "RING_SPLIT", "VIRTUAL_RING_SPLIT"]
		},
		"routing_table": {
			"MESH":  ["DIJKSTRA", "MESH_XY", "GREEDY_PROMOTION", "UP_DOWN"],
			"TORUS": ["DIJKSTRA", "MESH_XY", "GREEDY_PROMOTION"],
			"CIRCULANT": [
				"DIJKSTRA",
				"CIRCULANT_PAIR_EXCHANGE", "CIRCULANT_MULTIPLICATIVE", 
				"CIRCULANT_CLOCKWISE", "CIRCULANT_ADAPTIVE"
			]
		},
		"buffer_depth": (2, 20, 2),
		"packet_injection_rate": (0, 1, 0.1),

	}

	def __init__(self, ids):
		# simple way to configure simulation params
		self.__ids = {
			"topology": "MESH",
			"topology_args": "[10, 10]",
			"topology_channels": 1,
			"virtual_channels":  2,
			"buffer_depth":  8,

			"min_packet_size": 8,
			"max_packet_size": 8,
			"flit_injection_rate": "true",
			"scale_with_nodes": "false",
			"packet_injection_rate": 0.05,

			"routing_algorithm":  "MESH_XY",
			"routing_table": 	  "MESH_XY",

			"clock_period_ps":    1000,
			"simulation_time":    10000,
			"stats_warm_up_time": 300,
		}
		for key in ids:
			self.__ids[key] = ids[key] 

		self.init_values()

	def init_values(self):
		# we need only the throughput and latency values for graphs
		self.results = pd.DataFrame({
			"packet_injection_rate": [],
			"Network production (flits/cycle)": [],
			"Network acceptance (flits/cycle)": [],
			"Network throughput (flits/cycle)": [],
			"Global average delay (cycles)": [],
		})
		# read values from yml-file and store it to __params
		with open(self.__template_path, "r") as f:
			lines = f.readlines()
			pattern = r":\s"

			for i, line in enumerate(lines):
				if line == "\n": continue
				key = re.split(pattern, line, maxsplit=1)[0]
				if key in self.__x:
					# now we know where to replace x-params in config-file
					self.__x[key] = i

				if key in self.__ids:
					lines[i] = f"{key}: {self.__ids[key]}\n"
			self.__params = lines
		# 	
		self.__file_handler = None
		# 
		self.__temp_path = f"""temp-{self.__ids["topology"]}-{self.__ids["routing_table"]}"""
		self.__temp_path = f"""{self.__temp_path}-{self.__ids["routing_algorithm"]}.yml"""
		

		self.__result_dir = f"""results/{self.__ids["topology"]}-{self.__ids["routing_table"]}-{self.__ids["routing_algorithm"]}"""
		if not os.path.exists("results/"):
			os.system("mkdir results")

		if not os.path.exists("self.__result_dir"):
			os.system(f"mkdir {self.__result_dir}")

		# for example: "MESH-[10, 10]-DIJKSTRA-MESH_XY.csv"
		self.__result_path = f"""{self.__result_dir}/{self.__ids["topology"]}-{self.__ids["topology_args"]}"""
		self.__result_path = f"""{self.__result_path}-{self.__ids["routing_table"]}-{self.__ids["routing_algorithm"]}.csv"""

	# for now it is only for the packet_injection_rate param
	def edit_content(self, key, value):
		self.__params[self.__x[key]] = f"{key}: {str('%.1f'%value)}\n" # update x value
		self.__file_handler.seek(0) # move to the top of the file
		self.__file_handler.truncate() # clear all
		self.__file_handler.writelines(self.__params) # write updated content

	def run(self, key="packet_injection_rate"):
		self.__file_handler = open(self.__temp_path, "w")
		start, end, step = self.params_range[key]

		# run newxim with __temp_path.yml (end-start)/step times
		for i in np.arange(start, end+step, step):
			self.edit_content(key, i)
			result = os.popen(f"./Newxim.exe -config {self.__temp_path}", "r").read()

			# there must be a code, which will drop unnecessary lines from result text
			pattern = re.compile(r"(\w+):\s*(.*)") 	# find all lines, which have ':'
			result = pattern.findall(result) 		# create list of tuples (key, value) from lines "key: value"
			dresult = {}							# an empy dictionary for the final result
			for k, v in result:
				if k in self.results.columns.to_list():
					dresult[k] = v.strip()
			dresult[key] = '%.1f'%i	 # add x-value to the row
			# finally add the row of dictonary to results
			self.results = pd.concat([self.results, pd.DataFrame([dresult])], ignore_index=True)
		
		os.system(f"rm {self.__temp_path}") # delete __temp_path.yml
		
		# now save results to __result_path.csv
		with open(f"{self.__result_path}", "w") as f:
			self.results.to_csv(f, index=False)


key = "topology_args"
def tests(topology):
	ids = {
		"topology": f"{topology}",
		"topology_args": "{i}",
		"routing_algorithm": "{i}",
		"routing_table": "{i}"
	}
	if (topology == "CIRCULANT"):
		ring_params = pd.read_csv("circulant_2d/ring_selection.csv")
		Config.params_range[key][ids["topology"]] = (0, ring_params.shape[0]-1, 1)
	else:
		ids["topology_args"] = "[{i}, {i}]"


	start, end, step = Config.params_range[key][ids["topology"]]
	for ralgorithm in Config.params_range["routing_algorithm"][ids["topology"]]:
		temp_ids = dict(ids)
		temp_ids["routing_algorithm"] = ids["routing_algorithm"].format(i=ralgorithm)
		for rtable in Config.params_range["routing_table"][ids["topology"]]:
			temp_ids["routing_table"] = ids["routing_table"].format(i=rtable)
			for i in np.arange(start, end+step, step):
				if (topology == "CIRCULANT"):
					row = ring_params.iloc[i]
					row = f"{[row['Nodes']] + list(map(int, row['Generators'].split()))}"
					temp_ids[key] = ids[key].format(i=row)
				else:
					temp_ids[key] = ids[key].format(i=i)
				sim_unit = Config(temp_ids)
				sim_unit.run()


def main():
	tests("MESH")
	tests("TORUS")
	tests("CIRCULANT")

main()


