# written by python 3.7.1

import sys



if len(sys.argv) == 6 and sys.argv[5] >=0 and and sys.argv[5] <=1:
	id = str(sys.argv[1])
	first_successive_id = str(sys.argv[2])
	second_successive_id = str(sys.argv[3])
	MSS = str(sys.argv[4])
	drop_probability = str(sys.argv[5])
else:
	print('please input the data of correct form')
	sys.exit()


