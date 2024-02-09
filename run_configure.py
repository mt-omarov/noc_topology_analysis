import io
import os
import re
import csv
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

config = None

class Config:
	arg = "topology_args"

	template_path = "config_v1.yml"
	result_path = None
	
	skip = True
	append = False
	comment = None

	ids = {
		"topology": None,
		"routing_algorithm": None,
		"routing_table": None
	}

	routing_algs = [
		"TABLE_BASED",
		"MESH_XY",
		# "SUBNETWORK",
		# "FIT_SUBNETWORK",
		# "FIXED_SUBNETWORK",
		# "VIRTUAL_SUBNETWORK",
		# "FIT_VIRTUAL_SUBNETWORK",
		"RING_SPLIT",
		"VIRTUAL_RING_SPLIT"
	]
	results = pd.DataFrame({
		f"{arg}": [],
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

	def __init__(self):
		self.set_params()

	def set_params(self):
		if (Config.arg == "topology_args"):
			self.start = 2
			self.end = 40
			self.step = 1
		elif (Config.arg == "stats_warm_up_time"):
			self.start = 100
			self.end = 2000
			self.step = 200
		elif (Config.arg == "virtual_channels"):
			self.start = 2
			self.end = 50
			self.step = 5
		elif (Config.arg == "routing_algorithm"):
			self.start = 0
			self.end = 3
			self.step = 1
		else:
			self.start = 0
			self.end = 10
			self.step = 1

	def __format__(self, value):
		if (Config.arg == "routing_algorithm"):
			return f"{Config.routing_algs[int(value)]}"
		elif (Config.arg =="topology_args"):
			return f"[{value}, {value}]"
		else:
			return f"{value}"

def get_args():
	with open(config.template_path, "r") as f:
		lines = f.readlines()
		pattern = r":\s"

		for line in lines:
			if line == "\n": continue
			key, value = re.split(pattern, line, maxsplit=1)
			value = value.strip()
			if key in config.ids:
				config.ids[key] = value 

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
	label = "IP throughput (flits/cycle/IP)"
	fig, ax = plt.subplots()
	
	if (config.arg == "routing_algorithm"):
		for i, key in enumerate(subplot_results.x):
			ax.bar(key, subplot_results.df[label][i], label = key, width = 0.3)
		ax.set_yscale("log")
	else:
		ax.plot(subplot_results.x, subplot_results.df[label], label = label, linewidth = 2.5)
		ax.legend()

	ax.grid(linestyle = '-', linewidth = 0.5)
	ax.set_title(label)
	ax.set(ylabel="flits/cycle", xlabel=config.arg)
	plt.savefig(f"{config.result_path}-throughput.png", bbox_inches='tight', dpi=175)
	plt.show()

def run():
	global config
	linenum = find_arg()
	get_args()

	for i in range(config.start, config.end+config.step, config.step):
		edit_line(f"config_v1-{config.arg}-{i}.yml", linenum, f"{config.arg}: {config:{i}}\n")
		result = os.popen(f"./newxim.exe -config config_v1-{config.arg}-{i}.yml", "r").read()
		result = re.findall(r"^%.*?:\s*(.*)$", result, re.MULTILINE)
		if (config.arg == "topology_args"):
			result.insert(0, f"{i*i}")
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

def main():
	global config
	config = Config()
	get_args()
	config.result_path = f"results/{config.ids['topology']}-{config.arg}-{config.start}-{config.end}-{config.step}"
	config.comment = f"#{config.ids['topology']}-{config.ids['routing_algorithm']}-{config.ids['routing_table']}-{config.arg}-{config.start}-{config.end}-{config.step}"

	if not os.path.exists("./results/"):
		os.system("mkdir results")
	
	if config.skip and os.path.exists(f"{config.result_path}.csv"):
		config.skip = (open(f"{config.result_path}.csv", "r").readline().strip("\n") == config.comment)
	if not config.skip or config.append:
		run()

	# create static variables for the subplot_results() function
	subplot_results.df = pd.read_csv(f"{config.result_path}.csv", skiprows=1)
	subplot_results.x = subplot_results.df[config.arg].to_list()

	if (config.arg != "routing_algorithm"):
		plot_all_results(*list(config.results.keys()[1:]))
	plot_results()

main()