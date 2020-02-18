import os
import sys

print("you need to run this from a folder that contains other folders: 'sem_eval_ger', 'sem_eval_swe' etc")
print("add any combination of [ger|swe|lat|eng] in argv\n")

langs = sys.argv[1:]
corpora = ["corpus1","corpus2"]

def check_file(path_in):
	dic_tokens = {}
	print("checking",path_in)
	with open(path_in) as f:
		x = 0
		y = 0
		for line in f.readlines():
			x += 1 
			tokens = line.split()
			if len(tokens) < 10:
				#print("SENTENCE SHORTER THAN TEN", line)
				y +=1
			for token in tokens:
				try:
					dic_tokens[token] += 1
				except KeyError:
					dic_tokens[token] = 1

		total_tokens = 0
		for key in dic_tokens:
			total_tokens += dic_tokens[key]

		print(x,"lines")
		print(len(list(dic_tokens.keys())),"types")
		print(total_tokens,"tokens")
		print(y,"sentences shorter than 10, or",y/x*100,"%")
		print("\n")


for lang in langs:
	for corpus in corpora:
		files = []
		for file in os.listdir(os.path.join("sem_eval_"+lang,corpus,"lemma")):
			if file.endswith(".txt"):
				files.append(os.path.join("sem_eval_"+lang,corpus,"lemma",file))
		print("Dealing with",lang,corpus)
		
		for file in sorted(files):
			check_file(file)