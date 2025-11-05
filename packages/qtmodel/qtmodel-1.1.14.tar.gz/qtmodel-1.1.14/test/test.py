import sys
module_path = r'C:\Users\Robert\Desktop\MyWork\Python建模'
sys.path.append(rf"{module_path}")
from qtmodel import *
mdb.do_solve()
reaction_forces= odb.get_reaction(ids=[101,102,103,104,105,106,107,108],stage_id=-1,case_name="CQ:成桥(合计)")
print(reaction_forces)