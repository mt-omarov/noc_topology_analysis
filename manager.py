import os

path = "config_v1.yml"
arg = "routing_table"

def find_arg():
	linenum = 0
	with open(path, "r") as f:
		lines = f.readlines()
		for linenum in range(0, len(lines)):
			if arg in lines[linenum]:
				break
	return linenum

def edit_line(pos, text):
	lines = open(path, "r").readlines()
	lines[pos] = text
	out = open(path, "w")
	out.writelines(lines)
	out.close()

def main():
	(start, end, step) = (0, 3, 1)
	# values = ["TABLE_BASED", "MESH_XY", "RING_SPLIT", "VIRTUAL_RING_SPLIT"]
	values = ["DIJKSTRA", "UP_DOWN", "MESH_XY", "GREEDY_PROMOTION", "just table"]
	pos = find_arg()

	for i in range(start, end+step, step):
		edit_line(pos, f"{arg}: {values[i]}\n")
		result = os.system(f"python3 run_configure.py")

main()


	