import io
import os
import re
import csv
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

config = None

class Config:
	arg = "packet_injection_rate"

	template_path = "config_v1.yml"
	
	skip = False
	append = False
	comment = None

	topologies = [
		"MESH",
		"TORUS",
		"CIRCULANT"
	]

	routing_algs = [
		"TABLE_BASED",
		"MESH_XY",
		"RING_SPLIT",
		"VIRTUAL_RING_SPLIT"
	]

	routing_tables = [
		"DIJKSTRA",
		"MESH_XY",
		"GREEDY_PROMOTION",
	]

	arg_params = {
		"topology_args": (2, 35, 1), #(0, 37, 1) for ring circulant
		"routing_algorithm": (0, 3, 1),
		"routing_table": (0, 4, 1),
		"topology": (0, 1, 1),
		"packet_injection_rate": (0.05, 1, 0.05),
	}

	circulant_params = None

	def __init__(self):
		self.set_params()

	def set_params(self):
		self.ids = {
			"topology": None,
			"routing_algorithm": None,
			"routing_table": None,
			"virtual_channels": None
		}

		self.results = pd.DataFrame({
			f"{Config.arg}": [],
			"Total produced flits": [],
			"Total accepted flits": [],
			"Total received flits": [],
			"Network production (flits/cycle)": [],
			"Network acceptance (flits/cycle)": [],
			"Network throughput (flits/cycle)": [],
			"IP throughput (flits/cycle/IP)": [],
			"Last time flit received (cycles)": [],
			"Max buffer stuck delay (cycles)": [],
			"Max time flit in network (cycles)": [],
			"Total received packets": [],
			"Total flits lost": [],
			"Global average delay (cycles)": [],
			"Max delay (cycles)": [],
			"Average buffer utilization": []
		})

		self.get_args()
		if (self.ids["topology"] == "CIRCULANT"):
			Config.arg_params["topology_args"] = (0, 37, 1)
		(self.start, self.end, self.step) = Config.arg_params[Config.arg]

		if (Config.arg == "topology_args"):
			Config.circulant_params = pd.read_csv("circulant_2d/ring_optimal.csv")

		name = f"{self.ids['topology']}-{self.ids['routing_algorithm']}-{self.ids['routing_table']}-{self.ids['virtual_channels']}"
		name = f"{name}-{self.arg}-{self.start}-{self.end}-{self.step}"
		self.result_path = f"results/{name}"
		self.comment = f"#{name}"

	def __format__(self, value):
		if (Config.arg == "topology"):
			return f"{Config.topologies[int(value)]}"
		elif (Config.arg == "routing_algorithm"):
			return f"{Config.routing_algs[int(value)]}"
		elif (Config.arg == "topology_args"):
			if (self.ids["topology"] == "CIRCULANT"):
				row = Config.circulant_params.iloc[int(value)]
				return f"{[row['Nodes']] + list(map(int, row['Generators'].split()))}"
			else:	
				return f"[{value}, {value}]"
		elif (Config.arg == "routing_table"):
			return f"{Config.routing_tables[int(value)]}"
		else:
			return f"{value}"

	def get_args(self):
		with open(Config.template_path, "r") as f:
			lines = f.readlines()
			pattern = r":\s"

			for line in lines:
				if line == "\n": continue
				key, value = re.split(pattern, line, maxsplit=1)
				value = value.strip()
				if key in self.ids:
					self.ids[key] = value 

	def set_result_path(self, path):
		self.result_path = path


def find_arg():
	linenum = 0
	with open(config.template_path, "r") as f:
		lines = f.readlines()
		for linenum in range(0, len(lines)):
			if config.arg in lines[linenum]:
				break
	return linenum

def edit_line(filename, linenum, text):
	lines = open(config.template_path, "r").readlines()
	lines[linenum] = text
	out = open(filename, "w")
	out.writelines(lines)
	out.close()

def subplot_results(ax, *features):
	for i, param in enumerate(features):
		y = subplot_results.df[param].to_list()
		ax.plot(subplot_results.x, y, label = param, linewidth = 2.5)
	
	ax.grid(linestyle = '-', linewidth = 0.5)
	ax.legend()

def plot_all_results(*keys):
	fig, axs = plt.subplots(4, 2, sharex=True, sharey=False, figsize=(20, 15))
	subplot_results(axs[0, 0], *keys[0:3])
	subplot_results(axs[0, 1], keys[3])
	subplot_results(axs[1, 0], keys[4])
	subplot_results(axs[1, 1], keys[5])
	subplot_results(axs[2, 0], *keys[8:10])
	subplot_results(axs[2, 1], keys[11])
	subplot_results(axs[3, 0], *keys[12:14])
	subplot_results(axs[3, 1], keys[14])

	axs[0, 0].set_title("Received flits")
	axs[0, 0].set(ylabel="flits")
	axs[0, 1].set_title("Network production")
	axs[0, 1].set(ylabel="flits/cycle")
	axs[1, 0].set_title("Network acceptance")
	axs[1, 0].set(ylabel="flits/cycle")
	axs[1, 1].set_title("Network throughput")
	axs[1, 1].set(ylabel="flits/cycles")
	axs[2, 0].set_title("Max values")
	axs[2, 0].set(ylabel="cycles")
	axs[2, 1].set_title("Total flits lost")
	axs[2, 1].set(ylabel="flits")
	axs[3, 0].set_title("Delays")
	axs[3, 0].set(ylabel="cycles")
	axs[3, 1].set_title("Average buffer utilization")
	#axs[3, 1].set(ylabel="cycles")
	
	# plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(params[arg]['step']))
	fig.add_subplot(111, frameon=False)
	# hide tick and tick label of the big axis
	plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
	fig.suptitle(f"{config.arg}")
	plt.xlabel(f"{config.arg}, i")
	plt.savefig(f"{config.result_path}.png", bbox_inches='tight', dpi=200)
	plt.show()

def plot_results():
	label = "Network throughput (flits/cycle)" # "IP throughput (flits/cycle/IP)"
	fig, ax = plt.subplots()
	subplot_results.x = subplot_results.df["Network production (flits/cycle)"]
	# subplot_results.x = list(map(lambda x: int(x**0.5), subplot_results.x))
	
	# xmin, xmax = min(subplot_results.x), max(subplot_results.x)
	# step = int((xmax-xmin)*0.1)
	# ticks = list(range(xmin, xmax + int(0.2*step), step))
	
	if (config.arg == "routing_algorithm"):
		for i, key in enumerate(subplot_results.x):
			ax.bar(key, subplot_results.df[label][i], label = key, width = 0.3)
		ax.set_yscale("log")
	else:
		ax.plot(subplot_results.x, subplot_results.df[label], label = label, linewidth = 2.5)
		ax.legend()

	ax.grid(linestyle = '-', linewidth = 0.5)
	ax.set_title(label)
	ax.set(ylabel="flits/cycle", xlabel= "Amount of nodes" if (config.arg == "topology_args") else config.arg)
	plt.savefig(f"{config.result_path}-throughput.png", bbox_inches='tight', dpi=175)
	plt.show()

def run():
	global config
	linenum = find_arg()

	float_values = np.arange(config.start, config.end+config.step, config.step)
	# for i in range(config.start, config.end+config.step, config.step):
	for i in float_values:
		edit_line(f"config_v1-{config.arg}-{i}.yml", linenum, f"{config.arg}: {config:{i}}\n")
		result = os.popen(f"./newxim.exe -config config_v1-{config.arg}-{i}.yml", "r").read()
		result = re.findall(r"^%.*?:\s*(.*)$", result, re.MULTILINE)
		if (config.arg == "topology_args"):
			# result.insert(0, f"{i*i}")
			result.insert(0, f"{Config.circulant_params.iloc[i]['Nodes']}")
		else:
			result.insert(0, f"{config:{i}}")
		config.results.loc[len(config.results)] = result
		os.system(f"rm config_v1-{config.arg}-{i}.yml")

	mode = 'a' if config.append else 'w'
	with open(f"{config.result_path}.csv", mode) as f:
		if not config.append:
			f.write(f"{config.comment}\n")
			config.results.to_csv(f, index=False)
		else:
			config.results.to_csv(f, mode="a", header=False, index=False)

def compare():
	f = "results/TORUS-{i}-MESH_XY-2-packet_injection_rate-0.05-1-0.05.csv"
	config = Config()
	Config.arg = "routing_algorithm"
	args = ["TABLE_BASED", "MESH_XY"]

	fig, ax = plt.subplots()
	for i in range(0, 2):
		df = pd.read_csv(f.format(i = f"{args[i]}"), skiprows=1)
		df = df[["Network production (flits/cycle)", "Network throughput (flits/cycle)"]]
		# df = df.iloc[0:19]

		ax.plot(df["Network production (flits/cycle)"], df["Network throughput (flits/cycle)"], label = f"{args[i]}", linewidth = 2.5)
		ax.legend()

	ax.set(ylabel="flits/cycle", xlabel= "Network production (flits/cycle)")
	ax.grid(linestyle = '-', linewidth = 0.5)
	ax.set_title("Network production (flits/cycle)")
	plt.savefig(f"results/TORUS-MESH_XY-(TABLE_BASED_vs_MESH_XY)-2-topology_args-2-35-1", bbox_inches='tight', dpi=175)
	plt.show()


def main():
	global config
	config = Config()

	if not os.path.exists("./results/"):
		os.system("mkdir results")
	
	if config.skip and os.path.exists(f"{config.result_path}.csv"):
		config.skip = (open(f"{config.result_path}.csv", "r").readline().strip("\n") == config.comment)
	else:
		config.skip = False

	if not config.skip or config.append:
		run()

	# create static variables for the subplot_results() function
	subplot_results.df = pd.read_csv(f"{config.result_path}.csv", skiprows=1)
	subplot_results.x = subplot_results.df[config.arg].to_list()

	#if (config.arg != "routing_algorithm"):
	plot_all_results(*list(config.results.keys()[1:]))
	plot_results()

main()
# compare()